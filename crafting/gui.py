"""PySide6 window for the crafting advisor."""
from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton, QScrollArea, QSpinBox,
    QSplitter, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from crafting.calculator import (
    Opportunity, apply_history, filter_recipes, find_opportunities,
)
from crafting.config import CITIES, CITY_RU, GROUPS, MARKETS, SERVERS, CalcSettings
from crafting.market import MarketClient
from crafting.recipes import Recipe, display_name, load_recipes

HISTORY_TOP_N = 500  # candidates checked against 7-day sales history


def ru(city: str) -> str:
    return CITY_RU.get(city, city)


def fmt_silver(v: float) -> str:
    return f"{v:,.0f}".replace(",", " ")


def fmt_age(h: float) -> str:
    if h < 1:
        return f"{int(h * 60)} мин"
    return f"{h:.0f} ч"


class CalcWorker(QThread):
    status = Signal(str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, settings: CalcSettings, client: MarketClient,
                 cache: dict, refresh_recipes: bool, force_prices: bool):
        super().__init__()
        self.s = settings
        self.client = client
        self.cache = cache
        self.refresh_recipes = refresh_recipes
        self.force_prices = force_prices

    def run(self):
        try:
            if self.refresh_recipes or "recipes" not in self.cache:
                recipes, names = load_recipes(self.status.emit, force=self.refresh_recipes)
                self.cache["recipes"], self.cache["names"] = recipes, names
            recipes: List[Recipe] = self.cache["recipes"]
            selected = filter_recipes(recipes, self.s)
            if not selected:
                self.done.emit([])
                return
            ids = {r.item_id for r in selected} | {
                res.item_id for r in selected for res in r.resources}
            self.status.emit(f"Предметов: {len(selected)}, запрашиваю цены для {len(ids)} id...")
            prices = self.client.get_prices(ids, self.status.emit, force=self.force_prices)
            self.status.emit("Считаю прибыль...")
            opps = find_opportunities(selected, prices, self.s)[:HISTORY_TOP_N]
            if opps:
                history = self.client.get_history(
                    [(o.recipe.item_id, o.sell_market) for o in opps], self.status.emit)
                opps = apply_history(opps, history, self.s)
            self.done.emit(opps)
        except Exception as e:  # surface any network/data error to the UI
            self.failed.emit(str(e))


class NumItem(QTableWidgetItem):
    def __init__(self, text: str, value: float):
        super().__init__(text)
        self.setData(Qt.UserRole, value)
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __lt__(self, other):
        a, b = self.data(Qt.UserRole), other.data(Qt.UserRole)
        if a is None or b is None:
            return super().__lt__(other)
        return a < b


COLUMNS = ["Предмет", "Профит/шт", "ROI %", "Профит/день*", "Продаж/день",
           "Купить материалы", "Крафтить в", "Продать в", "Цена продажи",
           "Себестоимость", "Возраст данных"]


class CraftingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Albion Crafting Advisor — что крафтить")
        self.resize(1400, 820)
        self.cache: dict = {}
        self.clients: Dict[str, MarketClient] = {}
        self.worker: Optional[CalcWorker] = None
        self.opps: List[Opportunity] = []

        root = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._build_settings())
        scroll.setMinimumWidth(400)
        splitter.addWidget(scroll)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        self.status_label = QLabel("Настройте фильтры и нажмите «Рассчитать».")
        rl.addWidget(self.status_label)

        vsplit = QSplitter(Qt.Vertical)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._show_details)
        vsplit.addWidget(self.table)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        vsplit.addWidget(self.details)
        vsplit.setSizes([560, 240])
        rl.addWidget(vsplit)
        rl.addWidget(QLabel(
            "* Профит/день = профит × min(продаж в день, 10% рынка) — грубая оценка ликвидности. "
            "Цены — из Albion Online Data Project (данные игроков), качество «Обычное»."))
        splitter.addWidget(right)
        splitter.setSizes([410, 990])

    # ---------- settings panel ----------
    def _checks(self, title: str, items: Dict[str, str], checked, cols: int = 2):
        box = QGroupBox(title)
        grid = QGridLayout(box)
        boxes = {}
        for n, (key, label) in enumerate(items.items()):
            cb = QCheckBox(label)
            cb.setChecked(key in checked)
            grid.addWidget(cb, n // cols, n % cols)
            boxes[key] = cb
        return box, boxes

    def _build_settings(self) -> QWidget:
        d = CalcSettings()
        w = QWidget()
        lay = QVBoxLayout(w)

        main = QGroupBox("Основное")
        form = QFormLayout(main)
        self.server = QComboBox()
        self.server.addItems(list(SERVERS))
        form.addRow("Сервер", self.server)
        self.premium = QCheckBox("Премиум (налог 4% вместо 8%)")
        self.premium.setChecked(d.premium)
        form.addRow(self.premium)
        self.focus = QCheckBox("Крафт с фокусом")
        self.focus.setChecked(d.use_focus)
        form.addRow(self.focus)
        self.fee = QSpinBox()
        self.fee.setRange(0, 10000)
        self.fee.setValue(int(d.station_fee))
        form.addRow("Налог станка (за 100 еды)", self.fee)
        self.max_age = QSpinBox()
        self.max_age.setRange(1, 168)
        self.max_age.setValue(int(d.max_age_hours))
        self.max_age.setSuffix(" ч")
        form.addRow("Цены не старше", self.max_age)
        self.min_profit = QSpinBox()
        self.min_profit.setRange(-1_000_000, 10_000_000)
        self.min_profit.setSingleStep(500)
        self.min_profit.setValue(int(d.min_profit))
        form.addRow("Мин. профит/шт", self.min_profit)
        self.min_roi = QDoubleSpinBox()
        self.min_roi.setRange(-100, 1000)
        self.min_roi.setValue(d.min_roi)
        self.min_roi.setSuffix(" %")
        form.addRow("Мин. ROI", self.min_roi)
        self.min_vol = QDoubleSpinBox()
        self.min_vol.setRange(0, 10000)
        self.min_vol.setValue(d.min_daily_volume)
        form.addRow("Мин. продаж/день", self.min_vol)
        lay.addWidget(main)

        trade = QGroupBox("Торговля")
        tl = QVBoxLayout(trade)
        self.buy_orders = QCheckBox("Материалы через заказы на покупку (дешевле, дольше)")
        self.buy_orders.setChecked(d.buy_with_orders)
        self.sell_orders = QCheckBox("Продавать через свои ордера (дороже, дольше)")
        self.sell_orders.setChecked(d.sell_with_orders)
        self.buy_in_craft = QCheckBox("Покупать всё в городе крафта (без логистики)")
        self.buy_in_craft.setChecked(d.buy_in_craft_city)
        for cb in (self.buy_orders, self.sell_orders, self.buy_in_craft):
            tl.addWidget(cb)
        lay.addWidget(trade)

        box, self.tier_cb = self._checks("Тиры", {t: f"T{t}" for t in range(2, 9)}, d.tiers, 4)
        lay.addWidget(box)
        box, self.ench_cb = self._checks("Зачарование", {e: f".{e}" for e in range(5)}, d.enchants, 5)
        lay.addWidget(box)
        box, self.group_cb = self._checks("Что крафтим", GROUPS, d.groups)
        lay.addWidget(box)
        box, self.buy_cb = self._checks("Где покупать", {c: ru(c) for c in CITIES}, d.buy_cities)
        lay.addWidget(box)
        box, self.craft_cb = self._checks("Где можно крафтить", {c: ru(c) for c in CITIES}, d.craft_cities)
        lay.addWidget(box)
        box, self.sell_cb = self._checks("Где продавать", {c: ru(c) for c in MARKETS}, d.sell_markets)
        lay.addWidget(box)

        self.calc_btn = QPushButton("Рассчитать")
        self.calc_btn.clicked.connect(lambda: self._run(False, False))
        lay.addWidget(self.calc_btn)
        self.refresh_btn = QPushButton("Обновить цены (сбросить кэш)")
        self.refresh_btn.clicked.connect(lambda: self._run(False, True))
        lay.addWidget(self.refresh_btn)
        self.recipes_btn = QPushButton("Обновить рецепты из игры")
        self.recipes_btn.clicked.connect(lambda: self._run(True, False))
        lay.addWidget(self.recipes_btn)
        lay.addStretch()
        return w

    def _settings(self) -> CalcSettings:
        pick = lambda d: {k for k, cb in d.items() if cb.isChecked()}  # noqa: E731
        return CalcSettings(
            server=self.server.currentText(), premium=self.premium.isChecked(),
            use_focus=self.focus.isChecked(), station_fee=self.fee.value(),
            max_age_hours=self.max_age.value(), tiers=pick(self.tier_cb),
            enchants=pick(self.ench_cb), groups=pick(self.group_cb),
            buy_cities=pick(self.buy_cb), craft_cities=pick(self.craft_cb),
            sell_markets=pick(self.sell_cb), buy_with_orders=self.buy_orders.isChecked(),
            sell_with_orders=self.sell_orders.isChecked(),
            buy_in_craft_city=self.buy_in_craft.isChecked(),
            min_profit=self.min_profit.value(), min_roi=self.min_roi.value(),
            min_daily_volume=self.min_vol.value(),
        )

    # ---------- run ----------
    def _run(self, refresh_recipes: bool, force_prices: bool):
        if self.worker and self.worker.isRunning():
            return
        s = self._settings()
        if s.server not in self.clients:
            self.clients[s.server] = MarketClient(s.server)
        self.worker = CalcWorker(s, self.clients[s.server], self.cache,
                                 refresh_recipes, force_prices)
        self.worker.status.connect(self.status_label.setText)
        self.worker.done.connect(self._on_done)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(lambda: self._set_busy(False))
        self._set_busy(True)
        self.worker.start()

    def _set_busy(self, busy: bool):
        for b in (self.calc_btn, self.refresh_btn, self.recipes_btn):
            b.setEnabled(not busy)

    def _on_failed(self, msg: str):
        self.status_label.setText(f"Ошибка: {msg}")

    def _on_done(self, opps: List[Opportunity]):
        self.opps = opps
        names = self.cache.get("names", {})
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(opps))
        for row, o in enumerate(opps):
            vol, daily = o.daily_volume, o.daily_profit
            cells = [
                QTableWidgetItem(display_name(o.recipe.item_id, names)),
                NumItem(fmt_silver(o.profit), o.profit),
                NumItem(f"{o.roi:.1f}", o.roi),
                NumItem(fmt_silver(daily) if daily is not None else "—",
                        daily if daily is not None else -1e18),
                NumItem(f"{vol:.1f}" if vol is not None else "—",
                        vol if vol is not None else -1.0),
                QTableWidgetItem(", ".join(ru(c) for c in o.buy_cities)),
                QTableWidgetItem(f"{ru(o.craft_city)} ({o.return_rate * 100:.1f}% возврата)"),
                QTableWidgetItem(ru(o.sell_market)),
                NumItem(fmt_silver(o.sell_price), o.sell_price),
                NumItem(fmt_silver(o.cost), o.cost),
                NumItem(fmt_age(o.oldest_data_hours), o.oldest_data_hours),
            ]
            cells[0].setData(Qt.UserRole + 1, row)
            for col, item in enumerate(cells):
                self.table.setItem(row, col, item)
        self.table.setSortingEnabled(True)
        self.table.sortItems(3, Qt.DescendingOrder)
        self.table.resizeColumnsToContents()
        self.status_label.setText(
            f"Найдено выгодных вариантов: {len(opps)}. Кликните строку — покажу план.")
        if opps:
            self.table.selectRow(0)

    def _show_details(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        idx = self.table.item(rows[0].row(), 0).data(Qt.UserRole + 1)
        o = self.opps[idx]
        names = self.cache.get("names", {})
        r = o.recipe
        lines = [f"<h3>{display_name(r.item_id, names)}</h3>"]
        lines.append("<b>1. Купить</b> (на один крафт"
                     + (f", выходит {r.amount} шт." if r.amount > 1 else "") + "):<ul>")
        for m in o.materials:
            note = "" if m.returnable else " <i>(не возвращается)</i>"
            lines.append(
                f"<li>{display_name(m.item_id, names)} × {m.count:g} — "
                f"<b>{ru(m.city)}</b> по {fmt_silver(m.unit_price)} "
                f"= {fmt_silver(m.unit_price * m.count)}{note} "
                f"<span style='color:gray'>(цена {fmt_age(m.age_hours)} назад)</span></li>")
        lines.append("</ul>")
        lines.append(
            f"<b>2. Крафтить</b> в <b>{ru(o.craft_city)}</b> — возврат ресурсов "
            f"{o.return_rate * 100:.1f}%. Материалы с учётом возврата: "
            f"{fmt_silver(o.material_cost)}/шт, налог станка: {fmt_silver(o.fee_cost)}/шт.<br>")
        lines.append(
            f"<b>3. Везти и продать</b> в <b>{ru(o.sell_market)}</b> по "
            f"{fmt_silver(o.sell_price)} → на руки {fmt_silver(o.revenue)} после налогов.<br>")
        if o.listed_price:
            lines.append(
                f"<span style='color:#e0a040'>Сейчас выставлено по {fmt_silver(o.listed_price)}, "
                f"но средняя цена сделок за 7 дней ниже — считаю по ней.</span><br>")
        if o.alternatives:
            alt = ", ".join(f"{ru(m)}: {fmt_silver(n)}" for m, n in o.alternatives)
            lines.append(f"<span style='color:gray'>Другие рынки (на руки): {alt}</span><br>")
        lines.append(
            f"<br><b>Себестоимость:</b> {fmt_silver(o.cost)} · <b>Профит:</b> "
            f"{fmt_silver(o.profit)}/шт · <b>ROI:</b> {o.roi:.1f}%")
        if o.profit_per_focus is not None:
            lines.append(f" · <b>Серебро за 1 фокус:</b> {o.profit_per_focus:.1f}")
        if o.daily_volume is not None:
            lines.append(f"<br>Продаётся в среднем {o.daily_volume:.1f} шт/день "
                         f"в {ru(o.sell_market)} (за 7 дней).")
        self.details.setHtml("".join(lines))
