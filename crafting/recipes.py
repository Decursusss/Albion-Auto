"""Builds a compact recipe database from the ao-bin-dumps game data."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import requests

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
RECIPES_PATH = os.path.join(DATA_DIR, "recipes.json")

ITEMS_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/items.json"
NAMES_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"

SECTIONS = ("weapon", "equipmentitem", "consumableitem", "simpleitem")

SHOP_TO_GROUP = {
    "weapons": "weapon",
    "armors": "armor",
    "head": "head",
    "shoes": "shoes",
    "offhands": "offhand",
    "capes": "cape",
    "bags": "bag",
    "gathering": "gathering",
    "other": "gathering",  # some tools live in 'other'
}


@dataclass
class Resource:
    item_id: str
    count: float
    returnable: bool


@dataclass
class Recipe:
    item_id: str
    tier: int
    enchant: int
    category: str       # craftingcategory, used for city bonus
    group: str          # filter group key
    focus: float
    amount: int         # items produced per craft
    silver: float
    value: float        # item value, used for station fee
    resources: List[Resource]
    is_refining: bool


def _as_list(x) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _api_id(name: str, ench: int) -> str:
    return f"{name}@{ench}" if ench > 0 else name


def _pick_requirement(reqs: list) -> Optional[dict]:
    """Prefer a recipe without faction/avalon tokens (those aren't on the market)."""
    reqs = [r for r in reqs if r.get("craftresource")]
    if not reqs:
        return None
    for r in reqs:
        names = [c["@uniquename"] for c in _as_list(r["craftresource"])]
        if not any("TOKEN" in n for n in names):
            return r
    return reqs[0]


def _group_for(section: str, item: dict) -> Optional[str]:
    if section == "simpleitem":
        return "refined" if item.get("@shopsubcategory1") == "refinedresources" else None
    cat = item.get("@craftingcategory")
    if not cat:
        return None
    if section == "consumableitem":
        return cat if cat in ("food", "potion") else None
    return SHOP_TO_GROUP.get(item.get("@shopcategory", ""))


def build_recipes(items_dump: dict, names_dump: list) -> dict:
    items = items_dump["items"]

    # Item values of everything (needed for station fees).
    values: Dict[str, float] = {}
    for section in SECTIONS:
        for it in _as_list(items.get(section)):
            if "@itemvalue" in it:
                ench = int(it.get("@enchantmentlevel", 0) or 0)
                values[_api_id(it["@uniquename"], ench)] = float(it["@itemvalue"])

    def make(item_id, tier, ench, cat, group, req, refining) -> Optional[dict]:
        if req is None:
            return None
        res = []
        value = 0.0
        for c in _as_list(req.get("craftresource")):
            rid = _api_id(c["@uniquename"], int(c.get("@enchantmentlevel", 0) or 0))
            cnt = float(c["@count"])
            res.append([rid, cnt, c.get("@maxreturnamount") != "0"])
            value += values.get(rid, 0.0) * cnt
        if not res:
            return None
        return {
            "id": item_id, "tier": tier, "ench": ench, "cat": cat, "group": group,
            "focus": float(req.get("@craftingfocus", 0) or 0),
            "amount": int(req.get("@amountcrafted", 1) or 1),
            "silver": float(req.get("@silver", 0) or 0),
            "value": value, "res": res, "refining": refining,
        }

    products = []
    for section in SECTIONS:
        for it in _as_list(items.get(section)):
            group = _group_for(section, it)
            if not group:
                continue
            base = it["@uniquename"]
            tier = int(it.get("@tier", 0) or 0)
            cat = it.get("@craftingcategory", "")
            refining = group == "refined"
            if refining:
                # Enchanted refined resources are separate entries (T5_LEATHER_LEVEL1).
                ench = int(it.get("@enchantmentlevel", 0) or 0)
                p = make(_api_id(base, ench), tier, ench, cat, group,
                         _pick_requirement(_as_list(it.get("craftingrequirements"))), True)
                if p:
                    products.append(p)
                continue
            p = make(base, tier, 0, cat, group,
                     _pick_requirement(_as_list(it.get("craftingrequirements"))), False)
            if p:
                products.append(p)
            for en in _as_list((it.get("enchantments") or {}).get("enchantment")):
                lvl = int(en["@enchantmentlevel"])
                p = make(_api_id(base, lvl), tier, lvl, cat, group,
                         _pick_requirement(_as_list(en.get("craftingrequirements"))), False)
                if p:
                    products.append(p)

    needed = {p["id"] for p in products} | {r[0] for p in products for r in p["res"]}
    names: Dict[str, str] = {}
    for n in names_dump:
        uid = n.get("UniqueName")
        if uid in needed and n.get("LocalizedNames"):
            ln = n["LocalizedNames"]
            names[uid] = ln.get("RU-RU") or ln.get("EN-US") or uid
    return {"products": products, "names": names}


def download_and_build(progress: Callable[[str], None] = print) -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    progress("Скачиваю рецепты из дампа игры (~17 МБ)...")
    items_dump = requests.get(ITEMS_URL, timeout=120).json()
    progress("Скачиваю названия предметов (~24 МБ)...")
    names_dump = requests.get(NAMES_URL, timeout=120).json()
    progress("Собираю базу рецептов...")
    db = build_recipes(items_dump, names_dump)
    with open(RECIPES_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
    progress(f"Рецептов: {len(db['products'])}")
    return db


def load_recipes(progress: Callable[[str], None] = print,
                 force: bool = False) -> Tuple[List[Recipe], Dict[str, str]]:
    if force or not os.path.exists(RECIPES_PATH):
        db = download_and_build(progress)
    else:
        with open(RECIPES_PATH, encoding="utf-8") as f:
            db = json.load(f)
    recipes = [
        Recipe(
            item_id=p["id"], tier=p["tier"], enchant=p["ench"], category=p["cat"],
            group=p["group"], focus=p["focus"], amount=p["amount"], silver=p["silver"],
            value=p["value"], resources=[Resource(r[0], r[1], r[2]) for r in p["res"]],
            is_refining=p["refining"],
        )
        for p in db["products"]
    ]
    return recipes, db["names"]


def display_name(item_id: str, names: Dict[str, str]) -> str:
    if item_id in names:
        name = names[item_id]
    else:
        name = names.get(item_id.split("@")[0], item_id)
    name = re.sub(r"\s*\([^)]*\)$", "", name)  # drop "(мастер)" — tier is shown below
    tier = item_id.split("_")[0]
    ench = item_id.split("@")[1] if "@" in item_id else "0"
    return f"{name} {tier[1:]}.{ench}" if tier[:1] == "T" and tier[1:].isdigit() else name
