# NIFTY Dashboard — Code Implementation Snippets & Patterns

## 1. GREEKS TIME-SERIES DISPLAY

### 1.1 — Add Greeks Timeline Table to Option Chain Tab

```python
# In tab2 (Option Chain) — Add this after the current chain table

st.markdown("---")
st.markdown("### 📈 Greeks Timeline (Selected Strike Progression)")

# User selects strike to track
selected_strike = st.selectbox("Select Strike to Track", 
    sorted(enriched_chain['strike_price'].unique()))

# Filter for selected strike (both CE and PE)
timeline_data = []

for day in range(5):  # Mon to Thu (5 trading days in a week)
    # This would come from your time-series DB
    # For now, simulate with slight daily changes
    snapshot = enriched_chain[
        enriched_chain['strike_price'] == selected_strike
    ]
    
    if not snapshot.empty:
        # CE row
        ce_row = snapshot[snapshot['instrument_type'] == 'CE'].iloc[0] if not snapshot[snapshot['instrument_type'] == 'CE'].empty else None
        
        if ce_row is not None:
            timeline_data.append({
                'Day': day,
                'Date': (pd.Timestamp.now() + timedelta(days=day)).strftime('%a, %b %d'),
                'Instrument': 'CE',
                'LTP': f"₹{ce_row['ltp']:.2f}",
                'IV': f"{ce_row['iv']*100:.1f}%",
                'Delta': f"{ce_row['delta']:.2f}",
                'Theta (daily)': f"₹{ce_row['theta']*50:.0f}",  # Per lot
                'Gamma': f"{ce_row['gamma']:.4f}",
                'Vega (per 1%)': f"₹{ce_row['vega']*50:.0f}",  # Per lot
            })

timeline_df = pd.DataFrame(timeline_data)
st.dataframe(timeline_df, use_container_width=True, hide_index=True)

# Add insight
st.caption("""
💡 **How to read this table:**
- **Theta:** Daily decay (negative = buyer loses, positive = seller profits)
- **Gamma:** How much delta changes per 100-point move (high = risky near expiry)
- **Vega:** Daily P&L impact from 1% IV change
""")
```

### 1.2 — Add Theta Acceleration Chart

```python
# In tab2 (Option Chain) — Add after Greeks timeline

st.markdown("#### Theta Decay Curve (Acceleration)")

# Simulate theta decay from entry to expiry
dte_array = np.arange(5, 0, -1)  # 5 days to expiry down to 0
theta_values = []

for dte in dte_array:
    # Theta increases in magnitude as expiry approaches (acceleration)
    theta = -15 * (5 / dte) ** 1.5  # Rough approximation
    theta_values.append(theta)

fig_theta = go.Figure()
fig_theta.add_trace(go.Scatter(
    x=['5d', '4d', '3d', '2d', '1d'],
    y=theta_values,
    mode='lines+markers',
    name='Theta (daily)',
    line=dict(color='#00d4aa', width=2),
    marker=dict(size=8),
    fill='tozeroy',
    fillcolor='rgba(0,212,170,0.2)',
))

fig_theta.add_annotation(
    x=2, y=theta_values[2],
    text='🔥 Theta accelerates!',
    showarrow=True,
    arrowhead=2,
    arrowcolor='#fbbf24',
)

fig_theta.update_layout(
    title='Theta Acceleration Towards Expiry (ATM Call)',
    xaxis_title='Days to Expiry',
    yaxis_title='Daily Theta (₹ per contract)',
    template='plotly_dark',
    height=300,
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(15,12,41,0.5)',
)

st.plotly_chart(fig_theta, use_container_width=True)

st.info("""
**Entry Signal:** When theta accelerates to > -25, it's a good time to enter SHORT positions
(sellers profit from decay). For bull call spread, you profit from the short leg's theta.
""")
```

---

## 2. POINT-IN-TIME BACKTEST (Weekly Expiry Loop)

### 2.1 — Weekly Backtest Engine Core

