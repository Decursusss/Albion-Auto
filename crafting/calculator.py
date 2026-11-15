"""Profit calculation: what to buy, where to craft, where to sell."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from crafting.config import (
    BASE_PRODUCTION_BONUS, BLACK_MARKET, BLACK_MARKET_GROUPS, CITY_CRAFT_BONUS,
    CITY_REFINE_BONUS, CRAFT_BONUS, FOCUS_BONUS, ORDER_SETUP_FEE, REFINE_BONUS,
    CalcSettings,
)
from crafting.market import Price
from crafting.recipes import Recipe

Prices = Dict[str, Dict[str, Price]]


@dataclass
class MaterialLine:
    item_id: str
    count: float          # per craft action
    city: str
    unit_price: float
    returnable: bool
    age_hours: float


@dataclass
class Opportunity:
    recipe: Recipe
    craft_city: str
    return_rate: float
    materials: List[MaterialLine]
    material_cost: float      # per item, after resource return
    fee_cost: float           # station fee + recipe silver, per item
    cost: float               # total per item
    sell_market: str
    sell_price: float         # gross price per item
    revenue: float            # after tax / setup fee
    profit: float
    roi: float                # percent
    sell_age_hours: float
    profit_per_focus: Optional[float] = None
    daily_volume: Optional[float] = None
    avg_price: Optional[float] = None         # 7-day average sale price
    listed_price: Optional[float] = None      # current order price before capping

    @property
    def daily_profit(self) -> Optional[float]:
        """Rough profit/day if you take ~10% of the market (at least 1 item)."""
        if self.daily_volume is None:
            return None
        return self.profit * min(self.daily_volume, max(1.0, self.daily_volume * 0.1))
    alternatives: List[Tuple[str, float]] = field(default_factory=list)  # (market, net revenue)

    @property
    def buy_cities(self) -> List[str]:
        seen: List[str] = []
        for m in self.materials:
            if m.city not in seen:
                seen.append(m.city)
        return seen

    @property
    def oldest_data_hours(self) -> float:
        return max([self.sell_age_hours] + [m.age_hours for m in self.materials])


def return_rate(bonus_percent: float) -> float:
    return 1.0 - 1.0 / (1.0 + bonus_percent / 100.0)


def production_bonus(recipe: Recipe, city: str, use_focus: bool) -> float:
    bonus = BASE_PRODUCTION_BONUS
    if recipe.is_refining:
        if REFINE_BONUS.get(recipe.category) == city:
            bonus += CITY_REFINE_BONUS
    elif recipe.category in CRAFT_BONUS.get(city, set()):
        bonus += CITY_CRAFT_BONUS
    if use_focus:
        bonus += FOCUS_BONUS
    return bonus


def _buy_price(p: Price, s: CalcSettings) -> Optional[Tuple[float, float]]:
    """Unit cost to acquire a material at a location, and data age."""
    if s.buy_with_orders:
        if p.buy_max > 0 and p.buy_max_age <= s.max_age_hours:
            return p.buy_max * (1 + ORDER_SETUP_FEE), p.buy_max_age
    elif p.sell_min > 0 and p.sell_min_age <= s.max_age_hours:
        return float(p.sell_min), p.sell_min_age
    return None


def _sell_options(recipe: Recipe, prices: Prices,
                  s: CalcSettings) -> List[Tuple[str, float, float, float]]:
    """[(market, gross price, net revenue, age)] sorted best first."""
    out = []
    for market, p in prices.get(recipe.item_id, {}).items():
        if market not in s.sell_markets:
            continue
        if market == BLACK_MARKET:
            if recipe.group not in BLACK_MARKET_GROUPS:
                continue
            # The Black Market only has buy orders: you sell instantly.
            if p.buy_max > 0 and p.buy_max_age <= s.max_age_hours:
                out.append((market, float(p.buy_max), p.buy_max * (1 - s.tax), p.buy_max_age))
            continue
        if s.sell_with_orders:
            if p.sell_min > 0 and p.sell_min_age <= s.max_age_hours:
                gross = float(p.sell_min)
                out.append((market, gross, gross * (1 - s.tax - ORDER_SETUP_FEE), p.sell_min_age))
        elif p.buy_max > 0 and p.buy_max_age <= s.max_age_hours:
            gross = float(p.buy_max)
            out.append((market, gross, gross * (1 - s.tax), p.buy_max_age))
    out.sort(key=lambda x: -x[2])
    return out


def _materials(recipe: Recipe, prices: Prices, s: CalcSettings,
               only_city: Optional[str]) -> Optional[List[MaterialLine]]:
    lines = []
    for r in recipe.resources:
        best = None
        for city, p in prices.get(r.item_id, {}).items():
            if city not in s.buy_cities or (only_city and city != only_city):
                continue
            bp = _buy_price(p, s)
            if bp and (best is None or bp[0] < best[1]):
                best = (city, bp[0], bp[1])
        if best is None:
            return None
        lines.append(MaterialLine(r.item_id, r.count, best[0], best[1], r.returnable, best[2]))
    return lines


def evaluate(recipe: Recipe, prices: Prices, s: CalcSettings) -> Optional[Opportunity]:
    sells = _sell_options(recipe, prices, s)
    if not sells:
        return None
    best: Optional[Opportunity] = None
    for city in s.craft_cities:
        mats = _materials(recipe, prices, s, city if s.buy_in_craft_city else None)
        if mats is None:
            continue
        rrr = return_rate(production_bonus(recipe, city, s.use_focus))
        mat_cost = sum(m.count * m.unit_price * ((1 - rrr) if m.returnable else 1.0)
                       for m in mats)
        station = recipe.value * 0.1125 * s.station_fee / 100.0
        fees = station + recipe.silver
        cost = (mat_cost + fees) / recipe.amount
        market, gross, net, age = sells[0]
        profit = net - cost
        opp = Opportunity(
            recipe=recipe, craft_city=city, return_rate=rrr, materials=mats,
            material_cost=mat_cost / recipe.amount, fee_cost=fees / recipe.amount,
            cost=cost, sell_market=market, sell_price=gross, revenue=net,
            profit=profit, roi=(profit / cost * 100) if cost > 0 else 0.0,
            sell_age_hours=age,
            alternatives=[(m, n) for m, _, n, _ in sells[1:4]],
        )
        if s.use_focus and recipe.focus > 0:
            opp.profit_per_focus = profit * recipe.amount / recipe.focus
        if best is None or opp.profit > best.profit:
            best = opp
    return best


def find_opportunities(recipes: List[Recipe], prices: Prices,
                       s: CalcSettings) -> List[Opportunity]:
    out = []
    for r in recipes:
        opp = evaluate(r, prices, s)
        if opp and opp.profit >= s.min_profit and opp.roi >= s.min_roi:
            out.append(opp)
    out.sort(key=lambda o: -o.profit)
    return out


def apply_history(opps: List[Opportunity],
                  history: Dict[Tuple[str, str], Tuple[float, Optional[float]]],
                  s: CalcSettings) -> List[Opportunity]:
    """Cap sale price at the 7-day average, attach volume, drop illiquid items."""
    out = []
    for o in opps:
        vol, avg = history.get((o.recipe.item_id, o.sell_market), (None, None))
        o.daily_volume, o.avg_price = vol, avg
        if avg is not None and avg < o.sell_price:
            factor = o.revenue / o.sell_price
            o.listed_price = o.sell_price
            o.sell_price = avg
            o.revenue = avg * factor
            o.profit = o.revenue - o.cost
            o.roi = (o.profit / o.cost * 100) if o.cost > 0 else 0.0
            if o.profit_per_focus is not None:
                o.profit_per_focus = o.profit * o.recipe.amount / o.recipe.focus
        if (vol or 0) < s.min_daily_volume:
            continue
        if o.profit >= s.min_profit and o.roi >= s.min_roi:
            out.append(o)
    out.sort(key=lambda o: -(o.daily_profit or 0))
    return out


def filter_recipes(recipes: List[Recipe], s: CalcSettings) -> List[Recipe]:
    return [r for r in recipes
            if r.tier in s.tiers and r.enchant in s.enchants and r.group in s.groups]
