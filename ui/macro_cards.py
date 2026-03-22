"""Tier-1 macro strategy cards (synthetic probabilities + IV context)."""

import streamlit as st


def _card(title: str, body: str, accent: str) -> str:
    return f"""
    <div class="strategy-card-lite" style="border-left:4px solid {accent};padding:0.85rem 1rem;margin-bottom:0.5rem;
         background:rgba(30,41,59,0.55);border-radius:10px;">
      <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem;margin-bottom:0.35rem">{title}</div>
      <div style="color:#94a3b8;font-size:0.78rem;line-height:1.45">{body}</div>
    </div>
    """


def render_macro_strategy_row(
    market_condition: str,
    iv_rank: float,
    tte_days: int,
    bullish_prob: float,
) -> None:
    """Four playbook cards + synthetic headline metrics."""
    st.markdown("#### Strategy playbooks (macro view)")
    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("Bull Call Spread", "Debit vertical · capped risk · trend days", "#00d4aa"),
        ("Bear Put Spread", "Downside hedge · defined risk", "#ff6b6b"),
        ("Short Strangle", "Range + IV crush · tail risk", "#fbbf24"),
        ("Long Strangle", "Vol expansion · breakout plays", "#a78bfa"),
    ]
    highlight = {
        "bullish": 0,
        "bearish": 1,
        "sideways": 2,
        "high_volatility": 3,
    }.get(market_condition, -1)

    for i, (title, body, color) in enumerate(cards):
        col = [c1, c2, c3, c4][i]
        with col:
            if i == highlight:
                body = f"<strong style='color:#f1f5f9'>Regime match: {market_condition}</strong><br><br>" + body
            st.markdown(_card(title, body, color), unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Synthetic P(bullish week)", f"{bullish_prob:.0%}", help="Heuristic from RSI/SMA alignment — not a forecast.")
    m2.metric("IV rank", f"{iv_rank:.0f}%", help="Where current IV sits vs simulated 52-week band.")
    m3.metric("TTE (days)", f"{tte_days}", help="Days to expiry for weekly options.")
