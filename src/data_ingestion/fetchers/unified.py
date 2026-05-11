"""
Unified data fetcher for WCVS market data.
Uses Yahoo Finance API (free, unofficial) as primary where possible,
with cache fallback and stale data tolerance.
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from ..cache import DataCache


class UnifiedFetcher:
    """Coordinates fetching of all WCVS metrics."""

    def __init__(self, cache: DataCache):
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WCVS-DataBot/1.0 (Research Project)"
        })

    def fetch_all(self) -> Dict[str, Any]:
        """Fetch all metrics. Returns dict of {metric: {value, stale, cached}}."""
        results = {}
        results["sp500_price"] = self._fetch("sp500_price", self._live_sp500)
        results["shiller_cape"] = self._fetch("shiller_cape", self._live_cape)
        results["forward_pe"] = self._fetch("forward_pe", self._live_forward_pe)
        results["fear_greed"] = self._fetch("fear_greed", self._live_fear_greed)
        results["naaim"] = self._fetch("naaim", self._live_naaim)
        results["aaii_bull_bear"] = self._fetch("aaii_bull_bear", self._live_aaii)
        results["put_call"] = self._fetch("put_call", self._live_put_call)
        results["yield_10y"] = self._fetch("yield_10y", self._live_yield_10y)
        results["yield_2y"] = self._fetch("yield_2y", self._live_yield_2y)
        results["yield_3m"] = self._fetch("yield_3m", self._live_yield_3m)
        results["hy_oas"] = self._fetch("hy_oas", self._live_hy_oas)
        results["dxy"] = self._fetch("dxy", self._live_dxy)
        results["wti"] = self._fetch("wti", self._live_wti)
        results["gold"] = self._fetch("gold", self._live_gold)
        results["market_cap_gdp"] = self._fetch("market_cap_gdp", self._live_mktcap_gdp)
        results["pct_above_50d"] = self._fetch("pct_above_50d", self._live_breadth_50d)
        results["pct_above_200d"] = self._fetch("pct_above_200d", self._live_breadth_200d)
        # Derived spreads
        results["spread_10y_2y"] = self._derive_spread(results["yield_10y"], results["yield_2y"])
        results["spread_10y_3m"] = self._derive_spread(results["yield_10y"], results["yield_3m"])
        return results

    def _fetch(self, key: str, live_fetcher) -> Dict[str, Any]:
        val = live_fetcher()
        if val is not None:
            self.cache.set(key, val, source="live")
            return {"value": val, "stale": False, "cached": False}
        cached, stale = self.cache.get(key)
        if cached is not None:
            return {"value": cached, "stale": stale, "cached": True}
        return {"value": None, "stale": False, "cached": False}

    def _live_sp500(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_cape(self) -> Optional[float]:
        try:
            url = "https://www.multpl.com/shiller-pe"
            r = self.session.get(url, timeout=15)
            text = r.text
            # Look for a number near "Shiller PE Ratio" heading
            m = re.search(r"Shiller PE Ratio\s*.*?([0-9]+\\.?[0-9]*)", text, re.IGNORECASE | re.DOTALL)
            if m:
                val = float(m.group(1))
                if 5 < val < 100:
                    return val
            # Fallback: grab first reasonable number in page
            m = re.search(r"([0-9]{2}\\.[0-9]+)", text)
            if m:
                val = float(m.group(1))
                if 5 < val < 100:
                    return val
            return None
        except Exception:
            return None

    def _live_forward_pe(self) -> Optional[float]:
        # Yahoo doesn't expose this cleanly for ^GSPC; rely on cache/manual
        return None

    def _live_fear_greed(self) -> Optional[int]:
        try:
            url = "https://production.dataviz.cnn.io/index/fearandgreed/current"
            r = self.session.get(url, timeout=15)
            data = r.json()
            return int(data["fear_and_greed"]["score"])
        except Exception:
            return None

    def _live_naaim(self) -> Optional[float]:
        return None  # No simple API

    def _live_aaii(self) -> Optional[float]:
        return None  # No simple API

    def _live_put_call(self) -> Optional[float]:
        try:
            url = "https://www.cboe.com/us/options/market_statistics/daily/"
            r = self.session.get(url, timeout=15)
            text = r.text
            m = re.search(r"Put/Call Ratio.*?([0-9]+\\.?[0-9]*)", text, re.IGNORECASE)
            if m:
                return float(m.group(1))
            return None
        except Exception:
            return None

    def _live_yield_10y(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_yield_2y(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ETWO"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_yield_3m(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EIRX"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_hy_oas(self) -> Optional[float]:
        return None

    def _live_dxy(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_wti(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_gold(self) -> Optional[float]:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
            r = self.session.get(url, timeout=15)
            data = r.json()
            price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return float(price) if price else None
        except Exception:
            return None

    def _live_mktcap_gdp(self) -> Optional[float]:
        return None

    def _live_breadth_50d(self) -> Optional[float]:
        return None

    def _live_breadth_200d(self) -> Optional[float]:
        return None

    @staticmethod
    def _derive_spread(y10: Dict, y2: Dict) -> Dict[str, Any]:
        if y10.get("value") is not None and y2.get("value") is not None:
            val = round(y10["value"] - y2["value"], 2)
            stale = y10.get("stale", False) or y2.get("stale", False)
            return {"value": val, "stale": stale, "cached": False}
        return {"value": None, "stale": False, "cached": False}
