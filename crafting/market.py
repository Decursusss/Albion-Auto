"""Client for the Albion Online Data Project market API (crowd-sourced prices)."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote

import requests

from crafting.config import MARKETS, SERVERS

MAX_URL_LEN = 3800
PRICE_CACHE_TTL = 600  # seconds


@dataclass
class Price:
    sell_min: int        # cheapest sell order (what you pay for instant buy)
    sell_min_age: float  # hours
    buy_max: int         # highest buy order (what you get for instant sell)
    buy_max_age: float


def _age_hours(date_str: str, now: datetime) -> float:
    if not date_str or date_str.startswith("0001"):
        return float("inf")
    try:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return float("inf")
    return max(0.0, (now - dt).total_seconds() / 3600)


class RateLimiter:
    """API limits: 180 req/min and 300 req/5 min."""

    def __init__(self, per_minute: int = 170, per_5min: int = 290):
        self.limits = [(60.0, per_minute), (300.0, per_5min)]
        self.calls: deque = deque()

    def wait(self) -> None:
        while True:
            now = time.monotonic()
            while self.calls and now - self.calls[0] > 300:
                self.calls.popleft()
            delay = 0.0
            for window, limit in self.limits:
                recent = [t for t in self.calls if now - t <= window]
                if len(recent) >= limit:
                    delay = max(delay, window - (now - recent[0]) + 0.1)
            if delay <= 0:
                self.calls.append(now)
                return
            time.sleep(delay)


class MarketClient:
    def __init__(self, server: str = "Europe"):
        self.base = SERVERS[server]
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "AlbionCraftingAdvisor/1.0",
        })
        self.limiter = RateLimiter()
        self._cache: Dict[str, Tuple[float, Dict[str, Price]]] = {}

    def _get(self, url: str) -> list:
        for attempt in range(5):
            self.limiter.wait()
            r = self.session.get(url, timeout=60)
            if r.status_code == 429 or "Throttled" in r.text[:40]:
                time.sleep(15 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("API рынка ограничивает запросы, попробуйте через пару минут")

    @staticmethod
    def _batches(ids: List[str], prefix_len: int) -> Iterable[List[str]]:
        batch: List[str] = []
        length = prefix_len
        for i in ids:
            add = len(quote(i, safe="@_")) + 1
            if batch and length + add > MAX_URL_LEN:
                yield batch
                batch, length = [], prefix_len
            batch.append(i)
            length += add
        if batch:
            yield batch

    def get_prices(self, item_ids: Iterable[str],
                   progress: Optional[Callable[[str], None]] = None,
                   force: bool = False) -> Dict[str, Dict[str, Price]]:
        """Returns {item_id: {location: Price}} for quality 1."""
        ids = sorted(set(item_ids))
        now_mono = time.monotonic()
        todo = [i for i in ids if force or i not in self._cache
                or now_mono - self._cache[i][0] > PRICE_CACHE_TTL]

        locations = ",".join(quote(m) for m in MARKETS)
        suffix = f".json?locations={locations}&qualities=1"
        prefix = f"{self.base}/api/v2/stats/prices/"
        batches = list(self._batches(todo, len(prefix) + len(suffix)))
        now = datetime.utcnow()
        for n, batch in enumerate(batches, 1):
            if progress:
                progress(f"Загружаю цены: {n}/{len(batches)}")
            url = prefix + ",".join(quote(i, safe="@_") for i in batch) + suffix
            fetched: Dict[str, Dict[str, Price]] = {i: {} for i in batch}
            for row in self._get(url):
                if row.get("quality", 1) != 1:
                    continue
                fetched.setdefault(row["item_id"], {})[row["city"]] = Price(
                    sell_min=row.get("sell_price_min") or 0,
                    sell_min_age=_age_hours(row.get("sell_price_min_date", ""), now),
                    buy_max=row.get("buy_price_max") or 0,
                    buy_max_age=_age_hours(row.get("buy_price_max_date", ""), now),
                )
            stamp = time.monotonic()
            for i, p in fetched.items():
                self._cache[i] = (stamp, p)
        return {i: self._cache[i][1] for i in ids if i in self._cache}

    def get_history(self, pairs: Iterable[Tuple[str, str]],
                    progress: Optional[Callable[[str], None]] = None,
                    days: int = 7) -> Dict[Tuple[str, str], Tuple[float, Optional[float]]]:
        """(avg sold per day, avg sale price) over the last `days` days."""
        by_loc: Dict[str, List[str]] = {}
        for item_id, loc in pairs:
            by_loc.setdefault(loc, []).append(item_id)
        result: Dict[Tuple[str, str], Tuple[float, Optional[float]]] = {}
        prefix = f"{self.base}/api/v2/stats/history/"
        for loc, ids in by_loc.items():
            suffix = f".json?locations={quote(loc)}&qualities=1&time-scale=24"
            for batch in self._batches(sorted(set(ids)), len(prefix) + len(suffix)):
                if progress:
                    progress(f"Загружаю объёмы продаж: {loc}")
                url = prefix + ",".join(quote(i, safe="@_") for i in batch) + suffix
                now = datetime.utcnow()
                for row in self._get(url):
                    recent = [d for d in row.get("data") or []
                              if _age_hours(d.get("timestamp", ""), now) <= days * 24]
                    count = sum(d.get("item_count", 0) for d in recent)
                    if count:
                        avg = sum(d.get("avg_price", 0) * d.get("item_count", 0)
                                  for d in recent) / count
                        result[(row["item_id"], loc)] = (count / days, avg)
                for i in batch:
                    result.setdefault((i, loc), (0.0, None))
        return result
