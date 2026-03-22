"""
Tier-0: which Greek to prioritize by strategy and days-to-expiry bucket.
Simplified ranges use net delta for vertical spreads (buy CE delta − sell CE delta) or |buy_delta| for single-leg style rows where applicable.
"""

from typing import Any, Dict, Optional, Tuple

# DTE bucket: 4 = 4+ days, 3 = exactly ~3, 2 = 1-2 days
DTEBucket = int


def dte_to_bucket(dte: int) -> DTEBucket:
    if dte >= 4:
        return 4
    if dte == 3:
        return 3
    return 2


def _entry(
    best: str,
    lo: float,
    hi: float,
    why: str,
) -> Dict[str, Any]:
    return {"best_greek": best, "range": (lo, hi), "why": why}


# strategy_key -> bucket -> spec
GREEKS_MATRIX: Dict[str, Dict[int, Dict[str, Any]]] = {
    "bull_call_spread": {
        4: _entry("delta", 0.12, 0.35, "Direction matters early in the week."),
        3: _entry("delta", 0.15, 0.38, "Need clearer directional edge as theta ramps."),
        2: _entry("gamma", 0.004, 0.025, "Pinch risk — watch net gamma."),
    },
    "bear_put_spread": {
        4: _entry("delta", -0.35, -0.12, "Put spread net delta (negative)."),
        3: _entry("delta", -0.38, -0.14, "Stronger bearish conviction."),
        2: _entry("gamma", 0.004, 0.025, "Gamma risk on short leg."),
    },
    "short_strangle": {
        4: _entry("theta", 5.0, 50.0, "Theta ₹/day per lot (scale-free band)."),
        3: _entry("theta", 8.0, 60.0, "Decay accelerates."),
        2: _entry("gamma", 0.01, 0.04, "Wings — gamma explodes near expiry."),
    },
    "long_strangle": {
        4: _entry("vega", 8.0, 80.0, "Vega ₹ per 1% IV (per lot) — need vol expansion."),
        3: _entry("vega", 8.0, 75.0, "Still vega-heavy."),
        2: _entry("gamma", 0.015, 0.05, "Needs a big move soon."),
    },
}


def lookup(strategy_key: str, dte: int) -> Optional[Dict[str, Any]]:
    b = dte_to_bucket(dte)
    return GREEKS_MATRIX.get(strategy_key, {}).get(b)


def grade_value(strategy_key: str, dte: int, net_delta: float, net_gamma: float, net_theta: float, net_vega: float) -> Tuple[str, str]:
    """
    Returns (grade 'A'|'B'|'C', message).
    Uses net greeks from spread where relevant.
    """
    spec = lookup(strategy_key, dte)
    if not spec:
        return "B", "No matrix row — neutral grade"

    g = spec["best_greek"]
    lo, hi = spec["range"]

    if g == "delta":
        v = abs(net_delta)
        lo, hi = (min(abs(lo), abs(hi)), max(abs(lo), abs(hi)))
    elif g == "gamma":
        v = abs(net_gamma)
    elif g == "theta":
        v = abs(net_theta) * 50  # per lot rupee scale
    else:  # vega
        v = abs(net_vega) * 50

    if lo <= v <= hi:
        return "A", f"{g.title()} in ideal band ({lo:.3g}–{hi:.3g})"
    if lo * 0.7 <= v <= hi * 1.3:
        return "B", f"{g.title()} acceptable (watch {g})"
    return "C", f"{g.title()} outside comfort zone for {dte} DTE"