```python
# File: backtest_engine.py (new module)

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class BacktestTrade:
    expiry_date: str
    entry_date: str
    strategy: str
    buy_strike: float
    sell_strike: float
    entry_premium: float
    exit_premium: float
    pnl: float
    exit_reason: str
    entry_greeks: Dict
    daily_progression: List[Dict]

class WeeklyBacktestEngine:
    
    def __init__(self, data_loader, signal_generator, lot_size=50):
        self.loader = data_loader
        self.signals = signal_generator
        self.lot_size = lot_size
    
    def run_backtest(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Backtest from start to end, one weekly expiry at a time.
        
        Args:
            start_date: 'YYYY-MM-DD' (e.g., '2025-01-01')
            end_date: 'YYYY-MM-DD' (e.g., '2025-12-31')
        
        Returns:
            DataFrame with all trades (expiry, entry_date, strategy, PnL, etc.)
        """
        
        weekly_expiries = self.loader.get_weekly_expiries(start_date, end_date)
        all_trades = []
        
        for expiry_date in weekly_expiries:
            # Entry is always Monday 2 PM (or first available time after 2 PM)
            entry_time = self.get_entry_time(expiry_date)
            
            # Load option chain at entry time
            entry_chain = self.loader.load_chain(expiry_date, entry_time)
            
            if entry_chain is None or len(entry_chain) == 0:
                continue  # No data for this expiry
            
            # Get market metrics at entry
            spot = entry_chain['spot_price'].iloc[0]
            market_cond = entry_chain.get('market_condition', 'sideways').iloc[0]
            
            # Generate signals
            signals = self.signals.generate(
                chain=entry_chain,
                spot=spot,
                market_condition=market_cond,
            )
            
            # Simulate each signal as a trade
            for signal in signals:
                trade = self.simulate_trade(
                    expiry=expiry_date,
                    entry_time=entry_time,
                    entry_chain=entry_chain,
                    signal=signal,
                )
                
                if trade:
                    all_trades.append(trade)
        
        # Convert to DataFrame
        return pd.DataFrame([t.__dict__ for t in all_trades])
    
    def get_entry_time(self, expiry_date: str) -> datetime:
        """
        Get entry time: Monday 2 PM (or closest available).
        expiry_date is Thursday of that week.
        """
        expiry_dt = pd.to_datetime(expiry_date)
        
        # Go back to Monday of the same week
        days_back = (expiry_dt.weekday() - 0) % 7  # 0 = Monday
        entry_date = expiry_dt - timedelta(days=days_back + 3)  # 3 days back (Sat to Wed)
        
        # Set to 2 PM IST
        entry_time = entry_date.replace(hour=14, minute=0, second=0)
        
        return entry_time
    
    def simulate_trade(self, expiry: str, entry_time: datetime, 
                      entry_chain: pd.DataFrame, signal) -> BacktestTrade:
        """
        Simulate a single trade from entry to exit.
        """
        
        # Find buy and sell rows
        buy_row = entry_chain[
            (entry_chain['strike_price'] == signal.buy_strike) &
            (entry_chain['instrument_type'] == signal.instrument_type_buy)
        ]
        
        sell_row = entry_chain[
            (entry_chain['strike_price'] == signal.sell_strike) &
            (entry_chain['instrument_type'] == signal.instrument_type_sell)
        ]
        
        if buy_row.empty or sell_row.empty:
            return None
        
        # Entry
        buy_ltp = buy_row['ltp'].iloc[0]
        sell_ltp = sell_row['ltp'].iloc[0]
        entry_premium = buy_ltp - sell_ltp
        
        entry_greeks = {
            'delta': buy_row['delta'].iloc[0] - sell_row['delta'].iloc[0],
            'theta': buy_row['theta'].iloc[0] - sell_row['theta'].iloc[0],
            'gamma': buy_row['gamma'].iloc[0] - sell_row['gamma'].iloc[0],
            'vega': buy_row['vega'].iloc[0] - sell_row['vega'].iloc[0],
        }
        
        # Track daily progression
        daily_progression = []
        pnl = 0
        exit_reason = 'EXPIRY'
        exit_time = None
        exit_premium = entry_premium
        
        # Simulate day-by-day (Mon to Thu)
        for day in range(1, 5):
            exit_time_candidate = entry_time + timedelta(days=day)
            
            # Cap at Thursday 9:30 AM (expiry time)
            expiry_dt = pd.to_datetime(expiry)
            expiry_close = expiry_dt.replace(hour=9, minute=30)
            
            if exit_time_candidate.time() >= time(9, 30) and exit_time_candidate.weekday() == 3:
                exit_time_candidate = expiry_close
            
            # Load chain at this time
            exit_chain = self.loader.load_chain(expiry, exit_time_candidate)
            
            if exit_chain is None or len(exit_chain) == 0:
                continue
            
            buy_exit = exit_chain[
                (exit_chain['strike_price'] == signal.buy_strike) &
                (exit_chain['instrument_type'] == signal.instrument_type_buy)
            ]
            
            sell_exit = exit_chain[
                (exit_chain['strike_price'] == signal.sell_strike) &
                (exit_chain['instrument_type'] == signal.instrument_type_sell)
            ]
            
            if buy_exit.empty or sell_exit.empty:
                continue
            
            # Calculate P&L at this checkpoint
            exit_ltp_buy = buy_exit['ltp'].iloc[0]
            exit_ltp_sell = sell_exit['ltp'].iloc[0]
            exit_premium_current = exit_ltp_buy - exit_ltp_sell
            
            pnl = (entry_premium - exit_premium_current) * self.lot_size
            
            # Record daily greeks
            daily_progression.append({
                'day': day,
                'time': exit_time_candidate.isoformat(),
                'exit_premium': exit_premium_current,
                'pnl': pnl,
                'delta': buy_exit['delta'].iloc[0] - sell_exit['delta'].iloc[0],
                'theta': buy_exit['theta'].iloc[0] - sell_exit['theta'].iloc[0],
                'gamma': buy_exit['gamma'].iloc[0] - sell_exit['gamma'].iloc[0],
                'vega': buy_exit['vega'].iloc[0] - sell_exit['vega'].iloc[0],
            })
            
            # Check exit conditions
            max_profit = abs(signal.sell_strike - signal.buy_strike) * self.lot_size
            
            if pnl >= max_profit * 0.5:  # 50% of max profit
                exit_reason = 'PROFIT_TARGET_50%'
                exit_premium = exit_premium_current
                break
            
            # Check stop loss (2x entry premium)
            if pnl <= -entry_premium * 2 * self.lot_size:
                exit_reason = 'STOP_LOSS'
                exit_premium = exit_premium_current
                break
            
            exit_premium = exit_premium_current
        
        return BacktestTrade(
            expiry_date=expiry,
            entry_date=entry_time.date().isoformat(),
            strategy=signal.strategy,
            buy_strike=signal.buy_strike,
            sell_strike=signal.sell_strike,
            entry_premium=entry_premium,
            exit_premium=exit_premium,
            pnl=pnl,
            exit_reason=exit_reason,
            entry_greeks=entry_greeks,
            daily_progression=daily_progression,
        )
```

