"""Dark / light theme for Streamlit + Plotly."""

import streamlit as st

THEME_KEY = "ui_theme"


def plotly_axis_style(fig):
    """Match grid/tick colors to current light/dark theme."""
    init_theme()
    t = st.session_state.get(THEME_KEY, "dark")
    if t == "light":
        fig.update_xaxes(
            gridcolor="rgba(15,23,42,0.12)", zerolinecolor="rgba(15,23,42,0.25)",
            tickfont=dict(color="#475569"), title_font=dict(color="#334155"),
        )
        fig.update_yaxes(
            gridcolor="rgba(15,23,42,0.12)", zerolinecolor="rgba(15,23,42,0.25)",
            tickfont=dict(color="#475569"), title_font=dict(color="#334155"),
        )
    else:
        fig.update_xaxes(
            gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.2)",
            tickfont=dict(color="#cbd5e1"), title_font=dict(color="#e2e8f0"),
        )
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.2)",
            tickfont=dict(color="#cbd5e1"), title_font=dict(color="#e2e8f0"),
        )


def init_theme():
    if THEME_KEY not in st.session_state:
        st.session_state[THEME_KEY] = "dark"


def theme_choice_sidebar():
    """Sidebar control; returns 'dark' | 'light'."""
    init_theme()
    opts = ["Dark", "Light"]
    idx = 0 if st.session_state[THEME_KEY] == "dark" else 1
    choice = st.radio(
        "Appearance",
        opts,
        index=idx,
        horizontal=True,
        help="Light theme uses high-contrast text for daytime use.",
    )
    st.session_state[THEME_KEY] = "dark" if choice == "Dark" else "light"
    return st.session_state[THEME_KEY]


def plotly_template() -> str:
    init_theme()
    return "plotly_dark" if st.session_state.get(THEME_KEY, "dark") == "dark" else "plotly_white"


def inject_global_css(theme: str):
    """Inject theme-dependent styles after base Streamlit render."""
    if theme == "light":
        st.markdown(
            """
<style>
    .stApp {
        font-family: 'Inter', system-ui, sans-serif;
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        color: #0f172a !important;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #1d4ed8 100%) !important;
        box-shadow: 0 4px 24px rgba(37, 99, 235, 0.25);
    }
    .main-header h1 { color: #ffffff !important; }
    .main-header p { color: #e0e7ff !important; }
    .metric-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .metric-card .label { color: #64748b !important; }
    .metric-card .sub { color: #94a3b8 !important; }
    .strategy-card-lite {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    div[data-testid="stSidebar"] label { color: #334155 !important; }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] p { color: #475569 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #0f172a !important; }
    div[data-testid="stNumberInput"] input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }
    @media (max-width: 900px) {
        .main-header { padding: 1rem 1.2rem !important; }
        .main-header h1 { font-size: 1.35rem !important; }
        .stTabs [data-baseweb="tab"] { padding: 6px 10px !important; font-size: 0.82rem !important; }
    }
</style>
""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
<style>
    .stApp { font-family: 'Inter', system-ui, sans-serif; }
    .strategy-card-lite { /* dark mode uses existing classes */ }
    @media (max-width: 900px) {
        .main-header { padding: 1rem 1.2rem !important; }
        .main-header h1 { font-size: 1.35rem !important; }
        .stTabs [data-baseweb="tab"] { padding: 6px 10px !important; font-size: 0.82rem !important; }
    }
</style>
""",
            unsafe_allow_html=True,
        )
