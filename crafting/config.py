"""Static game data and default settings for the crafting advisor.

City bonuses and taxes change with game patches — if the numbers drift,
edit them here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

SERVERS: Dict[str, str] = {
    "Europe": "https://europe.albion-online-data.com",
    "Americas (West)": "https://west.albion-online-data.com",
    "Asia (East)": "https://east.albion-online-data.com",
}

BLACK_MARKET = "Black Market"

# Cities where you can buy / craft / sell (API location names).
CITIES: List[str] = [
    "Martlock",
    "Bridgewatch",
    "Lymhurst",
    "Fort Sterling",
    "Thetford",
    "Caerleon",
    "Brecilien",
]
MARKETS: List[str] = CITIES + [BLACK_MARKET]

CITY_RU: Dict[str, str] = {
    "Martlock": "Мартлок",
    "Bridgewatch": "Бриджвотч",
    "Lymhurst": "Лимхерст",
    "Fort Sterling": "Форт Стерлинг",
    "Thetford": "Тетфорд",
    "Caerleon": "Карлеон",
    "Brecilien": "Брецилиэн",
    BLACK_MARKET: "Чёрный рынок",
}

# craftingcategory (from the game dump) -> city with +15% crafting bonus.
CRAFT_BONUS: Dict[str, Set[str]] = {
    "Martlock": {"axe", "quarterstaff", "froststaff", "plate_shoes", "offhand"},
    "Bridgewatch": {"crossbow", "dagger", "cursestaff", "plate_armor", "cloth_shoes"},
    "Lymhurst": {"sword", "bow", "arcanestaff", "leather_helmet", "leather_shoes"},
    "Fort Sterling": {"hammer", "spear", "holystaff", "plate_helmet", "cloth_armor"},
    "Thetford": {"mace", "naturestaff", "firestaff", "leather_armor", "cloth_helmet"},
    "Caerleon": {"knuckles", "shapeshifterstaff", "tools", "gatherergear", "food"},
    "Brecilien": {"cape", "bag", "potion"},
}

# Refining category -> city with +40% refining bonus.
REFINE_BONUS: Dict[str, str] = {
    "hide": "Martlock",
    "rock": "Bridgewatch",
    "fiber": "Lymhurst",
    "wood": "Fort Sterling",
    "ore": "Thetford",
}

# Production bonus percentages; resource return rate = 1 - 1 / (1 + bonus/100).
BASE_PRODUCTION_BONUS = 18.0
CITY_CRAFT_BONUS = 15.0
CITY_REFINE_BONUS = 40.0
FOCUS_BONUS = 59.0

# Market fees (fractions).
TAX_PREMIUM = 0.04
TAX_NO_PREMIUM = 0.08
ORDER_SETUP_FEE = 0.025

# Product groups shown in the filter (label -> internal key).
GROUPS: Dict[str, str] = {
    "weapon": "Оружие",
    "armor": "Броня",
    "head": "Шлемы",
    "shoes": "Обувь",
    "offhand": "Оффхенды",
    "cape": "Плащи",
    "bag": "Сумки",
    "gathering": "Сбор / инструменты",
    "food": "Еда",
    "potion": "Зелья",
    "refined": "Переработка",
}

# Groups the Black Market buys.
BLACK_MARKET_GROUPS = {"weapon", "armor", "head", "shoes", "offhand", "cape", "bag"}


@dataclass
class CalcSettings:
    server: str = "Europe"
    premium: bool = True
    use_focus: bool = False
    station_fee: float = 400.0          # silver per 100 nutrition
    max_age_hours: float = 24.0         # ignore prices older than this
    tiers: Set[int] = field(default_factory=lambda: {4, 5, 6, 7, 8})
    enchants: Set[int] = field(default_factory=lambda: {0, 1, 2})
    groups: Set[str] = field(default_factory=lambda: set(GROUPS) - {"refined"})
    buy_cities: Set[str] = field(default_factory=lambda: set(CITIES))
    craft_cities: Set[str] = field(default_factory=lambda: set(CITIES))
    sell_markets: Set[str] = field(default_factory=lambda: set(MARKETS))
    buy_with_orders: bool = False       # materials via buy orders instead of instant buy
    sell_with_orders: bool = True       # list sell orders instead of instant sell
    buy_in_craft_city: bool = False     # buy all materials in the crafting city
    min_profit: float = 1000.0
    min_roi: float = 5.0                # percent
    min_daily_volume: float = 1.0       # items sold per day in the sell market

    @property
    def tax(self) -> float:
        return TAX_PREMIUM if self.premium else TAX_NO_PREMIUM
