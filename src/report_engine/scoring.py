"""
WCVS Scoring Engine
"""

import math
from typing import Any, Dict, List, Tuple


class WCVSScorer:
    """Calculates WCVS category scores and composite."""

    CATEGORIES = {
        "fundamental": {"weight": 0.25, "name": "Fundamental Valuation"},
        "internals": {"weight": 0.20, "name": "Market Internals"},
        "sentiment": {"weight": 0.20, "name": "Sentiment & Psychology"},
        "credit": {"weight": 0.15, "name": "Credit & Liquidity"},
        "macro": {"weight": 0.20, "name": "Macro & Cross-Asset"},
    }

    def score_fundamental(self, cape: float, forward_pe: float = None, mktcap_gdp: float = None) -> Tuple[float, str]:
        """Return (score, label)."""
        scores = []
        if cape:
            if cape > 35:
                scores.append(1.0)
            elif cape > 28:
                scores.append(2.0)
            elif cape > 20:
                scores.append(3.0)
            elif cape > 15:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if forward_pe:
            if forward_pe > 22:
                scores.append(1.0)
            elif forward_pe > 19:
                scores.append(2.0)
            elif forward_pe > 16:
                scores.append(3.0)
            elif forward_pe > 13:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if mktcap_gdp:
            if mktcap_gdp > 180:
                scores.append(1.0)
            elif mktcap_gdp > 140:
                scores.append(2.0)
            elif mktcap_gdp > 100:
                scores.append(3.0)
            elif mktcap_gdp > 80:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if not scores:
            return 3.0, "Neutral"
        avg = sum(scores) / len(scores)
        return self._round_and_label(avg)

    def score_internals(self, pct_50d: float = None, pct_200d: float = None) -> Tuple[float, str]:
        scores = []
        if pct_200d is not None:
            if pct_200d < 30:
                scores.append(1.0)
            elif pct_200d < 45:
                scores.append(2.0)
            elif pct_200d < 60:
                scores.append(3.0)
            elif pct_200d < 75:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if not scores:
            return 3.0, "Neutral"
        return self._round_and_label(sum(scores) / len(scores))

    def score_sentiment(self, fear_greed: int = None, naaim: float = None, aaii: float = None, put_call: float = None) -> Tuple[float, str]:
        """Sentiment is contrarian: high optimism -> low score."""
        scores = []
        if fear_greed is not None:
            if fear_greed > 75:
                scores.append(1.0)
            elif fear_greed > 60:
                scores.append(2.0)
            elif fear_greed > 40:
                scores.append(3.0)
            elif fear_greed > 25:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if naaim is not None:
            if naaim > 95:
                scores.append(1.0)
            elif naaim > 85:
                scores.append(2.0)
            elif naaim > 60:
                scores.append(3.0)
            elif naaim > 40:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if aaii is not None:
            if aaii > 30:
                scores.append(1.0)
            elif aaii > 15:
                scores.append(2.0)
            elif aaii > -5:
                scores.append(3.0)
            elif aaii > -15:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if put_call is not None:
            if put_call < 0.75:
                scores.append(1.0)
            elif put_call < 0.90:
                scores.append(2.0)
            elif put_call < 1.10:
                scores.append(3.0)
            elif put_call < 1.30:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if not scores:
            return 3.0, "Neutral"
        return self._round_and_label(sum(scores) / len(scores))

    def score_credit(self, spread_10y_2y: float = None, spread_10y_3m: float = None, hy_oas: float = None) -> Tuple[float, str]:
        scores = []
        # Use 10Y-2Y as primary curve signal
        s = spread_10y_2y if spread_10y_2y is not None else spread_10y_3m
        if s is not None:
            if s < 0:
                scores.append(1.0)
            elif s < 50:
                scores.append(2.0)
            elif s < 100:
                scores.append(3.0)
            elif s < 200:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if hy_oas is not None:
            if hy_oas > 600:
                scores.append(1.0)
            elif hy_oas > 400:
                scores.append(2.0)
            elif hy_oas > 300:
                scores.append(3.0)
            elif hy_oas > 200:
                scores.append(4.0)
            else:
                scores.append(5.0)
        if not scores:
            return 3.0, "Neutral"
        return self._round_and_label(sum(scores) / len(scores))

    def score_macro(self, dxy: float = None, wti: float = None, gold: float = None) -> Tuple[float, str]:
        scores = []
        # Oil is a key macro stress signal
        if wti is not None:
            if wti > 100:
                scores.append(1.0)
            elif wti > 85:
                scores.append(2.0)
            elif wti > 65:
                scores.append(3.0)
            elif wti > 50:
                scores.append(4.0)
            else:
                scores.append(5.0)
        # Gold spike often signals distrust/instability
        if gold is not None:
            if gold > 2500:
                scores.append(2.0)  # elevated safe-haven demand
            elif gold > 2000:
                scores.append(3.0)
            else:
                scores.append(4.0)
        if not scores:
            return 3.0, "Neutral"
        return self._round_and_label(sum(scores) / len(scores))

    def calculate_composite(self, category_scores: Dict[str, float]) -> Tuple[float, str, str]:
        """Return (composite_score, rating_text, rating_class)."""
        total = 0.0
        for key, info in self.CATEGORIES.items():
            total += info["weight"] * category_scores.get(key, 3.0)
        composite = round(total, 1)
        if composite <= 1.9:
            return composite, "Severely Overvalued", "rating-red"
        elif composite <= 3.0:
            return composite, "Overvalued / Risk-Adjusted Neutral", "rating-orange"
        elif composite <= 4.0:
            return composite, "Fairly Valued", "rating-green"
        else:
            return composite, "Undervalued / Attractive", "rating-green"

    @staticmethod
    def expected_returns(cape: float) -> List[Dict[str, Any]]:
        """Generate forward return expectation table."""
        horizons = [1, 3, 5, 10, 15]
        confidences = {1: "Low", 3: "Moderate", 5: "Moderate", 10: "Higher", 15: "Higher"}
        results = []
        for h in horizons:
            base = -0.08 * math.log(cape / 17.0) if cape > 0 else 0.0
            term = 0.03 * math.sqrt(min(h, 15) / 15.0)
            exp_ret = round(base + term, 1)
            results.append({
                "horizon": f"{h} Year{'s' if h > 1 else ''}",
                "expected_return": f"{exp_ret:+.1f}" if exp_ret != 0 else "0.0",
                "confidence": confidences[h],
            })
        return results

    @staticmethod
    def _round_and_label(score: float) -> Tuple[float, str]:
        rounded = round(score * 2) / 2  # round to nearest 0.5
        if rounded <= 1.5:
            return rounded, "Extreme"
        elif rounded <= 2.5:
            return rounded, "Unfavorable"
        elif rounded <= 3.5:
            return rounded, "Neutral"
        elif rounded <= 4.5:
            return rounded, "Favorable"
        else:
            return rounded, "Attractive"
