"""
NIFTY Weekly Options Quantitative Trading Dashboard
====================================================
A comprehensive Streamlit dashboard for analyzing NIFTY weekly options,
running Monte Carlo simulations, backtesting strategies, and generating
trade signals.
"""

import sys
from pathlib import Path

# Repo root on Streamlit Cloud / local — ensures `config`, `data`, … import reliably
_APP_DIR = Path(__file__).resolve().parent
_root = str(_APP_DIR)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from config.settings import (
    NIFTY_LOT_SIZE, RISK_FREE_RATE, DEFAULT_CAPITAL,
    STRATEGY_PARAMS, INDICATOR_PARAMS, MONTE_CARLO_SIMS,
)
from data.sample_data import (
    generate_option_chain, generate_nifty_history, generate_backtest_results,
    generate_iv_history,
)
from indicators.technical import enrich_dataframe, classify_market
from options.chain_processor import enrich_chain, compute_pcr, max_pain
from options.liquidity_filter import filter_liquid_strikes
from strike_selection.selector import StrikeSelector
from probability.monte_carlo import simulate_terminal_prices
from probability.black_scholes import bs_pop_above, bs_pop_between
from probability.pop_estimator import POPEstimator
from backtest.metrics import compute_metrics, equity_curve
from strategy.spreads import (
    bull_call_payoff, bear_put_payoff, long_strangle_payoff,
    short_strangle_payoff, iron_condor_payoff,
)

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NIFTY Options Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #a8a4ce;
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    .metric-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }
    .metric-card .label {
        color: #8b8fa3;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.4rem;
    }
    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }
    .metric-card .sub {
        color: #6b7280;
        font-size: 0.75rem;
    }
    .green { color: #00d4aa; }
    .red { color: #ff6b6b; }
    .blue { color: #4ecdc4; }
    .purple { color: #a78bfa; }
    .orange { color: #fbbf24; }
    .white { color: #e2e8f0; }

    .signal-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-left: 4px solid;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
    }
    .signal-high { border-color: #00d4aa; }
    .signal-medium { border-color: #fbbf24; }
    .signal-low { border-color: #ff6b6b; }

    .condition-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-bullish { background: rgba(0, 212, 170, 0.15); color: #00d4aa; border: 1px solid rgba(0, 212, 170, 0.3); }
    .badge-bearish { background: rgba(255, 107, 107, 0.15); color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.3); }
    .badge-sideways { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .badge-high_volatility { background: rgba(167, 139, 250, 0.15); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29, #1a1a2e);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1rem;
    }
    /* Streamlit metrics: readable on dark cards */
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {
        color: #cbd5e1 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f8fafc !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #e2e8f0 !important;
    }
    /* Sidebar inputs */
    div[data-testid="stSidebar"] label { color: #e2e8f0 !important; }
    div[data-testid="stSidebar"] .stMarkdown p { color: #cbd5e1; }
    /* Main area: inputs readable on dark theme */
    div[data-testid="stNumberInput"] input,
    div[data-testid="stNumberInput"] input:focus {
        color: #f8fafc !important;
        background-color: #334155 !important;
        -webkit-text-fill-color: #f8fafc !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        color: #f1f5f9 !important;
        background-color: #334155 !important;
    }
    div[data-testid="stMultiSelect"] span { color: #e2e8f0 !important; }
    div[data-testid="stRadio"] label { color: #e2e8f0 !important; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    spot_price = st.number_input("NIFTY Spot Price", value=23000.0, step=50.0, format="%.1f")
    tte_days = st.slider("Days to Expiry", 1, 7, 5)
    base_iv = st.slider("Base IV (%)", 8, 40, 14) / 100
    capital = st.number_input("Capital (₹)", value=float(DEFAULT_CAPITAL), step=50000.0, format="%.0f")

    st.markdown("---")
    st.markdown("### 🎯 Strategy Filters")
    min_rr = st.slider("Min Risk:Reward", 1.0, 5.0, STRATEGY_PARAMS["min_risk_reward"], 0.1)
    min_pop = st.slider("Min POP (%)", 30, 80, int(STRATEGY_PARAMS["min_pop"] * 100)) / 100
    n_sims = st.select_slider("Monte Carlo Sims", options=[10000, 25000, 50000, 100000], value=MONTE_CARLO_SIMS)

    st.markdown("---")
    st.markdown("### 📊 Liquidity Filters")
    min_oi = int(st.number_input("Min Open Interest", value=50000.0, step=10000.0, format="%.0f"))
    min_vol = int(st.number_input("Min Volume", value=500.0, step=100.0, format="%.0f"))

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#6b7280; font-size:0.75rem;'>"
        "Built with the NIFTY Weekly Options<br>Quantitative Trading Model"
        "</div>",
        unsafe_allow_html=True,
    )


# ─── Data Generation ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data(spot, tte, iv):
    chain = generate_option_chain(spot, tte, iv)
    # Scale synthetic history so last close matches sidebar spot (technical snapshot aligns)
    history = generate_nifty_history(252, start_price=float(spot) * 0.92, end_price=float(spot))
    backtest = generate_backtest_results(52)
    return chain, history, backtest

chain_df, history_df, backtest_df = load_data(spot_price, tte_days, base_iv)

# IV Rank: where current IV sits vs. simulated 52-week history (0 = lowest, 100 = highest)
_iv_history = generate_iv_history(base_iv)
_iv_min, _iv_max = float(_iv_history.min()), float(_iv_history.max())
iv_rank = float((base_iv - _iv_min) / (_iv_max - _iv_min) * 100) if _iv_max > _iv_min else 50.0
iv_rank_label = "Low — prefer buying" if iv_rank < 30 else "Elevated — favor selling" if iv_rank > 60 else "Moderate"

enriched_history = enrich_dataframe(history_df)
enriched_chain = enrich_chain(chain_df, spot_price, tte_days)
liquid_chain = filter_liquid_strikes(enriched_chain, min_oi, min_vol)

latest = enriched_history.iloc[-1]
# Align regime with last bar (series scaled to end at configured spot)
latest_close = float(latest["close"])
market_condition = classify_market(
    latest_close, float(latest["rsi_14"]), float(latest["sma_20"]), float(latest["sma_50"]),
    base_iv, base_iv * 0.95,
)

pcr_data = compute_pcr(enriched_chain)
mp = max_pain(enriched_chain)


# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown(
    f"""<div class="main-header">
        <h1>⚡ NIFTY Options Command Center</h1>
        <p>Real-time quantitative analysis &bull; Weekly expiry strategies &bull;
        Monte Carlo simulations &bull; {datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
    </div>""",
    unsafe_allow_html=True,
)


# ─── Top Metrics Row ─────────────────────────────────────────────────────────

badge_class = f"badge-{market_condition}"
condition_html = f'<span class="condition-badge {badge_class}">{market_condition}</span>'

cols = st.columns(6)
metrics = [
    ("NIFTY SPOT", f"₹{latest_close:,.0f}", "white",
     f"ATM: {int(round(float(spot_price) / 50) * 50)}",
     "Last traded price of NIFTY 50 index. ATM = nearest 50-pt strike to spot."),
    ("MARKET", condition_html, "",
     f"RSI: {latest['rsi_14']:.1f}",
     "Market regime detected from RSI + SMA alignment. Drives strategy selection."),
    ("IV LEVEL", f"{base_iv*100:.1f}%", "purple",
     f"IV Rank: {iv_rank:.0f}% — {iv_rank_label}",
     f"Implied Volatility — how nervous the market is. {base_iv*100:.0f}% IV → NIFTY expected to move ~{base_iv/np.sqrt(52)*100:.1f}% this week. IV Rank shows where current IV sits vs the past 52 weeks."),
    ("PCR (OI)", f"{pcr_data['oi_pcr']:.2f}",
     "blue" if pcr_data['oi_pcr'] > 1 else "orange",
     pcr_data['interpretation'].title(),
     "Put-Call Ratio (Open Interest). >1 = more puts held (bearish bets). <1 = more calls (bullish bets). ~1 = neutral/balanced market."),
    ("MAX PAIN", f"₹{mp:,.0f}", "orange",
     f"Dist: {(mp-spot_price)/spot_price*100:+.1f}%",
     "Strike price where option sellers (writers) lose the least money. Market historically gravitates toward this level at expiry."),
    ("DAYS TO EXPIRY", f"{tte_days}", "green",
     "Weekly Thursday expiry",
     "Calendar days until Thursday expiry. Options lose value (theta decay) fastest in the last 5 days."),
]

for i, (label, value, color, sub, tooltip) in enumerate(metrics):
    with cols[i]:
        if label == "MARKET":
            st.markdown(
                f'<div class="metric-card" title="{tooltip}"><div class="label">{label}</div>'
                f'<div style="margin:0.5rem 0">{value}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="metric-card" title="{tooltip}"><div class="label">{label}</div>'
                f'<div class="value {color}">{value}</div>'
                f'<div class="sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)


# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Market Overview",
    "🔗 Option Chain",
    "🎯 Strategy Builder",
    "🎲 Monte Carlo Lab",
    "📊 Backtest Results",
    "🚀 Trade Signals",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Market Overview
# ═══════════════════════════════════════════════════════════════════════════════

def _plotly_axis_style(fig):
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.2)",
        tickfont=dict(color="#cbd5e1"), title_font=dict(color="#e2e8f0"),
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.2)",
        tickfont=dict(color="#cbd5e1"), title_font=dict(color="#e2e8f0"),
    )


with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### NIFTY — Price & moving averages")
        fig_price = go.Figure()
        fig_price.add_trace(go.Candlestick(
            x=enriched_history["date"],
            open=enriched_history["open"], high=enriched_history["high"],
            low=enriched_history["low"], close=enriched_history["close"],
            name="NIFTY", increasing_line_color="#00d4aa", decreasing_line_color="#ff6b6b",
        ))
        for col_name, color, dash in [
            ("sma_20", "#4ecdc4", "solid"),
            ("sma_50", "#fbbf24", "dash"),
            ("bb_upper", "#a78bfa", "dot"),
            ("bb_lower", "#a78bfa", "dot"),
        ]:
            fig_price.add_trace(go.Scatter(
                x=enriched_history["date"], y=enriched_history[col_name],
                name=col_name.upper().replace("_", " "),
                line=dict(color=color, width=1.5, dash=dash),
                opacity=0.85,
            ))
        fig_price.update_layout(
            template="plotly_dark",
            height=440,
            margin=dict(l=60, r=30, t=50, b=50),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
            xaxis_rangeslider_visible=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,12,41,0.55)",
            font=dict(family="Inter", color="#e2e8f0"),
            xaxis_title="Date",
            yaxis_title="Price (₹)",
        )
        _plotly_axis_style(fig_price)
        st.plotly_chart(fig_price, use_container_width=True)

        rsi_c, vol_c = st.columns(2)
        with rsi_c:
            st.markdown("#### RSI (14)")
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=enriched_history["date"], y=enriched_history["rsi_14"],
                name="RSI", line=dict(color="#a78bfa", width=2),
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="rgba(255,107,107,0.6)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="rgba(0,212,170,0.6)")
            fig_rsi.add_hrect(y0=30, y1=70, fillcolor="rgba(167,139,250,0.06)", line_width=0)
            fig_rsi.update_layout(
                template="plotly_dark", height=300,
                margin=dict(l=50, r=20, t=30, b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.55)",
                font=dict(color="#e2e8f0"), showlegend=False,
                xaxis_title="Date", yaxis_title="RSI",
            )
            _plotly_axis_style(fig_rsi)
            st.plotly_chart(fig_rsi, use_container_width=True)

        with vol_c:
            st.markdown("#### Volume")
            vol_colors = ["#00d4aa" if c >= o else "#ff6b6b"
                          for c, o in zip(enriched_history["close"], enriched_history["open"])]
            fig_vol = go.Figure(go.Bar(
                x=enriched_history["date"], y=enriched_history["volume"],
                name="Volume", marker_color=vol_colors, opacity=0.65,
            ))
            fig_vol.update_layout(
                template="plotly_dark", height=300,
                margin=dict(l=50, r=20, t=30, b=40),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.55)",
                font=dict(color="#e2e8f0"), showlegend=False,
                xaxis_title="Date", yaxis_title="Volume",
            )
            _plotly_axis_style(fig_vol)
            st.plotly_chart(fig_vol, use_container_width=True)

    with col2:
        st.markdown("### Technical Snapshot")
        st.caption(
            "Synthetic history scaled so last close = NIFTY spot in sidebar. "
            "Indicators are computed on that series (not live NSE data)."
        )

        v20 = latest["vwap_20d"]
        v20_ok = pd.notna(v20)
        _rsi = float(latest['rsi_14'])
        _rsi_color = "red" if _rsi > 70 else "green" if _rsi < 30 else "blue"
        _rsi_interp = "Overbought — bearish signal" if _rsi > 70 else "Oversold — bullish signal" if _rsi < 30 else "Neutral — no directional signal yet"
        indicators = {
            "Close": (f"₹{latest_close:,.2f}", "white"),
            "SMA 20": (f"₹{latest['sma_20']:,.2f}", "green" if latest_close > latest['sma_20'] else "red"),
            "SMA 50": (f"₹{latest['sma_50']:,.2f}", "green" if latest_close > latest['sma_50'] else "red"),
            "RSI 14": (f"{_rsi:.1f}", _rsi_color),
            "VWAP (20d)": (
                f"₹{float(v20):,.2f}" if v20_ok else "—",
                "blue" if v20_ok and latest_close > v20 else "orange" if v20_ok else "blue",
            ),
            "BB Upper": (f"₹{latest['bb_upper']:,.2f}", "purple"),
            "BB Lower": (f"₹{latest['bb_lower']:,.2f}", "purple"),
            "ATR 14 (Daily Range)": (f"{latest['atr_14']:.0f} pts", "orange"),
            "Daily Return": (f"{latest['daily_return']*100:+.2f}%", "green" if latest['daily_return'] > 0 else "red"),
        }

        _row_style = 'display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid rgba(255,255,255,0.05)'
        for name, (val, color) in indicators.items():
            st.markdown(
                f'<div style="{_row_style}">'
                f'<span style="color:#8b8fa3;font-size:0.85rem">{name}</span>'
                f'<span class="{color}" style="font-weight:600;font-size:0.85rem">{val}</span></div>',
                unsafe_allow_html=True,
            )
            # RSI interpretation sub-row
            if name == "RSI 14":
                st.markdown(
                    f'<div style="padding:0.15rem 0 0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.05)">'
                    f'<span style="color:#6b7280;font-size:0.75rem;font-style:italic">{_rsi_interp}</span></div>',
                    unsafe_allow_html=True,
                )
            # ATR explanation sub-row
            if name == "ATR 14 (Daily Range)":
                st.markdown(
                    f'<div style="padding:0.15rem 0 0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.05)">'
                    f'<span style="color:#6b7280;font-size:0.75rem;font-style:italic">avg high-to-low swing per day</span></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Market Regime Distribution")

        regime_counts = {"bullish": 0, "bearish": 0, "sideways": 0, "high_volatility": 0}
        recent = enriched_history.tail(60)
        for _, row in recent.iterrows():
            if pd.notna(row["rsi_14"]) and pd.notna(row["sma_20"]) and pd.notna(row["sma_50"]):
                cond = classify_market(row["close"], row["rsi_14"], row["sma_20"], row["sma_50"], base_iv, base_iv * 0.95)
                regime_counts[cond] = regime_counts.get(cond, 0) + 1

        fig_regime = go.Figure(go.Pie(
            labels=list(regime_counts.keys()),
            values=list(regime_counts.values()),
            hole=0.55,
            marker=dict(colors=["#00d4aa", "#ff6b6b", "#fbbf24", "#a78bfa"]),
            textinfo="label+percent",
            textfont=dict(size=11),
        ))
        fig_regime.update_layout(
            template="plotly_dark", height=280,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig_regime, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Option Chain
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("### Live Option Chain Analysis")

    oc_col1, oc_col2, oc_col3 = st.columns(3)
    with oc_col1:
        chain_view = st.radio("View", ["All Strikes", "Liquid Only", "ATM ± 5"], horizontal=True)
    with oc_col2:
        greek_display = st.multiselect("Greeks", ["delta", "gamma", "theta", "vega"], default=["delta", "theta"])
    with oc_col3:
        sort_by = st.selectbox("Sort by", ["strike_price", "open_interest", "volume", "iv"])

    if chain_view == "Liquid Only":
        display_chain = liquid_chain
    elif chain_view == "ATM ± 5":
        atm = round(spot_price / 50) * 50
        display_chain = enriched_chain[
            (enriched_chain["strike_price"] >= atm - 250) &
            (enriched_chain["strike_price"] <= atm + 250)
        ]
    else:
        display_chain = enriched_chain

    display_chain = display_chain.sort_values(sort_by)

    # ATM / ITM / OTM colour legend
    st.markdown(
        '<div style="display:flex;gap:1.5rem;align-items:center;padding:0.5rem 0;margin-bottom:0.5rem">'
        '<span style="color:#8b8fa3;font-size:0.78rem;font-weight:500">Strike colours:</span>'
        '<span style="background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.4);'
        'border-radius:6px;padding:2px 10px;font-size:0.75rem;font-weight:600">ATM</span>'
        '<span style="background:rgba(78,205,196,0.12);color:#4ecdc4;border:1px solid rgba(78,205,196,0.35);'
        'border-radius:6px;padding:2px 10px;font-size:0.75rem;font-weight:600">ITM — deeper in money</span>'
        '<span style="background:rgba(107,114,128,0.15);color:#9ca3af;border:1px solid rgba(107,114,128,0.35);'
        'border-radius:6px;padding:2px 10px;font-size:0.75rem;font-weight:600">OTM — out of money</span>'
        '<span style="color:#6b7280;font-size:0.73rem;font-style:italic">High OI = liquid (easy to enter/exit)</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Liquidity warning: flag strikes where bid-ask spread > 0.5% of LTP
    if "ask" in display_chain.columns and "bid" in display_chain.columns and "ltp" in display_chain.columns:
        _ltp_safe = display_chain["ltp"].replace(0, np.nan)
        _spread_pct = (display_chain["ask"] - display_chain["bid"]) / _ltp_safe * 100
        _illiquid = display_chain[_spread_pct > 0.5]["strike_price"].unique()
        if len(_illiquid) > 0:
            _bad_str = ", ".join([str(int(s)) for s in sorted(_illiquid)[:10]])
            st.markdown(
                f'<div style="background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.3);'
                f'border-radius:8px;padding:0.5rem 1rem;margin-bottom:0.5rem;font-size:0.8rem;color:#ff6b6b">'
                f'⚠ <strong>Illiquid strikes</strong> (bid-ask spread &gt;0.5% of LTP): {_bad_str} — '
                f'wide spreads mean you lose money just entering. Prefer liquid strikes.</div>',
                unsafe_allow_html=True,
            )

    calls = display_chain[display_chain["instrument_type"] == "CE"].set_index("strike_price")
    puts = display_chain[display_chain["instrument_type"] == "PE"].set_index("strike_price")

    col_ce, col_mid, col_pe = st.columns([5, 1, 5])

    with col_ce:
        st.markdown("#### 📗 CALLS (CE)")
        call_cols = ["ltp", "iv", "volume", "open_interest", "oi_change"] + greek_display
        available_cols = [c for c in call_cols if c in calls.columns]
        # Plain dataframe avoids optional jinja2 / Styler issues on Streamlit Cloud
        st.dataframe(
            calls[available_cols],
            height=500,
            use_container_width=True,
            hide_index=False,
        )

    with col_mid:
        st.markdown("#### Strike")
        strikes = sorted(display_chain["strike_price"].unique())
        for s in strikes:
            color = "#fbbf24" if s == round(spot_price / 50) * 50 else "#6b7280"
            st.markdown(f'<div style="text-align:center;color:{color};padding:2px;font-size:0.8rem;font-weight:600">{int(s)}</div>', unsafe_allow_html=True)

    with col_pe:
        st.markdown("#### 📕 PUTS (PE)")
        put_cols = ["ltp", "iv", "volume", "open_interest", "oi_change"] + greek_display
        available_cols = [c for c in put_cols if c in puts.columns]
        st.dataframe(
            puts[available_cols],
            height=500,
            use_container_width=True,
            hide_index=False,
        )

    st.markdown("---")

    oi_col1, oi_col2 = st.columns(2)

    with oi_col1:
        st.markdown("### Open Interest Distribution")
        oi_fig = go.Figure()
        for opt_type, color in [("CE", "#00d4aa"), ("PE", "#ff6b6b")]:
            data = enriched_chain[enriched_chain["instrument_type"] == opt_type]
            oi_fig.add_trace(go.Bar(
                x=data["strike_price"], y=data["open_interest"],
                name=opt_type, marker_color=color, opacity=0.8,
            ))
        oi_fig.add_vline(x=spot_price, line_dash="dash", line_color="#fbbf24", annotation_text="Spot")
        oi_fig.add_vline(x=mp, line_dash="dot", line_color="#a78bfa", annotation_text="Max Pain")
        oi_fig.update_layout(
            template="plotly_dark", height=400, barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.5)",
            xaxis_title="Strike Price", yaxis_title="Open Interest",
        )
        st.plotly_chart(oi_fig, use_container_width=True)

    with oi_col2:
        st.markdown("### IV Smile / Skew")
        iv_fig = go.Figure()
        for opt_type, color in [("CE", "#4ecdc4"), ("PE", "#ff6b6b")]:
            data = enriched_chain[enriched_chain["instrument_type"] == opt_type].sort_values("strike_price")
            iv_fig.add_trace(go.Scatter(
                x=data["strike_price"], y=data["iv"] * 100,
                name=f"{opt_type} IV", mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5),
            ))
        iv_fig.add_vline(x=spot_price, line_dash="dash", line_color="#fbbf24", annotation_text="Spot")
        iv_fig.update_layout(
            template="plotly_dark", height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.5)",
            xaxis_title="Strike Price", yaxis_title="Implied Volatility (%)",
        )
        st.plotly_chart(iv_fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: Strategy Builder
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("### Interactive Strategy Payoff Builder")

    with st.expander("📖 Strategy term glossary — hover over any term to learn more"):
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("""
**Net Premium** — Total cash received (credit) or paid (debit) upfront.
- Debit: you pay to enter (e.g. ₹120 debit × 50 lot = ₹6,000 max risk)
- Credit: you receive cash (e.g. ₹65 credit = ₹3,250 income, also your max profit)

**Max Profit / Max Loss** — The absolute best and worst-case outcomes at expiry.
For spreads these are *fixed* — your loss can never exceed Max Loss no matter what happens.

**Breakeven** — The NIFTY level at expiry where P&L = ₹0.
If NIFTY closes exactly at breakeven, you neither profit nor lose.
""")
        with g2:
            st.markdown("""
**POP (Probability of Profit)** — From Monte Carlo simulation: % of simulated expiries
where this trade ends profitable. 60% POP = profitable in 60 of 100 simulated outcomes.

**R:R (Risk:Reward)** — Potential gain ÷ potential loss.
R:R of 2.0 = earn ₹2 for every ₹1 risked. Higher is better, but higher R:R
usually means lower POP (the trade is harder to win).

**Lot size** — NIFTY options trade in lots of 50. All P&L figures include the full lot.
""")

    sb_col1, sb_col2 = st.columns([1, 2])

    with sb_col1:
        strategy_type = st.selectbox("Strategy", [
            "Bull Call Spread", "Bear Put Spread",
            "Long Strangle", "Short Strangle",
            "Long Straddle", "Short Straddle",
            "Iron Condor",
        ])

        atm_strike = float(round(float(spot_price) / 50) * 50)
        spot_range = np.linspace(float(spot_price) * 0.92, float(spot_price) * 1.08, 500)

        if strategy_type == "Bull Call Spread":
            buy_k = st.number_input("Buy Call Strike", value=atm_strike, step=50.0, format="%.0f")
            sell_k = st.number_input("Sell Call Strike", value=atm_strike + 200.0, step=50.0, format="%.0f")
            premium = st.number_input("Net Premium Paid", value=85.0, step=5.0, format="%.1f")
            payoff = bull_call_payoff(spot_range, buy_k, sell_k, premium, NIFTY_LOT_SIZE)

        elif strategy_type == "Bear Put Spread":
            buy_k = st.number_input("Buy Put Strike", value=atm_strike, step=50.0, format="%.0f")
            sell_k = st.number_input("Sell Put Strike", value=atm_strike - 200.0, step=50.0, format="%.0f")
            premium = st.number_input("Net Premium Paid", value=80.0, step=5.0, format="%.1f")
            payoff = bear_put_payoff(spot_range, buy_k, sell_k, premium, NIFTY_LOT_SIZE)

        elif strategy_type in ("Long Strangle", "Short Strangle"):
            put_k = st.number_input("Put Strike", value=atm_strike - 200.0, step=50.0, format="%.0f")
            call_k = st.number_input("Call Strike", value=atm_strike + 200.0, step=50.0, format="%.0f")
            premium = st.number_input("Total Premium", value=120.0, step=5.0, format="%.1f")
            if strategy_type == "Long Strangle":
                payoff = long_strangle_payoff(spot_range, put_k, call_k, premium, NIFTY_LOT_SIZE)
            else:
                payoff = short_strangle_payoff(spot_range, put_k, call_k, premium, NIFTY_LOT_SIZE)

        elif strategy_type in ("Long Straddle", "Short Straddle"):
            straddle_k = st.number_input("Straddle Strike", value=atm_strike, step=50.0, format="%.0f")
            premium = st.number_input("Total Premium", value=200.0, step=5.0, format="%.1f")
            if strategy_type == "Long Straddle":
                payoff = (np.abs(spot_range - straddle_k) - premium) * NIFTY_LOT_SIZE
            else:
                payoff = (premium - np.abs(spot_range - straddle_k)) * NIFTY_LOT_SIZE

        else:  # Iron Condor
            pb = st.number_input("Put Buy Strike", value=atm_strike - 300.0, step=50.0, format="%.0f")
            ps = st.number_input("Put Sell Strike", value=atm_strike - 150.0, step=50.0, format="%.0f")
            cs = st.number_input("Call Sell Strike", value=atm_strike + 150.0, step=50.0, format="%.0f")
            cb = st.number_input("Call Buy Strike", value=atm_strike + 300.0, step=50.0, format="%.0f")
            premium = st.number_input("Net Credit", value=65.0, step=5.0, format="%.1f")
            payoff = iron_condor_payoff(spot_range, pb, ps, cs, cb, premium, NIFTY_LOT_SIZE)

    with sb_col2:
        fig_payoff = go.Figure()

        colors = np.where(payoff >= 0, "rgba(0,212,170,0.6)", "rgba(255,107,107,0.6)")
        fig_payoff.add_trace(go.Scatter(
            x=spot_range, y=payoff,
            fill="tozeroy",
            fillcolor="rgba(0,212,170,0.1)",
            line=dict(color="#00d4aa", width=2.5),
            name="P&L",
        ))

        fig_payoff.add_vline(x=spot_price, line_dash="dash", line_color="#fbbf24",
                             annotation_text=f"Spot: {spot_price:,.0f}")
        fig_payoff.add_hline(y=0, line_color="rgba(255,255,255,0.3)", line_width=1)

        max_p = float(np.max(payoff))
        max_l = float(np.min(payoff))
        be_indices = np.where(np.diff(np.sign(payoff)))[0]
        for idx in be_indices:
            be_price = spot_range[idx]
            fig_payoff.add_vline(x=be_price, line_dash="dot", line_color="#a78bfa",
                                 annotation_text=f"BE: {be_price:,.0f}")

        fig_payoff.update_layout(
            template="plotly_dark", height=500,
            title=dict(text=f"{strategy_type} — Payoff at Expiry", font=dict(size=16, color="#f1f5f9")),
            xaxis_title="NIFTY at Expiry",
            yaxis_title=f"P&L (₹) — Lot Size: {NIFTY_LOT_SIZE}",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.5)",
            font=dict(color="#e2e8f0"),
        )
        _plotly_axis_style(fig_payoff)
        st.plotly_chart(fig_payoff, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Max Profit", f"₹{max_p:,.0f}")
        m2.metric("Max Loss", f"₹{max_l:,.0f}")
        rr = abs(max_p / max_l) if max_l != 0 else float("inf")
        m3.metric("Risk:Reward", f"{rr:.2f}x")
        m4.metric("Breakevens", f"{len(be_indices)}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: Monte Carlo Lab
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown("### Monte Carlo Simulation Engine")

    mc_col1, mc_col2 = st.columns([1, 2])

    with mc_col1:
        st.markdown("#### Simulation Parameters")
        mc_spot = st.number_input("Spot Price", value=float(spot_price), step=50.0, format="%.1f", key="mc_spot")
        mc_iv = st.slider("Volatility (%)", 8, 50, int(base_iv * 100), key="mc_iv") / 100
        mc_tte = st.slider("Days to Expiry", 1, 30, int(tte_days), key="mc_tte")
        mc_sims = int(st.select_slider("Simulations", options=[5000, 10000, 25000, 50000, 100000], value=int(n_sims), key="mc_sims"))

        mc_target = st.number_input("Target Price", value=float(spot_price) * 1.02, step=50.0, format="%.1f", key="mc_tgt")
        mc_lower = st.number_input("Range Lower", value=float(spot_price) * 0.97, step=50.0, format="%.1f", key="mc_lo")
        mc_upper = st.number_input("Range Upper", value=float(spot_price) * 1.03, step=50.0, format="%.1f", key="mc_hi")

    with mc_col2:
        terminals = simulate_terminal_prices(mc_spot, mc_iv, mc_tte / 365, mc_sims)

        pop_above = float((terminals >= mc_target).mean())
        pop_range = float(((terminals >= mc_lower) & (terminals <= mc_upper)).mean())
        bs_above = bs_pop_above(mc_spot, mc_target, mc_iv, mc_tte / 365)
        bs_range = bs_pop_between(mc_spot, mc_lower, mc_upper, mc_iv, mc_tte / 365)

        pm1, pm2, pm3, pm4 = st.columns(4)
        pm1.metric("MC P(above target)", f"{pop_above:.1%}")
        pm2.metric("BS P(above target)", f"{bs_above:.1%}")
        pm3.metric("MC P(in range)", f"{pop_range:.1%}")
        pm4.metric("BS P(in range)", f"{bs_range:.1%}")

        fig_mc = make_subplots(rows=1, cols=2, subplot_titles=("Terminal Price Distribution", "Probability Cone"))

        fig_mc.add_trace(go.Histogram(
            x=terminals, nbinsx=100,
            marker_color="#4ecdc4", opacity=0.7, name="Terminal Prices",
        ), row=1, col=1)
        fig_mc.add_vline(x=mc_spot, line_dash="dash", line_color="#fbbf24",
                         annotation_text="Spot", row=1, col=1)
        fig_mc.add_vline(x=mc_target, line_dash="dot", line_color="#00d4aa",
                         annotation_text="Target", row=1, col=1)
        fig_mc.add_vrect(x0=mc_lower, x1=mc_upper, fillcolor="rgba(167,139,250,0.15)",
                         line_width=0, row=1, col=1)

        days = np.arange(0, mc_tte + 1)
        rng = np.random.default_rng(42)
        n_paths = min(200, mc_sims)
        for i in range(n_paths):
            daily_returns = rng.normal(
                (RISK_FREE_RATE - 0.5 * mc_iv**2) / 365,
                mc_iv / np.sqrt(365),
                mc_tte,
            )
            path = mc_spot * np.exp(np.concatenate([[0], np.cumsum(daily_returns)]))
            fig_mc.add_trace(go.Scatter(
                x=days, y=path, mode="lines",
                line=dict(color="#4ecdc4", width=0.3), opacity=0.15,
                showlegend=False,
            ), row=1, col=2)

        mean_path = mc_spot * np.exp((RISK_FREE_RATE - 0.5 * mc_iv**2) / 365 * days)
        upper_1sd = mc_spot * np.exp(((RISK_FREE_RATE - 0.5 * mc_iv**2) / 365 + mc_iv / np.sqrt(365)) * days)
        lower_1sd = mc_spot * np.exp(((RISK_FREE_RATE - 0.5 * mc_iv**2) / 365 - mc_iv / np.sqrt(365)) * days)

        fig_mc.add_trace(go.Scatter(x=days, y=mean_path, name="Mean", line=dict(color="#fbbf24", width=2)), row=1, col=2)
        fig_mc.add_trace(go.Scatter(x=days, y=upper_1sd, name="+1σ", line=dict(color="#a78bfa", dash="dash")), row=1, col=2)
        fig_mc.add_trace(go.Scatter(x=days, y=lower_1sd, name="-1σ", line=dict(color="#a78bfa", dash="dash")), row=1, col=2)

        fig_mc.update_layout(
            template="plotly_dark", height=520,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,12,41,0.5)",
            showlegend=True,
            font=dict(color="#e2e8f0"),
            title_font=dict(color="#f1f5f9"),
            margin=dict(t=60, b=50),
        )
        _plotly_axis_style(fig_mc)
        st.plotly_chart(fig_mc, use_container_width=True)

        # Breakeven callout using Target Price as the reference level
        _be_pct = float((terminals >= mc_target).mean() * 100)
        _be_color = "#00d4aa" if _be_pct >= 55 else "#fbbf24" if _be_pct >= 40 else "#ff6b6b"
        _be_verdict = "favourable" if _be_pct >= 55 else "marginal" if _be_pct >= 40 else "unfavourable"
        st.markdown(
            f'<div style="background:rgba(78,205,196,0.07);border:1px solid rgba(78,205,196,0.2);'
            f'border-radius:10px;padding:0.8rem 1.2rem;margin:0.6rem 0;font-size:0.88rem">'
            f'📊 <strong style="color:{_be_color}">{_be_pct:.1f}%</strong> of {mc_sims:,} simulated paths expire '
            f'<strong>above ₹{mc_target:,.0f}</strong> (your target / breakeven) — '
            f'<span style="color:{_be_color};font-weight:600">{_be_verdict}</span>. '
            f'<span style="color:#8b8fa3;font-size:0.8rem">Adjust target price or IV to explore different scenarios.</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### Distribution Statistics")
        stat_cols = st.columns(6)
        stat_cols[0].metric("Mean", f"₹{np.mean(terminals):,.0f}")
        stat_cols[1].metric("Median", f"₹{np.median(terminals):,.0f}")
        stat_cols[2].metric("Std Dev", f"₹{np.std(terminals):,.0f}")
        stat_cols[3].metric("5th %ile", f"₹{np.percentile(terminals, 5):,.0f}")
        stat_cols[4].metric("95th %ile", f"₹{np.percentile(terminals, 95):,.0f}")
        stat_cols[5].metric("Skewness", f"{pd.Series(terminals).skew():.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: Backtest Results
# ═══════════════════════════════════════════════════════════════════════════════

with tab5:
    st.markdown("### 52-Week Backtest Performance")

    metrics_data = compute_metrics(backtest_df)
    eq_df = equity_curve(backtest_df, capital)

    bm1, bm2, bm3, bm4, bm5, bm6 = st.columns(6)
    bm1.metric("Total P&L", f"₹{metrics_data['total_pnl']:,.0f}",
               delta=f"{metrics_data['total_pnl']/capital*100:+.1f}%")
    bm2.metric("Win Rate", f"{metrics_data['win_rate']:.1%}")
    bm3.metric("Sharpe Ratio", f"{metrics_data['sharpe_ratio']:.2f}")
    bm4.metric("Profit Factor", f"{metrics_data['profit_factor']:.2f}")
    bm5.metric("Max Drawdown", f"₹{metrics_data['max_drawdown']:,.0f}")
    bm6.metric("Avg R:R", f"{metrics_data['avg_rr']:.2f}x")

    bt_col1, bt_col2 = st.columns(2)

    with bt_col1:
        # Build a Buy & Hold NIFTY benchmark aligned to the backtest period
        _n_weeks = len(eq_df)
        _bh_history = history_df.tail(_n_weeks).copy().reset_index(drop=True)
        if len(_bh_history) >= 2:
            _bh_returns = _bh_history["close"].pct_change().fillna(0)
            _bh_equity = capital * (1 + _bh_returns).cumprod()
        else:
            _bh_equity = pd.Series([capital] * _n_weeks)

        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=eq_df["expiry"], y=eq_df["equity"],
            fill="tozeroy", fillcolor="rgba(0,212,170,0.1)",
            line=dict(color="#00d4aa", width=2), name="Options Strategy",
        ))
        fig_eq.add_trace(go.Scatter(
            x=eq_df["expiry"], y=eq_df["peak_equity"],
            line=dict(color="#fbbf24", width=1, dash="dash"), name="Peak Equity",
        ))
        fig_eq.add_trace(go.Scatter(
            x=eq_df["expiry"], y=_bh_equity.values[:len(eq_df)],
            line=dict(color="#9ca3af", width=1.5, dash="dot"),
            name="Buy & Hold NIFTY",
            opacity=0.75,
        ))
        fig_eq.add_hline(y=capital, line_dash="dot", line_color="rgba(255,255,255,0.3)")
        fig_eq.update_layout(
            template="plotly_dark", height=400,
            title="Equity Curve vs Buy & Hold NIFTY",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,12,41,0.5)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
        )
        st.plotly_chart(fig_eq, use_container_width=True)

    with bt_col2:
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=eq_df["expiry"], y=eq_df["drawdown"],
            fill="tozeroy", fillcolor="rgba(255,107,107,0.2)",
            line=dict(color="#ff6b6b", width=2), name="Drawdown",
        ))
        fig_dd.update_layout(
            template="plotly_dark", height=400,
            title="Drawdown", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,12,41,0.5)",
        )
        st.plotly_chart(fig_dd, use_container_width=True)

    bt_col3, bt_col4 = st.columns(2)

    with bt_col3:
        pnl_colors = ["#00d4aa" if p > 0 else "#ff6b6b" for p in backtest_df["pnl"]]
        fig_pnl = go.Figure(go.Bar(
            x=backtest_df["expiry"], y=backtest_df["pnl"],
            marker_color=pnl_colors, opacity=0.8,
        ))
        fig_pnl.update_layout(
            template="plotly_dark", height=350,
            title="Weekly P&L", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,12,41,0.5)",
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

    with bt_col4:
        strat_perf = backtest_df.groupby("strategy").agg(
            total_pnl=("pnl", "sum"),
            trades=("pnl", "count"),
            win_rate=("won", "mean"),
            avg_pnl=("pnl", "mean"),
        ).round(2)

        fig_strat = go.Figure(go.Bar(
            x=strat_perf.index, y=strat_perf["total_pnl"],
            marker_color=["#00d4aa" if p > 0 else "#ff6b6b" for p in strat_perf["total_pnl"]],
            text=[f"₹{p:,.0f}" for p in strat_perf["total_pnl"]],
            textposition="outside",
        ))
        fig_strat.update_layout(
            template="plotly_dark", height=350,
            title="P&L by Strategy", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,12,41,0.5)",
        )
        st.plotly_chart(fig_strat, use_container_width=True)

    st.markdown("### Detailed Trade Log")
    st.caption("POP = Probability of Profit (% chance the trade was expected to win at entry, from Monte Carlo simulation). Latest trades shown first.")
    display_bt = backtest_df.copy().sort_values("expiry", ascending=False).reset_index(drop=True)
    display_bt["pnl_formatted"] = display_bt["pnl"].apply(lambda x: f"₹{x:,.0f}")
    display_bt["won_icon"] = display_bt["won"].apply(lambda x: "✅" if x else "❌")
    display_bt = display_bt.rename(columns={"pop": "POP (win prob %)", "risk_reward": "R:R"})
    display_bt["POP (win prob %)"] = (display_bt["POP (win prob %)"] * 100).round(0).astype(int).astype(str) + "%"
    st.dataframe(
        display_bt[["expiry", "strategy", "market_condition", "pnl_formatted", "won_icon", "POP (win prob %)", "R:R"]],
        height=400, use_container_width=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6: Trade Signals
# ═══════════════════════════════════════════════════════════════════════════════

with tab6:
    st.markdown("### Live Trade Signal Generator")
    st.markdown(f'Current market condition: <span class="condition-badge badge-{market_condition}">{market_condition}</span>', unsafe_allow_html=True)

    # ── Strategy selection rationale: if-then logic ───────────────────────────
    _rsi_now = float(latest["rsi_14"])
    _sma20_now = float(latest["sma_20"])
    _sma50_now = float(latest["sma_50"])
    _spot_vs_sma20_pct = abs(latest_close - _sma20_now) / _sma20_now * 100

    _regime_why = {
        "bullish": f"RSI = {_rsi_now:.0f} (&gt;60) and spot is above both SMA20 (₹{_sma20_now:,.0f}) and SMA50 (₹{_sma50_now:,.0f}).",
        "bearish": f"RSI = {_rsi_now:.0f} (&lt;40) and spot is below both SMA20 (₹{_sma20_now:,.0f}) and SMA50 (₹{_sma50_now:,.0f}).",
        "high_volatility": f"IV ({base_iv*100:.0f}%) is &gt;25% above the 20-period average — elevated fear premium.",
        "sideways": f"RSI = {_rsi_now:.0f} (between 40–60) and spot is within {_spot_vs_sma20_pct:.1f}% of SMA20 (₹{_sma20_now:,.0f}).",
    }
    _switch_hints = {
        "bullish": "If RSI falls below 40 → switch to <strong>Bear Put Spread</strong>. If RSI stays 40–60 → switch to <strong>Short Strangle</strong>.",
        "bearish": "If RSI rises above 60 → switch to <strong>Bull Call Spread</strong>. If RSI stays 40–60 → switch to <strong>Short Strangle</strong>.",
        "sideways": "If RSI breaks above 60 → switch to <strong>Bull Call Spread</strong>. If RSI breaks below 40 → switch to <strong>Bear Put Spread</strong>.",
        "high_volatility": "If IV normalises below the 20-period average → switch to <strong>Short Strangle</strong>.",
    }
    _strat_name_map = {"bullish": "Bull Call Spread", "bearish": "Bear Put Spread", "sideways": "Short Strangle", "high_volatility": "Long Strangle"}
    _cur_strat_name = _strat_name_map.get(market_condition, "—")

    st.markdown(
        f'<div style="background:rgba(78,205,196,0.08);border:1px solid rgba(78,205,196,0.2);'
        f'border-radius:10px;padding:0.9rem 1.2rem;margin:0.8rem 0 1.2rem 0;font-size:0.85rem;line-height:1.7">'
        f'<span style="color:#4ecdc4;font-weight:700">Why {_cur_strat_name}?</span><br>'
        f'<span style="color:#cbd5e1">{_regime_why.get(market_condition, "")}</span><br>'
        f'<span style="color:#8b8fa3;font-size:0.8rem">Switch signal: {_switch_hints.get(market_condition, "")}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    selector = StrikeSelector(enriched_chain, spot_price)
    prob_model = POPEstimator(spot_price, base_iv, tte_days / 365)

    strategy_map = {
        "bullish": [("Bull Call Spread", selector.get_bull_call_combos)],
        "bearish": [("Bear Put Spread", selector.get_bear_put_combos)],
        "sideways": [("Short Strangle", selector.get_short_strangle_combos)],
        "high_volatility": [("Long Strangle", selector.get_long_strangle_combos)],
    }

    recommended = strategy_map.get(market_condition, [])

    if not recommended:
        st.info("No strategies mapped for the current market condition. Showing all strategies.")
        recommended = [
            ("Bull Call Spread", selector.get_bull_call_combos),
            ("Bear Put Spread", selector.get_bear_put_combos),
        ]

    for strat_name, combo_fn in recommended:
        st.markdown(f"#### {strat_name}")
        combos = combo_fn()

        if not combos:
            st.warning(f"No valid combos found for {strat_name}")
            continue

        for combo in combos[:5]:
            strategy_type_key = combo.strategy if hasattr(combo, "strategy") else "bull_call_spread"
            try:
                stats = prob_model.evaluate(combo, strategy_type_key)
            except Exception:
                stats = {"pop": 0.5, "risk_reward": 1.5, "expected_payoff": 0, "max_profit": 0, "max_loss": 0}

            if stats["pop"] < min_pop or stats["risk_reward"] < min_rr:
                continue

            if stats["pop"] > 0.60 and stats["risk_reward"] > 2.0:
                confidence = "high"
            elif stats["pop"] > 0.50 and stats["risk_reward"] > 1.5:
                confidence = "medium"
            else:
                confidence = "low"

            conf_color = {"high": "#00d4aa", "medium": "#fbbf24", "low": "#ff6b6b"}[confidence]

            _iv_desc = "moderate" if base_iv < 0.18 else "elevated" if base_iv > 0.25 else "normal"
            _combo_rationale = (
                f"IV at {base_iv*100:.0f}% ({_iv_desc}) · {strat_name} fits {market_condition} regime "
                f"(RSI={_rsi_now:.0f}) · Max loss capped at ₹{abs(combo.max_loss):,.0f}"
            )
            st.markdown(f"""
            <div class="signal-card signal-{confidence}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem">
                    <div>
                        <span style="color:#e2e8f0;font-weight:600;font-size:1.05rem">{combo.label}</span>
                        <span style="color:{conf_color};font-size:0.8rem;margin-left:0.8rem;text-transform:uppercase;font-weight:600">
                            {confidence} confidence
                        </span>
                    </div>
                    <span style="color:#a78bfa;font-size:0.85rem">R:R {stats['risk_reward']:.1f}x</span>
                </div>
                <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1rem;font-size:0.85rem">
                    <div><span style="color:#6b7280">Buy Strike</span><br><span style="color:#e2e8f0;font-weight:600">₹{combo.buy_strike:,.0f}</span></div>
                    <div><span style="color:#6b7280">Sell Strike</span><br><span style="color:#e2e8f0;font-weight:600">₹{combo.sell_strike:,.0f}</span></div>
                    <div><span style="color:#6b7280">Net Premium</span><br><span style="color:#e2e8f0;font-weight:600">₹{combo.net_premium:,.1f}</span></div>
                    <div><span style="color:#6b7280">POP</span><br><span style="color:#00d4aa;font-weight:600">{stats['pop']:.1%}</span></div>
                    <div><span style="color:#6b7280">Expected P&L</span><br><span style="color:{'#00d4aa' if stats['expected_payoff'] > 0 else '#ff6b6b'};font-weight:600">₹{stats['expected_payoff']:,.0f}</span></div>
                </div>
                <div style="color:#6b7280;font-size:0.78rem;margin-top:0.6rem;font-style:italic;border-top:1px solid rgba(255,255,255,0.05);padding-top:0.5rem">
                    {_combo_rationale}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Entry/Exit timing guide ───────────────────────────────────────────────
    with st.expander("⏰ Timing Guide — When to enter & exit this week's position"):
        st.markdown("""
**Entry: Best after 2:00 PM**

IV often peaks mid-session and softens toward close as market makers adjust positions.
Entering after 2 PM gives you the benefit of:
- Lower IV → cheaper premium for buyers, tighter spreads for sellers
- Cleaner directional read after the morning noise settles
- Roughly 5–7 minutes of pre-close time to adjust if needed

---

**Exit options — choose based on your risk appetite:**
""")
        eg1, eg2, eg3 = st.columns(3)
        with eg1:
            st.markdown(
                '<div style="background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.25);'
                'border-radius:10px;padding:0.9rem;text-align:center">'
                '<div style="color:#00d4aa;font-weight:700;font-size:0.9rem">50% Profit Target</div>'
                '<div style="color:#cbd5e1;font-size:0.82rem;margin-top:0.5rem">Exit when position hits half of max profit. '
                'Captures most theta decay while cutting gamma risk.</div>'
                '<div style="color:#6b7280;font-size:0.75rem;margin-top:0.6rem;font-style:italic">Best for: Short Strangle, Iron Condor</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with eg2:
            st.markdown(
                '<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);'
                'border-radius:10px;padding:0.9rem;text-align:center">'
                '<div style="color:#fbbf24;font-weight:700;font-size:0.9rem">Day 3 Exit (Tue close)</div>'
                '<div style="color:#cbd5e1;font-size:0.82rem;margin-top:0.5rem">If entered Monday, exit Tuesday close. '
                'Avoids Wednesday–Thursday gamma acceleration and expiry-day spikes.</div>'
                '<div style="color:#6b7280;font-size:0.75rem;margin-top:0.6rem;font-style:italic">Best for: Directional spreads</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with eg3:
            st.markdown(
                '<div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.25);'
                'border-radius:10px;padding:0.9rem;text-align:center">'
                '<div style="color:#a78bfa;font-weight:700;font-size:0.9rem">Thu 9:30 AM (pre-expiry)</div>'
                '<div style="color:#cbd5e1;font-size:0.82rem;margin-top:0.5rem">Exit 30 minutes before expiry close '
                '(≈9:30 AM). Avoids final-hour pin risk and settlement gaps.</div>'
                '<div style="color:#6b7280;font-size:0.75rem;margin-top:0.6rem;font-style:italic">Best for: Any weekly position</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### All Strategy Combos")

    all_combos = []
    for fn_name, fn in [
        ("Bull Call", selector.get_bull_call_combos),
        ("Bear Put", selector.get_bear_put_combos),
        ("Short Strangle", selector.get_short_strangle_combos),
        ("Long Strangle", selector.get_long_strangle_combos),
    ]:
        for combo in fn():
            all_combos.append({
                "Strategy": fn_name,
                "Label": combo.label,
                "Buy Strike": combo.buy_strike,
                "Sell Strike": combo.sell_strike,
                "Net Premium": combo.net_premium,
                "Max Profit": combo.max_profit,
                "Max Loss": combo.max_loss,
                "Breakeven": combo.breakeven,
            })

    if all_combos:
        st.dataframe(pd.DataFrame(all_combos), use_container_width=True)


# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#4b5563;font-size:0.8rem;padding:1rem">'
    'NIFTY Weekly Options Quantitative Trading Model &bull; '
    'Built with Streamlit, Plotly & Python &bull; '
    'Data is simulated for demonstration purposes'
    '</div>',
    unsafe_allow_html=True,
)