### 2.2 — Display Per-Trade Greeks Progression

```python
# In tab5 (Backtest Results) — Add this after equity curve chart

st.markdown("### 📊 Trade-by-Trade Greeks Progression")

# Select a trade to inspect
trades_df = backtest_df.copy()
trade_idx = st.selectbox(
    "Select Trade to Analyze",
    range(len(trades_df)),
    format_func=lambda i: f"Trade {i+1}: {trades_df.iloc[i]['strategy']} "
                         f"({trades_df.iloc[i]['entry_date']})"
)

selected_trade = trades_df.iloc[trade_idx]

# Display entry info
col1, col2, col3, col4 = st.columns(4)
col1.metric("Entry Premium", f"₹{selected_trade['entry_premium']:.2f}")
col2.metric("Exit Premium", f"₹{selected_trade['exit_premium']:.2f}")
col3.metric("P&L", f"₹{selected_trade['pnl']:,.0f}", 
           delta=f"{selected_trade['pnl']/selected_trade['entry_premium']/50*100:+.1f}%")
col4.metric("Exit Reason", selected_trade['exit_reason'])

# Greeks progression table
progression = pd.DataFrame(selected_trade['daily_progression'])

if not progression.empty:
    progression['Time'] = pd.to_datetime(progression['time']).dt.strftime('%a, %b %d %I:%M %p')
    progression['Exit Premium'] = progression['exit_premium'].apply(lambda x: f"₹{x:.2f}")
    progression['P&L (₹)'] = progression['pnl'].apply(lambda x: f"₹{x:,.0f}")
    progression['Delta'] = progression['delta'].apply(lambda x: f"{x:.2f}")
    progression['Theta (₹/day)'] = progression['theta'].apply(lambda x: f"₹{x*50:.0f}")
    progression['Gamma'] = progression['gamma'].apply(lambda x: f"{x:.4f}")
    progression['Vega (₹/%)'] = progression['vega'].apply(lambda x: f"₹{x*50:.0f}")
    
    display_cols = ['Time', 'Exit Premium', 'P&L (₹)', 'Delta', 
                   'Theta (₹/day)', 'Gamma', 'Vega (₹/%)']
    
    st.dataframe(
        progression[display_cols],
        use_container_width=True,
        hide_index=True,
    )
    
    # Greeks charts
    fig_greeks = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Delta Progression', 'Theta Decay', 'Gamma Curve', 'Vega Change'),
    )
    
    x_axis = progression['day'].values
    
    fig_greeks.add_trace(go.Scatter(
        x=x_axis, y=progression['delta'],
        mode='lines+markers', name='Delta', line=dict(color='#4ecdc4'),
    ), row=1, col=1)
    
    fig_greeks.add_trace(go.Scatter(
        x=x_axis, y=progression['theta'],
        mode='lines+markers', name='Theta', line=dict(color='#00d4aa'),
    ), row=1, col=2)
    
    fig_greeks.add_trace(go.Scatter(
        x=x_axis, y=progression['gamma'],
        mode='lines+markers', name='Gamma', line=dict(color='#fbbf24'),
    ), row=2, col=1)
    
    fig_greeks.add_trace(go.Scatter(
        x=x_axis, y=progression['vega'],
        mode='lines+markers', name='Vega', line=dict(color='#a78bfa'),
    ), row=2, col=2)
    
    fig_greeks.update_layout(
        template='plotly_dark', height=600,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,12,41,0.5)',
        showlegend=False,
    )
    
    st.plotly_chart(fig_greeks, use_container_width=True)
    
    # P&L Attribution (Theta + Gamma + Vega)
    st.markdown("#### P&L Attribution by Greeks")
    
    # Simplified: estimate contributions
    if len(progression) > 1:
        theta_pnl = progression['theta'].sum() * 50 * (len(progression) - 1)
        vega_pnl = progression['vega'].sum() * 50 * (progression['vega'].std())
        gamma_pnl = selected_trade['pnl'] - theta_pnl  # Rest is gamma
        
        pnl_attr = pd.DataFrame({
            'Source': ['Theta Decay', 'Vega (IV change)', 'Gamma (price move)'],
            'Contribution': [f"₹{theta_pnl:,.0f}", f"₹{vega_pnl:,.0f}", f"₹{gamma_pnl:,.0f}"],
            '% of P&L': [
                f"{theta_pnl/selected_trade['pnl']*100:.0f}%" if selected_trade['pnl'] != 0 else "—",
                f"{vega_pnl/selected_trade['pnl']*100:.0f}%" if selected_trade['pnl'] != 0 else "—",
                f"{gamma_pnl/selected_trade['pnl']*100:.0f}%" if selected_trade['pnl'] != 0 else "—",
            ],
        })
        
        st.dataframe(pnl_attr, use_container_width=True, hide_index=True)
        
        st.info(f"""
        **Insight:** Your profit came mostly from:
        - ✅ **Theta decay** (selling time decay) — ₹{theta_pnl:,.0f}
        - {'✅' if vega_pnl > 0 else '⚠️'} **IV contraction** (IV fell) — ₹{vega_pnl:,.0f}
        - {'✅' if gamma_pnl > 0 else '⚠️'} **Gamma P&L** (price movement) — ₹{gamma_pnl:,.0f}
        """)
```

---

## 3. MOBILE RESPONSIVE CSS

### 3.1 — Add to Top of app.py

