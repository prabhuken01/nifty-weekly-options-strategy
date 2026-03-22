"""Tier-0 Greeks monitoring copy — show before ranked combos."""

import streamlit as st

from config.greeks_matrix import dte_to_bucket, lookup


def render_greeks_monitoring_guide(dte: int, strategy_keys: list[str]) -> None:
    """Expandable checklist driven by GREEKS_MATRIX for selected strategies."""
    b = dte_to_bucket(dte)
    with st.expander("📋 **Greeks monitoring guide** (Tier 0 — read before picking strikes)", expanded=False):
        st.caption(
            f"DTE bucket **{b}** (from {dte} calendar days to expiry). "
            "Grades A/B/C in signals use these bands."
        )
        for sk in strategy_keys:
            spec = lookup(sk, dte)
            if not spec:
                continue
            lo, hi = spec["range"]
            st.markdown(
                f"**{sk.replace('_', ' ').title()}** — prioritize **{spec['best_greek'].upper()}** "
                f"in [{lo:.3g}, {hi:.3g}] · _{spec['why']}_"
            )


def strategy_keys_for_regime(market_condition: str) -> list[str]:
    m = {
        "bullish": ["bull_call_spread"],
        "bearish": ["bear_put_spread"],
        "sideways": ["short_strangle"],
        "high_volatility": ["long_strangle"],
    }
    return m.get(market_condition, ["bull_call_spread", "bear_put_spread", "short_strangle", "long_strangle"])
