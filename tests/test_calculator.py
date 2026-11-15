import unittest

from crafting.calculator import evaluate, return_rate
from crafting.config import CalcSettings
from crafting.market import Price
from crafting.recipes import Recipe, Resource


def price(sell=0, buy=0, age=1.0):
    return Price(sell_min=sell, sell_min_age=age, buy_max=buy, buy_max_age=age)


SWORD = Recipe(
    item_id="T4_MAIN_SWORD", tier=4, enchant=0, category="sword", group="weapon",
    focus=1286, amount=1, silver=0, value=0,
    resources=[Resource("T4_METALBAR", 16, True), Resource("T4_LEATHER", 8, True)],
    is_refining=False,
)


class CalculatorTest(unittest.TestCase):
    def test_return_rates(self):
        self.assertAlmostEqual(return_rate(18), 0.1525, places=3)
        self.assertAlmostEqual(return_rate(33), 0.2481, places=3)
        self.assertAlmostEqual(return_rate(18 + 15 + 59), 0.4792, places=3)

    def test_picks_cheapest_materials_bonus_city_and_best_market(self):
        prices = {
            "T4_METALBAR": {"Thetford": price(sell=100), "Lymhurst": price(sell=150)},
            "T4_LEATHER": {"Martlock": price(sell=80), "Lymhurst": price(sell=90)},
            "T4_MAIN_SWORD": {"Caerleon": price(sell=5000), "Black Market": price(buy=4500)},
        }
        s = CalcSettings(premium=True, station_fee=0)
        o = evaluate(SWORD, prices, s)
        self.assertEqual(o.craft_city, "Lymhurst")  # sword bonus city
        self.assertEqual(o.buy_cities, ["Thetford", "Martlock"])
        self.assertEqual(o.sell_market, "Caerleon")
        raw = 16 * 100 + 8 * 80
        self.assertAlmostEqual(o.cost, raw * (1 - return_rate(33)), places=4)
        self.assertAlmostEqual(o.revenue, 5000 * (1 - 0.04 - 0.025))

    def test_stale_prices_ignored_and_non_returnable(self):
        r = Recipe("X", 4, 0, "sword", "weapon", 0, 1, 0, 0,
                   [Resource("A", 1, False)], False)
        prices = {"A": {"Martlock": price(sell=10, age=100), "Thetford": price(sell=50)},
                  "X": {"Martlock": price(sell=200)}}
        o = evaluate(r, prices, CalcSettings(station_fee=0, max_age_hours=24))
        self.assertEqual(o.materials[0].city, "Thetford")
        self.assertAlmostEqual(o.cost, 50)  # artifact-like: no return

    def test_buy_in_craft_city(self):
        prices = {
            "T4_METALBAR": {"Thetford": price(sell=100), "Lymhurst": price(sell=150)},
            "T4_LEATHER": {"Thetford": price(sell=90), "Lymhurst": price(sell=90)},
            "T4_MAIN_SWORD": {"Lymhurst": price(sell=9000)},
        }
        o = evaluate(SWORD, prices, CalcSettings(station_fee=0, buy_in_craft_city=True))
        self.assertEqual(len(o.buy_cities), 1)
        self.assertEqual(o.buy_cities[0], o.craft_city)


if __name__ == "__main__":
    unittest.main()