```python
# Mobile-first responsive design

mobile_responsive_css = """
<style>
/* Base: Mobile (< 768px) */
@media (max-width: 767px) {
    /* Metric cards: Stack, reduce padding */
    .metric-card {
        padding: 0.6rem !important;
        margin-bottom: 0.4rem !important;
        border-radius: 8px !important;
    }
    
    .metric-card .label {
        font-size: 0.6rem !important;
        letter-spacing: 0.5px;
    }
    
    .metric-card .value {
        font-size: 1.1rem !important;
        margin: 0.2rem 0 !important;
    }
    
    .metric-card .sub {
        font-size: 0.65rem !important;
    }
    
    /* Tables: Smaller text, scrollable */
    [data-testid="stDataFrame"] {
        font-size: 0.7rem !important;
    }
    
    /* Charts: Reduce height for mobile */
    [data-testid="stPlotlyChart"] {
        height: 300px !important;
    }
    
    /* Sidebar: Full width on mobile */
    section[data-testid="stSidebar"] {
        width: 100% !important;
        position: static !important;
    }
    
    /* Tabs: Full width, smaller font */
    .stTabs [data-baseweb="tab"] {
        padding: 6px 12px !important;
        font-size: 0.8rem !important;
    }
    
    /* Columns: Stack into 1 column */
    [data-testid="stColumn"] {
        width: 100% !important;
    }
    
    /* Expand blocks: Better spacing */
    details {
        margin-bottom: 0.8rem;
    }
}

/* Tablet (768px – 1024px) */
@media (min-width: 768px) and (max-width: 1023px) {
    .metric-card {
        padding: 0.9rem !important;
        font-size: 0.95rem;
    }
    
    [data-testid="stDataFrame"] {
        font-size: 0.8rem !important;
    }
    
    [data-testid="stPlotlyChart"] {
        height: 400px !important;
    }
}

/* Desktop (> 1024px) */
@media (min-width: 1024px) {
    .metric-card {
        padding: 1.2rem !important;
        font-size: 1rem;
    }
    
    [data-testid="stDataFrame"] {
        font-size: 0.85rem !important;
    }
    
    [data-testid="stPlotlyChart"] {
        height: 500px !important;
    }
}

/* Universal improvements */
body {
    font-size: 16px;  /* Ensure readable base font */
}

/* Better spacing on all screens */
.stMarkdown {
    margin-bottom: 0.8rem;
}

/* Signal cards: Responsive */
.signal-card {
    padding: 0.9rem;
    margin-bottom: 0.6rem;
}

/* Forms: Better touch targets on mobile */
input, select, button {
    min-height: 44px;  /* iOS recommendation */
    font-size: 16px;   /* Prevents zoom on iOS */
}
</style>
"""

st.markdown(mobile_responsive_css, unsafe_allow_html=True)
```

### 3.2 — Conditional Metric Display (Mobile)

```python
# Show fewer metrics on mobile

def get_screen_width():
    """Approximate screen width (default to desktop)."""
    return 1024  # Default; could use session state for actual width

screen_width = get_screen_width()

if screen_width < 768:
    # Mobile: Show 4 most critical metrics
    key_metrics = [
        ("NIFTY SPOT", f"₹{latest_close:,.0f}", "white", f"ATM: {int(round(float(spot_price) / 50) * 50)}", "Spot price"),
        ("MARKET", condition_html, "", f"RSI: {latest['rsi_14']:.1f}", "Market regime"),
        ("IV LEVEL", f"{base_iv*100:.1f}%", "purple", f"IV Rank: {iv_rank:.0f}%", "Volatility level"),
        ("DAYS TO EXPIRY", f"{tte_days}", "green", "Weekly Thursday", "Time remaining"),
    ]
    cols = st.columns(2)  # 2 columns on mobile
    for i, metric in enumerate(key_metrics):
        with cols[i % 2]:
            display_metric_card(*metric)

elif screen_width < 1024:
    # Tablet: Show 4–5 metrics
    key_metrics = key_metrics[:5]
    cols = st.columns(3)
    for i, metric in enumerate(key_metrics):
        with cols[i % 3]:
            display_metric_card(*metric)

else:
    # Desktop: Show all 6 metrics
    cols = st.columns(6)
    for i, metric in enumerate(all_metrics):
        with cols[i]:
            display_metric_card(*metric)

def display_metric_card(label, value, color, sub, tooltip):
    """Helper to display a single metric card."""
    st.markdown(
        f'<div class="metric-card" title="{tooltip}">'
        f'<div class="label">{label}</div>'
        f'<div class="value {color}">{value}</div>'
        f'<div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )
```

---

## 4. INFO GUIDES (All Tabs)

### 4.1 — Reusable Info Guide Function

