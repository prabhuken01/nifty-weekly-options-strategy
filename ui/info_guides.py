"""One-line tab hints — keep copy short for scannability."""

TAB_HINTS = {
    "market": "Price & regime snapshot — use with **Strategy focus** in the sidebar.",
    "chain": "OI / Vol in **₹ Cr** = notional liquidity at each strike (lot × LTP).",
    "builder": "Payoff curves are **at expiry**; live P&L moves with spot & IV.",
    "mc": "Terminal distribution assumes lognormal GBM — same model as POP engine.",
    "analytics": "**MC cone** = path percentiles by day; **Greeks path** uses the mean path; **PIT** = BS on history + IV you set.",
    "backtest": "Synthetic weekly history — **Merit** blends POP, R:R, and outcome for sorting.",
    "signals": "Ranked by **Greek grade** (A/B/C) then composite **score** — pick one row and trade the strikes.",
}


def render_tab_hint(tab_key: str):
    import streamlit as st

    msg = TAB_HINTS.get(tab_key, "")
    if msg:
        st.caption(msg)