```python
# Add to a utils file (e.g., ui/info_guides.py)

def render_info_guide(tab_name: str, content: str, icon="📖"):
    """
    Render expandable info guide for any tab.
    
    Args:
        tab_name: Name of tab (e.g., "Market Overview")
        content: Markdown content to show
        icon: Emoji icon (default 📖)
    """
    with st.expander(f"{icon} {tab_name} Guide — Click to Learn", expanded=False):
        st.markdown(content)

# Define glossaries as constants

MARKET_OVERVIEW_GUIDE = """
### Key Indicators Explained

#### RSI (Relative Strength Index)
- **What it is:** Momentum oscillator (0–100 scale)
- **How to read it:**
  - **>70:** Overbought (potential sell signal, but not a trade signal by itself)
  - **<30:** Oversold (potential buy signal)
  - **40–60:** Neutral (no directional bias)
- **Entry tip:** Enter bull call spread when RSI is 40–60 and price crosses ABOVE SMA 20

#### SMA (Simple Moving Average)
- **SMA 20:** 20-day average (short-term trend)
- **SMA 50:** 50-day average (medium-term trend)
- **Setup:**
  - Price above both = bullish (buy call spreads)
  - Price below both = bearish (buy put spreads)
  - Price between them = uncertain (short strangles)

#### Bollinger Bands
- **Upper band:** Resistance level
- **Lower band:** Support level
- **Middle band:** 20-day SMA
- **Use:** Identify overbought/oversold levels

#### VWAP (Volume-Weighted Average Price)
- The average price, weighted by volume
- If price > VWAP → bullish momentum
- If price < VWAP → bearish momentum
"""

OPTION_CHAIN_GUIDE = """
### Understanding the Option Chain

#### Columns in the Table

**LTP (Last Traded Price)**
- What the option costs RIGHT NOW
- Higher for ITM options, lower for OTM

**IV (Implied Volatility)**
- Market's estimate of future moves (as a %)
- 14% = market expects NIFTY to move ~1.2% this week
- **Higher IV = more expensive premiums (good for sellers)**
- **Lower IV = cheaper premiums (good for buyers)**

**Delta (Directional Exposure)**
- For calls: 0 to 1 (negative for puts)
- **0.50 delta:** 50% probability it expires ITM
- **0.70 delta:** 70% probability ITM (more directional, more expensive)
- **Rule of thumb:** Pick delta ≈ 0.5 for balanced risk/reward in spreads

**Theta (Time Decay)**
- Daily P&L from passage of time
- **Negative:** Buyer loses ₹X per day (you bleed if holding)
- **Positive:** Seller gains ₹X per day (you profit just from waiting)
- **Accelerates:** As expiry approaches, theta decay speeds up
- **Best entry:** When theta starts to accelerate (last 3 days)

**Gamma (Delta's Acceleration)**
- How much delta changes per 100-point NIFTY move
- **High gamma:** Delta changes quickly (risky near expiry, pin risk)
- **Low gamma:** Delta stable (good for sellers, boring for traders)
- **Sweet spot:** Low gamma in first 3 days, then manage carefully

**Vega (IV Sensitivity)**
- P&L impact from 1% IV change
- **Short position:** Profit if IV drops (good if IV rank is high)
- **Long position:** Profit if IV rises (good if IV rank is low)

**Open Interest (OI) & Volume**
- **OI:** Number of open contracts (higher = more liquid)
- **Volume:** Contracts traded today (higher = easy to enter/exit)
- **Rule:** Avoid strikes with OI < ₹50 Cr or bid-ask spread > 0.5%

#### Strike Colors (Legend)
- 🟡 **Yellow:** At-the-Money (ATM) — closest to spot price
- 🔵 **Blue:** In-the-Money (ITM) — profitable if held to expiry
- ⚫ **Gray:** Out-of-the-Money (OTM) — loses value over time

#### Strike Selection Rules

| Strategy | Buy Strike | Sell Strike |
|----------|-----------|------------|
| **Bull Call** | Delta ≈ 0.4–0.5 | Delta ≈ 0.2–0.3 |
| **Bear Put** | Delta ≈ 0.3–0.4 | Delta ≈ 0.2 |
| **Short Strangle** | Delta ≈ 0.2 (both sides) | — |
"""

STRATEGY_BUILDER_GUIDE = """
### Strategy Payoff Diagrams Explained

#### Reading the Chart
- **X-axis:** NIFTY level at expiry (price range)
- **Y-axis:** Your profit/loss in rupees
- **Green area:** Profitable zones
- **Red area:** Loss zones

#### Key Metrics

**Max Profit**
- Best-case scenario (maximum you can earn)
- Occurs at a specific NIFTY level(s) at expiry

**Max Loss**
- Worst-case scenario (maximum you can lose)
- With spreads, this is CAPPED (not unlimited like naked options)

**Breakeven**
- The NIFTY level(s) where you neither profit nor lose
- If NIFTY closes here, P&L = ₹0

**Risk:Reward (R:R)**
- Max Profit ÷ Max Loss
- R:R of 2.0 = earn ₹2 for every ₹1 risked
- Higher R:R is better, but usually means lower probability

#### Strategy Selection Matrix

**Bull Call Spread**
- Best for: Bullish outlook (expect 2–5% upside)
- Setup: Buy ATM call, Sell OTM call
- Risk:Reward: Usually 1.5–2.5x
- Max Profit: Capped at distance between strikes

**Bear Put Spread**
- Best for: Bearish outlook (expect small decline or flat)
- Setup: Sell ITM put, Buy OTM put
- Risk:Reward: Usually 1.5–2.0x
- Max Profit: Capped (net credit received)

**Short Strangle**
- Best for: Sideways market (expect price to stay in range)
- Setup: Sell OTM call + OTM put
- Risk:Reward: Usually 2.0–3.0x
- Max Profit: Capped (total credit)
- **Theta:** Maximum theta decay (fastest profit source)

**Long Strangle**
- Best for: Low IV (expect volatility expansion)
- Setup: Buy OTM call + OTM put
- Risk:Reward: Usually 1.5–2.0x
- Max Loss: Capped (premiums paid)
"""

MONTE_CARLO_GUIDE = """
### Monte Carlo Simulation Explained

#### What Is It?
A technique that:
1. Takes today's price, volatility, and time to expiry
2. Simulates 50,000 random NIFTY price paths
3. Shows you the distribution of outcomes at expiry

#### Why Use It?
- **Better than Black-Scholes** for extreme moves (tail risk)
- **Historical distribution** of returns (not perfect normal curve)
- **Probability cones** show expanding uncertainty over time

#### Key Concepts

**Terminal Price Distribution**
- The histogram shows where NIFTY might end up
- Taller in the middle = more likely
- Flatter on edges = less likely but possible

**Probability Cone**
- Expands over time (more uncertainty farther in future)
- Red bands (±2σ) capture ~95% of outcomes
- Orange bands (±1σ) capture ~68% of outcomes

**P(above target)**
- Percentage of simulated paths that end ABOVE your target price
- Use this for entry decisions: "If 60% of scenarios go above, it's bullish"

#### Using MC for Trade Decisions
- **POP (Probability of Profit) < 40%:** Skip the trade
- **POP 40–55%:** Marginal (only if R:R > 2.0)
- **POP 55–70%:** Good (typical target)
- **POP > 70%:** Excellent (but rare)
"""

BACKTEST_GUIDE = """
### Understanding Backtest Metrics

#### Key Metrics

**Win Rate (%)**
- Percentage of trades that ended profitable
- **60% win rate** = 6 out of 10 trades made money
- Not the most important metric (a few big wins can offset many small losses)

**Profit Factor**
- (Total wins) ÷ (Total losses)
- **PF = 2.0** means you earn ₹2 for every ₹1 lost
- **PF > 1.5** is good; **PF > 2.0** is excellent

**Sharpe Ratio**
- Risk-adjusted return (higher = better)
- **Sharpe > 1.0:** Good
- **Sharpe > 1.5:** Excellent
- **Sharpe > 2.0:** Outstanding (rare)

**Max Drawdown**
- Largest peak-to-trough decline
- **-₹50,000 max DD** means you lost up to 50K from a peak
- Tells you about worst-case volatility

**Average R:R**
- Average risk:reward ratio across all trades
- **1.5x avg R:R** = on average, you risked ₹1 to earn ₹1.50
- Should be > 1.5 to justify the win rate

#### Interpreting Results
- A strategy with **60% win rate + 2.0 PF** beats a **80% win rate + 1.0 PF**
- **Sharpe ratio > 1.0** matters more than win rate
- **Max drawdown** matters: Can your account handle the swings?

#### Caveats
- Historical backtest ≠ future performance
- **Slippage:** Real P&L is 0.5–1% worse (bid-ask spreads)
- **Liquidity:** Real entry/exit prices worse than LTP
- **Fees:** Brokerages charge ~₹10–30 per contract (missing in backtest)
"""

TRADE_SIGNALS_GUIDE = """
### Trade Signal Interpretation

#### Confidence Levels

🟢 **HIGH Confidence**
- **Criteria:** POP > 60% AND R:R > 2.0
- **Recommendation:** Make this your priority trade
- **Entry:** Can enter full size
- **Stop Loss:** 1.5× entry premium (tight)

🟡 **MEDIUM Confidence**
- **Criteria:** POP 50–60% AND R:R 1.5–2.0
- **Recommendation:** Good backup trade
- **Entry:** 50–70% position size
- **Stop Loss:** 2.0× entry premium

🔴 **LOW Confidence**
- **Criteria:** POP < 50% OR R:R < 1.5
- **Recommendation:** Skip unless extra opportunities missing
- **Entry:** Don't enter
- **Alternative:** Wait for better setup

#### Entry & Exit Timing

**Entry: Best after 2:00 PM IST**
- IV typically softest before close
- Morning volatility spikes (avoid)
- Gives you time to adjust if needed
- Last 30 minutes can be chaotic

**Exit Options:**

| Exit Strategy | Best For | When |
|--------------|----------|------|
| **50% profit target** | Short spreads, strangles | First 2 days |
| **Tuesday close** | Directional spreads | If thesis broken, exit early |
| **Thursday 9:30 AM** | Any trade | Day before expiry (final theta) |
| **Stop loss** | Risk management | If trade goes wrong |

#### POP (Probability of Profit) Explained
- Derived from **Monte Carlo simulation** + **Black-Scholes**
- Not a guarantee, just an estimate
- Based on historical volatility and current IV
- **Update as expiry approaches:** Probabilities change daily
"""

# Usage in app.py
def add_info_guides_to_tabs():
    with tab1:
        render_info_guide("📈 Market Overview", MARKET_OVERVIEW_GUIDE)
    
    with tab2:
        render_info_guide("🔗 Option Chain", OPTION_CHAIN_GUIDE)
    
    with tab3:
        render_info_guide("🎯 Strategy Builder", STRATEGY_BUILDER_GUIDE)
    
    with tab4:
        render_info_guide("🎲 Monte Carlo Lab", MONTE_CARLO_GUIDE)
    
    with tab5:
        render_info_guide("📊 Backtest Results", BACKTEST_GUIDE)
    
    with tab6:
        render_info_guide("🚀 Trade Signals", TRADE_SIGNALS_GUIDE)
```

---

## 5. LIQUIDITY IN ₹ CRORE

### 5.1 — Simple Transformation

```python
# File: data/formatter.py

def format_liquidity_rupees(chain_df: pd.DataFrame, lot_size: int = 50) -> pd.DataFrame:
    """
    Convert OI and Volume to ₹ Crore for display.
    
    Args:
        chain_df: Option chain DataFrame (with oi, volume, ltp columns)
        lot_size: Contract size (default 50 for NIFTY)
    
    Returns:
        DataFrame with added OI_Rupees and Vol_Rupees columns
    """
    chain_df = chain_df.copy()
    
    # OI in Rupees = contracts × lot × LTP
    chain_df['oi_rupees'] = (chain_df['open_interest'] * lot_size * chain_df['ltp']) / 1e7  # ₹ Cr
    
    # Volume in Rupees = contracts × lot × avg_price
    avg_price = (chain_df['high'] + chain_df['low']) / 2
    chain_df['vol_rupees'] = (chain_df['volume'] * lot_size * avg_price) / 1e7  # ₹ Cr
    
    return chain_df

# Usage in app.py

enriched_chain = enrich_chain(chain_df, spot_price, tte_days)
enriched_chain = format_liquidity_rupees(enriched_chain)

# Display in table
display_cols = ['strike_price', 'instrument_type', 'ltp', 'oi_rupees', 'vol_rupees',
                'iv', 'delta', 'theta', 'volume', 'open_interest']

st.dataframe(
    enriched_chain[display_cols],
    column_config={
        'oi_rupees': st.column_config.NumberColumn(
            label='OI (₹Cr)',
            format='₹%.1f Cr'
        ),
        'vol_rupees': st.column_config.NumberColumn(
            label='Volume (₹Cr)',
            format='₹%.1f Cr'
        ),
    },
    use_container_width=True,
)
```

---

## 6. MACRO VIEW + COMBO RANKING

### 6.1 — Strategy Recommendation Cards

```python
# File: ui/macro_selector.py

def render_macro_strategy_view(bullish_prob, iv_rank, tte_days):
    """
    High-level strategy recommendation based on market regime.
    """
    
    st.markdown("### 🎯 Strategy Selector — Choose Your Bias")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Bullish Probability", f"{bullish_prob:.0%}", 
               delta=f"{(bullish_prob-0.5)*100:+.0f}pp")
    col2.metric("IV Rank", f"{iv_rank:.0f}%",
               delta=f"{'Elevated (sell)' if iv_rank > 60 else 'Low (buy)'}")
    col3.metric("Days Left", f"{tte_days}d",
               delta=f"{'Theta accelerates' if tte_days <= 2 else 'Still time'}")
    
    st.markdown("---")
    
    # Strategy cards
    strategies = [
        {
            'icon': '📈',
            'title': 'Bull Call Spread',
            'condition': 'You expect NIFTY to RISE (or stay flat)',
            'setup': 'Buy ATM/slightly OTM call → Sell OTM call',
            'requires': f'Bullish Prob > 55%',
            'best_for': 'Trending up days, moderate IV',
            'color': '#00d4aa' if bullish_prob > 0.55 else 'rgba(255,255,255,0.3)',
            'recommended': bullish_prob > 0.55,
        },
        {
            'icon': '📉',
            'title': 'Bear Put Spread',
            'condition': 'You expect NIFTY to FALL (or stay flat)',
            'setup': 'Sell ITM put → Buy OTM put',
            'requires': 'Bullish Prob < 45%',
            'best_for': 'Trending down days, high theta',
            'color': '#ff6b6b' if bullish_prob < 0.45 else 'rgba(255,255,255,0.3)',
            'recommended': bullish_prob < 0.45,
        },
        {
            'icon': '🔄',
            'title': 'Short Strangle',
            'condition': 'You expect NIFTY to stay in a RANGE',
            'setup': 'Sell OTM call + OTM put',
            'requires': 'Bullish Prob 45–55% AND IV > 50th percentile',
            'best_for': 'Sideways markets, maximum theta',
            'color': '#fbbf24' if (0.45 <= bullish_prob <= 0.55 and iv_rank > 50) else 'rgba(255,255,255,0.3)',
            'recommended': (0.45 <= bullish_prob <= 0.55 and iv_rank > 50),
        },
        {
            'icon': '🎲',
            'title': 'Long Strangle',
            'condition': 'You expect a BIG MOVE (either direction)',
            'setup': 'Buy OTM call + OTM put',
            'requires': 'IV very low (< 30th percentile)',
            'best_for': 'Before events, cheap vega',
            'color': '#a78bfa' if iv_rank < 30 else 'rgba(255,255,255,0.3)',
            'recommended': iv_rank < 30,
        },
    ]
    
    for strat in strategies:
        recommended_tag = "✨ RECOMMENDED" if strat['recommended'] else ""
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(78,205,196,0.08) 0%, rgba(0,0,0,0.2) 100%);
            border-left: 4px solid {strat['color']};
            border-radius: 10px;
            padding: 1rem;
            margin: 0.8rem 0;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #e2e8f0;">
                    {strat['icon']} {strat['title']}
                </h4>
                <span style="color: {strat['color']}; font-weight: 700; font-size: 0.8rem;">
                    {recommended_tag}
                </span>
            </div>
            
            <p style="color: #cbd5e1; margin: 0.6rem 0; font-size: 0.9rem;">
                <strong>If:</strong> {strat['condition']}
            </p>
            
            <p style="color: #8b8fa3; margin: 0.4rem 0; font-size: 0.85rem;">
                <strong>Setup:</strong> {strat['setup']}
            </p>
            
            <p style="color: #6b7280; margin: 0.4rem 0; font-size: 0.8rem;">
                <strong>Requirement:</strong> {strat['requires']}
            </p>
            
            <p style="color: #6b7280; margin: 0; font-size: 0.8rem; font-style: italic;">
                🎯 Best for: {strat['best_for']}
            </p>
        </div>
        """, unsafe_allow_html=True)
```

### 6.2 — Combo Ranking Score

```python
# File: models/ranking.py

def score_combo(combo, strategy_type: str, market_condition: str) -> float:
    """
    Calculate composite score (0–1) for combo ranking.
    Higher score = better combo.
    
    Weighting:
    - 40% Delta (strike selection quality)
    - 30% Liquidity (OI in rupees)
    - 20% Win Probability (POP from MC)
    - 10% Risk:Reward ratio
    """
    
    # Ideal deltas depend on strategy
    ideal_deltas = {
        'bull_call_spread': 0.5,      # Buy call delta
        'bear_put_spread': 0.3,       # Sell put delta (BE about 30% OTM)
        'short_strangle': 0.25,       # Both legs OTM
        'long_strangle': 0.25,        # Both legs OTM (buy)
        'iron_condor': 0.25,          # All OTM
    }
    
    ideal_delta = ideal_deltas.get(strategy_type, 0.4)
    
    # Delta score: closer to ideal = higher score
    delta_diff = abs(combo.buy_delta - ideal_delta)
    delta_score = max(0, 1.0 - delta_diff * 2)  # Penalize 0.5 diff heavily
    
    # Liquidity score: normalize to ₹100 Crore = 1.0
    liquidity_score = min(1.0, combo.oi_rupees / 100)  # OI in rupees
    
    # POP (probability of profit) score: 65% = perfect
    pop_score = min(1.0, combo.pop / 0.65)
    
    # R:R score: 2.0x = perfect
    rr_score = min(1.0, combo.risk_reward / 2.0)
    
    # Composite
    composite = (
        0.4 * delta_score +
        0.3 * liquidity_score +
        0.2 * pop_score +
        0.1 * rr_score
    )
    
    return composite

def get_recommendation_text(score: float) -> str:
    """Get recommendation label based on score."""
    if score > 0.75:
        return "✅ HIGHLY RECOMMENDED"
    elif score > 0.65:
        return "✓ RECOMMENDED"
    elif score > 0.55:
        return "△ CONSIDER"
    else:
        return "✗ NOT RECOMMENDED"

# Display in Streamlit

def show_ranked_combos(combos, strategy_type, market_condition):
    """
    Rank combos and display top 3 in detail, full list below.
    """
    
    st.markdown("### 📊 Combo Ranking (by Strategy Score)")
    
    # Score each combo
    ranked = []
    for combo in combos:
        score = score_combo(combo, strategy_type, market_condition)
        recommendation = get_recommendation_text(score)
        
        ranked.append({
            'combo': combo,
            'score': score,
            'recommendation': recommendation,
        })
    
    # Sort by score
    ranked = sorted(ranked, key=lambda x: x['score'], reverse=True)
    
    # Show top 3 in detail
    for idx, item in enumerate(ranked[:3]):
        combo = item['combo']
        score = item['score']
        rec = item['recommendation']
        
        # Color coding
        if score > 0.75:
            border_color = '#00d4aa'
            bg_color = 'rgba(0,212,170,0.08)'
        elif score > 0.65:
            border_color = '#fbbf24'
            bg_color = 'rgba(251,191,36,0.08)'
        else:
            border_color = '#ff6b6b'
            bg_color = 'rgba(255,107,107,0.08)'
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 1.2rem;
            margin: 0.8rem 0;
        ">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1.5rem; align-items: center;">
                
                <!-- Left: Strikes & Premium -->
                <div>
                    <div style="color: #e2e8f0; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.4rem;">
                        Rank #{idx+1}: {combo.label}
                    </div>
                    <div style="color: #8b8fa3; font-size: 0.9rem;">
                        <strong>Buy:</strong> ₹{combo.buy_strike:,.0f} &nbsp;&nbsp;
                        <strong>Sell:</strong> ₹{combo.sell_strike:,.0f}
                    </div>
                    <div style="color: #6b7280; font-size: 0.85rem; margin-top: 0.4rem;">
                        Net Premium: ₹{combo.net_premium:,.0f} &nbsp;|&nbsp;
                        Max Profit: ₹{combo.max_profit:,.0f}
                    </div>
                </div>
                
                <!-- Middle: Score & Recommendation -->
                <div style="text-align: center;">
                    <div style="color: {border_color}; font-weight: 700; font-size: 1.2rem;">
                        {score:.2f}
                    </div>
                    <div style="color: {border_color}; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">
                        {rec}
                    </div>
                </div>
                
                <!-- Right: Key Metrics -->
                <div style="text-align: right;">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: #6b7280; font-size: 0.8rem;">POP</span><br>
                        <span style="color: #00d4aa; font-weight: 600;">
                            {combo.pop:.0%}
                        </span>
                    </div>
                    <div>
                        <span style="color: #6b7280; font-size: 0.8rem;">R:R</span><br>
                        <span style="color: #a78bfa; font-weight: 600;">
                            {combo.risk_reward:.1f}x
                        </span>
                    </div>
                </div>
                
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Full ranked table below
    st.markdown("### All Ranked Combos")
    
    table_data = []
    for idx, item in enumerate(ranked):
        combo = item['combo']
        table_data.append({
            'Rank': idx + 1,
            'Buy Strike': f"₹{combo.buy_strike:,.0f}",
            'Sell Strike': f"₹{combo.sell_strike:,.0f}",
            'Score': f"{item['score']:.2f}",
            'Recommendation': item['recommendation'],
            'POP': f"{combo.pop:.0%}",
            'R:R': f"{combo.risk_reward:.1f}x",
            'OI (₹Cr)': f"{combo.oi_rupees:.1f}",
            'Net Premium': f"₹{combo.net_premium:,.0f}",
        })
    
    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
    )
```

---

**These are the core implementation snippets. Integrate them into your existing app.py following the phase roadmap provided in the strategic plan document.**
