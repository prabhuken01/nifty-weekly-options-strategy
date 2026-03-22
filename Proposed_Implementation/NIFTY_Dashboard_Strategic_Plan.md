# NIFTY Weekly Options Dashboard — Strategic Improvement Plan

**Last Updated:** March 22, 2026  
**Scope:** Architecture redesign + Feature prioritization + Technical recommendations

---

## Executive Summary

Your dashboard has a **solid foundation** but needs strategic evolution in 3 core areas:

1. **Historical Greeks & Time-Series Data** — Currently static; needs point-in-time lookback
2. **Backtesting Architecture** — Entry signals need date-specific option chains from NSE history
3. **UX/Mobile Optimization** — Desktop-centric design needs responsive refactoring

This plan prioritizes **data architecture** first, then UX. Why? Because better data flows → better signals → higher trade quality.

---

# PART 1: READING & STORING GREEKS (Delta, Theta, Gamma, Vega)

## 1.1 — The Challenge

**Current state:**
- Greeks are **static** in your current sample data generator
- You're computing/displaying them for TODAY only
- No historical series = no backtesting on "what the greeks looked like on Mar 18 at 2 PM"

**What you need:**
- Greeks **stored per strike per timestamp** in a time-series database
- Ability to query: "Give me CE 23200 Greeks as of Mar 18, 2:00 PM"
- This enables realistic backtest entry signals

---

## 1.2 — Data Schema for Time-Series Greeks

### Storage Architecture

```
Database: TimescaleDB (Postgres extension)
Table: option_chain_snapshots

Granularity: 1 snapshot per 5–15 minutes
Why 5 min? Fast enough for intraday backtest, small enough DB footprint

Key columns:
├── timestamp (PRIMARY KEY, indexed)
├── expiry_date (YYYYMMDD, e.g. 2026-03-26)
├── days_to_expiry (calculated, 5 for weekly)
├── strike_price
├── instrument_type (CE/PE)
├── spot_price (NIFTY level at snapshot time)
├── ltp, bid, ask
├── iv (annualized %)
├── volume, open_interest, oi_change
├── delta (per strike, per timestamp)
├── theta (per strike, per timestamp)
├── gamma (per strike, per timestamp)
├── vega (per strike, per timestamp)
├── rho (optional, less critical for short-dated)
└── market_condition (bullish/bearish/sideways)
```

### How Greeks Evolve Over Time

**Critical insight:** Greeks change DAILY as expiry approaches. Example for ATM 23200 CE:

```
Date      | DTE | Delta | Theta    | Gamma  | Vega
-----------|-----|-------|----------|--------|--------
Mar 18 2PM | 4d  | 0.50  | -15.2    | 0.003  | 8.1
Mar 18 EOD | 4d  | 0.48  | -16.1    | 0.0035 | 8.3
Mar 19 2PM | 3d  | 0.52  | -18.5    | 0.0042 | 7.9  ← Theta accelerates
Mar 20 2PM | 2d  | 0.54  | -25.3    | 0.0065 | 7.2  ← Gamma explodes
Mar 21 2PM | 1d  | 0.56  | -35.8    | 0.0120 | 6.8  ← Max decay
Mar 22 9AM | 0.3d| 0.58  | -65.0    | 0.0250 | 6.1  ← Chaos (pin risk)
```

**Action point:** You must capture this progression in your backtest to see:
- ✅ Which strikes had best theta decay (short entries)
- ✅ Which had highest gamma (avoid near expiry)
- ✅ How delta changed day-to-day (adjust hedges)

---

## 1.3 — Data Collection Strategy

### For Live Data (Future Integration)

**When you connect to Zerodha/Upstox:**

```python
# Pseudo-code: Run every 5 minutes

def snapshot_weekly_options():
    """
    Fetch NIFTY weekly option chain, compute/store Greeks
    """
    # Get spot
    nifty_spot = kite.get_ltp("NIFTY50")  # or from ticker
    
    # Get chain (ATM ± 10 strikes for weekly expiry)
    chain = kite.get_option_chain("NFO_NIFTY50", "WEEKLY")
    
    for strike in chain:
        # Extract market data
        ltp = strike['last_price']
        bid = strike['bid']
        ask = strike['ask']
        oi = strike['oi']
        vol = strike['volume']
        iv = strike['iv']  # If broker provides
        
        # Compute Greeks if not provided
        if not iv:
            iv = estimate_iv_from_ltp(ltp, strike_price, spot, dte)
        
        delta, theta, gamma, vega = compute_greeks(
            spot=nifty_spot,
            strike=strike['strike_price'],
            tte=dte / 365,
            iv=iv,
            opt_type=strike['instrument_type'],  # CE or PE
        )
        
        # Store snapshot
        db.insert_snapshot({
            'timestamp': now_ist(),
            'expiry_date': '20260326',
            'strike_price': strike['strike_price'],
            'instrument_type': strike['instrument_type'],
            'spot_price': nifty_spot,
            'ltp': ltp, 'bid': bid, 'ask': ask,
            'iv': iv,
            'volume': vol,
            'open_interest': oi,
            'delta': delta,
            'theta': theta,
            'gamma': gamma,
            'vega': vega,
            'market_condition': classify_market(...)
        })

def compute_greeks(spot, strike, tte, iv, opt_type, r=0.065):
    """
    Black-Scholes Greeks (analytical)
    Inputs:
      - spot: NIFTY level
      - strike: strike price
      - tte: time to expiry in years (e.g., 4/365 = 4 days)
      - iv: implied volatility (e.g., 0.15 = 15%)
      - opt_type: 'CE' or 'PE'
      - r: risk-free rate (default 6.5%)
    
    Returns: (delta, theta, gamma, vega)
    """
    d1 = (log(spot/strike) + (r + 0.5*iv**2)*tte) / (iv*sqrt(tte))
    d2 = d1 - iv*sqrt(tte)
    
    if opt_type == 'CE':
        delta = norm.cdf(d1)
        theta = (
            -spot * norm.pdf(d1) * iv / (2*sqrt(tte))
            - r * strike * exp(-r*tte) * norm.cdf(d2)
        ) / 365  # Per day
    else:  # PE
        delta = norm.cdf(d1) - 1
        theta = (
            -spot * norm.pdf(d1) * iv / (2*sqrt(tte))
            + r * strike * exp(-r*tte) * norm.cdf(-d2)
        ) / 365
    
    gamma = norm.pdf(d1) / (spot * iv * sqrt(tte))
    vega = spot * norm.pdf(d1) * sqrt(tte) / 100  # Per 1% IV change
    
    return delta, theta, gamma, vega
```

### For Backtesting (Historical)

**Option 1: NSE Historical Data (Limited)**
- NSE publishes **option chain snapshots** weekly (archived on their website)
- You can scrape/download weekly option chains for past expiries
- **Problem:** Only weekly snapshots, not intraday
- **Workaround:** Use weekly snapshots + interpolate daily using historical volatility

**Option 2: Broker History (If Available)**
- Zerodha's backtest data API gives EOD option chains
- Upstox archives option chains
- **Best for:** Weekly backtesting (EOD only)

**Option 3: Reconstruct from Price + IV (Synthetic)**
- Use historical NIFTY prices
- Reconstruct IV from broker's historical implied vols (or estimate from range)
- Compute Greeks analytically day-by-day
- **Best for:** Rapid prototyping, testing logic

**Recommendation:** Start with **Option 3** (reconstruct), then layer in **Option 2** (broker data) once integrated.

---

## 1.4 — Display Strategy for Greeks

### In App: Dashboard Greeks Table

**Current problem:** Greeks shown as **single number** (today only).

**Solution:** Add a **"Greeks Timeline"** panel:

```
Date      | Close | IV    | CE 23200 Delta | CE 23200 Theta | PE 23200 Vega
-----------|-------|-------|----------------|----------------|---------------
Mar 18 2PM | 23050 | 14.2% | 0.502          | -15.2          | 8.1
Mar 19 EOD | 23120 | 13.8% | 0.512          | -17.8          | 8.0
Mar 20 EOD | 23080 | 14.5% | 0.498          | -22.1          | 8.3
Mar 21 EOD | 23200 | 15.1% | 0.520          | -31.5          | 8.5
Mar 22 9AM | 23250 | 18.0% | 0.560          | -68.3          | 9.1
```

**Implementation:**
- Create a "Greeks Timeline" section in the **Option Chain** tab
- Allow user to select: **Date range** + **specific strikes** + **specific greeks**
- Plot as line chart: Greek vs Time (shows decay pattern)
- Add **theta acceleration indicator**: "Theta increased 45% in last 24h" (good for short entries)

---

## 1.5 — Key Metrics to Surface

### For CE/PE Selection

When reading greeks for a specific point in time, prioritize these:

| Greek | Why It Matters | For Buyers | For Sellers |
|-------|----------------|-----------|------------|
| **Delta** | Directional exposure (0-1 for calls) | High delta → behaves like stock | Higher = more expensive to hedge |
| **Theta** | Daily P&L decay | Negative (buyers lose daily) | **Positive (sellers profit)** |
| **Gamma** | Delta's acceleration | Low near ATM for sellers (good) | **High = risky near expiry** |
| **Vega** | IV sensitivity | Loss if IV drops | Profit if IV drops (shorting) |

**Backtest insight:**
- **Best short strangle entry:** High theta, LOW gamma, IV > 50th percentile rank
- **Best bull call entry:** Positive theta isn't critical; focus on delta ≈ 0.4–0.6 and high volume

---

# PART 2: POINT-IN-TIME BACKTESTING (Historical Greeks & Options Data)

## 2.1 — The Core Problem

**Current state:**
- Backtest uses **synthetic data** (fake weekly P&Ls)
- No connection to actual option chain snapshots on specific dates
- Can't ask: "If I entered a bull call on Mar 18 at 2 PM, what was the strike selection, Greeks, and actual exit P&L on Mar 22?"

**What you need:**
A backtesting framework that:
1. **Iterates over historical weekly expiries** (Mar 1, Mar 8, Mar 15, Mar 22, etc.)
2. **For each expiry:** Loads option chain snapshot at entry time (e.g., Monday 2 PM)
3. **Applies entry logic** (e.g., Bull Call Spread with delta ≈ 0.5, high OI)
4. **Stores exit point** (Wednesday close OR when target hit)
5. **Calculates P&L** using actual Greeks/liquidity at exit
6. **Aggregates metrics** (Sharpe, win rate, max drawdown)

---

## 2.2 — Backtesting Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Historical Data Store (DB / Parquet)                        │
│  ├─ NIFTY Daily OHLC (5 years)                              │
│  ├─ Option Chain Snapshots (per expiry, EOD or intraday)   │
│  └─ IV History (daily or per-snapshot)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Backtest Engine (Weekly Expiry Loop)                        │
│                                                             │
│  For each weekly expiry (Mar 1, 8, 15, 22, ...):           │
│   1. Load option chain at ENTRY_TIME (Mon 2 PM)            │
│   2. Classify market condition (bullish/bearish/etc)       │
│   3. Select strikes using Delta/OI/IV logic                │
│   4. Calculate Greeks at entry                             │
│   5. Loop days (Mon → Thu):                                │
│       - Track daily theta/gamma/vega P&L                   │
│       - Check exit signal (profit target / stop loss)      │
│       - Record Greeks at each checkpoint                   │
│   6. Record final P&L + metrics                            │
│   7. Store trade record (for analysis)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Output: Trade Log + Metrics                                 │
│  ├─ Per-trade Greeks progression (Mar 18 2PM → Mar 22 9AM) │
│  ├─ Strategy-level stats (Sharpe, win%, drawdown)          │
│  ├─ Greeks-based insights (best theta days, gamma spikes) │
│  └─ Interactive dashboard (filter by date/strategy)        │
└─────────────────────────────────────────────────────────────┘
```

### Data Structure for Backtesting

**Table: option_chain_snapshots (time-series)**
```
expiry_date | timestamp | strike | instrument | ltp | iv | delta | theta | ...
2026-03-26  | 2026-03-18 14:00 | 23200 | CE    | 120 | 14.2% | 0.50 | -15.2 | ...
2026-03-26  | 2026-03-18 14:00 | 23200 | PE    | 85  | 14.3% | -0.48| -12.1 | ...
...
2026-03-26  | 2026-03-22 09:00 | 23200 | CE    | 245 | 22.1% | 0.72 | -68.0 | ...
```

**Table: backtest_trades (output)**
```
expiry_date | entry_date | entry_time | strategy | buy_strike | sell_strike | 
market_condition | entry_delta | entry_theta | entry_greeks | exit_date | 
exit_price | exit_greeks | pnl | pnl_pct | exit_reason | metrics | ...
```

---

## 2.3 — Backtest Entry Logic (Pseudo-Code)

```python
class WeeklyBacktestEngine:
    
    def run_backtest(self, start_date, end_date):
        """
        Backtest from start_date to end_date, one weekly expiry at a time.
        """
        weekly_expiries = self.get_expiry_dates(start_date, end_date)
        results = []
        
        for expiry_date in weekly_expiries:
            # ENTRY: Always Monday 2 PM (or first available time after 2 PM)
            entry_time = self.get_entry_time(expiry_date)  # e.g., 2026-03-18 14:00
            
            # Load option chain at entry time
            entry_chain = self.load_chain_snapshot(expiry_date, entry_time)
            
            if entry_chain is None:
                continue  # Skip if no data
            
            # Get market data at entry
            nifty_spot = entry_chain['spot_price'].iloc[0]
            market_cond = entry_chain['market_condition'].iloc[0]
            
            # Generate entry signals based on market condition
            signals = self.signal_generator.generate(
                chain=entry_chain,
                spot=nifty_spot,
                market_condition=market_cond
            )
            
            # For each signal, simulate the trade
            for signal in signals:
                trade = self.simulate_trade(
                    expiry=expiry_date,
                    entry_signal=signal,
                    entry_time=entry_time,
                    entry_chain=entry_chain
                )
                if trade:
                    results.append(trade)
        
        return self.aggregate_results(results)
    
    def simulate_trade(self, expiry, entry_signal, entry_time, entry_chain):
        """
        Simulate a single trade from entry to exit.
        
        entry_signal contains:
          - strategy (e.g., 'bull_call_spread')
          - buy_strike, sell_strike
          - buy_delta, sell_delta (at entry)
          - expected_pop (from Monte Carlo)
        """
        
        # Calculate entry prices and Greeks
        buy_row = entry_chain[entry_chain['strike_price'] == entry_signal.buy_strike]
        sell_row = entry_chain[entry_chain['strike_price'] == entry_signal.sell_strike]
        
        if buy_row.empty or sell_row.empty:
            return None
        
        buy_ltp = buy_row['ltp'].iloc[0]
        sell_ltp = sell_row['ltp'].iloc[0]
        net_premium = buy_ltp - sell_ltp
        
        entry_delta = buy_row['delta'].iloc[0] - sell_row['delta'].iloc[0]
        entry_theta = buy_row['theta'].iloc[0] - sell_row['theta'].iloc[0]
        entry_gamma = buy_row['gamma'].iloc[0] - sell_row['gamma'].iloc[0]
        entry_vega = buy_row['vega'].iloc[0] - sell_row['vega'].iloc[0]
        
        # Track daily progression
        daily_snapshots = []
        
        # Exit: Simulate day-by-day until expiry or exit signal
        exit_found = False
        for day in range(1, 5):  # Mon to Thu (5 days total, but last day is partial)
            exit_time = entry_time + timedelta(days=day)
            
            # If past expiry Thursday 9:30 AM, exit
            if exit_time.time() >= time(9, 30) and exit_time.weekday() == 3:
                exit_time = exit_time.replace(hour=9, minute=30)
                exit_found = True
            
            exit_chain = self.load_chain_snapshot(expiry, exit_time)
            
            if exit_chain is not None:
                buy_exit = exit_chain[exit_chain['strike_price'] == entry_signal.buy_strike]
                sell_exit = exit_chain[exit_chain['strike_price'] == entry_signal.sell_strike]
                
                if not buy_exit.empty and not sell_exit.empty:
                    exit_ltp_buy = buy_exit['ltp'].iloc[0]
                    exit_ltp_sell = sell_exit['ltp'].iloc[0]
                    exit_premium = exit_ltp_buy - exit_ltp_sell
                    
                    # P&L at this point
                    pnl = (net_premium - exit_premium) * 50  # Lot size = 50
                    
                    # Store daily Greeks
                    daily_snapshots.append({
                        'day': day,
                        'time': exit_time,
                        'exit_premium': exit_premium,
                        'pnl': pnl,
                        'delta': buy_exit['delta'].iloc[0] - sell_exit['delta'].iloc[0],
                        'theta': buy_exit['theta'].iloc[0] - sell_exit['theta'].iloc[0],
                        'gamma': buy_exit['gamma'].iloc[0] - sell_exit['gamma'].iloc[0],
                        'vega': buy_exit['vega'].iloc[0] - sell_exit['vega'].iloc[0],
                    })
                    
                    # Check exit signals (50% profit target, 150% loss stop)
                    max_profit = abs(entry_signal.buy_strike - entry_signal.sell_strike) * 50
                    if pnl >= max_profit * 0.5:  # 50% of max profit
                        exit_found = True
                        exit_reason = "PROFIT_TARGET_50%"
                        break
            
            if exit_found:
                break
        
        # Record trade
        final_snapshot = daily_snapshots[-1] if daily_snapshots else {}
        
        return {
            'expiry_date': expiry,
            'entry_date': entry_time.date(),
            'entry_time': entry_time,
            'strategy': entry_signal.strategy,
            'buy_strike': entry_signal.buy_strike,
            'sell_strike': entry_signal.sell_strike,
            'market_condition': entry_chain['market_condition'].iloc[0],
            'entry_premium': net_premium,
            'entry_delta': entry_delta,
            'entry_theta': entry_theta,
            'entry_gamma': entry_gamma,
            'entry_vega': entry_vega,
            'exit_premium': final_snapshot.get('exit_premium', net_premium),
            'pnl': final_snapshot.get('pnl', 0),
            'exit_reason': exit_found and exit_reason or "EXPIRY",
            'daily_greeks_progression': daily_snapshots,
        }
```

---

## 2.4 — Key Backtesting Outputs

### Trade-by-Trade Greeks Progression

**Display this as a table in backtest results:**

```
Expiry: 2026-03-26 | Strategy: Bull Call Spread | Entry: 2026-03-18 14:00
Buy Strike: 23200 CE | Sell Strike: 23400 CE | Entry Premium: ₹85 | Max Profit: ₹115

Day | Time         | Delta | Theta | Gamma  | Vega  | Premium | P&L    | Exit Signal
----|--------------|-------|-------|--------|-------|---------|--------|-------------------
0   | Mon 14:00    | 0.35  | -18.2 | 0.0028 | 6.1   | 85      | 0      | —
1   | Tue 15:00    | 0.38  | -21.5 | 0.0031 | 6.0   | 78      | 350    | —
2   | Wed 15:00    | 0.42  | -26.8 | 0.0042 | 5.8   | 65      | 1000   | —
3   | Thu 09:30    | 0.51  | -62.1 | 0.0098 | 5.2   | 47      | 1900   | PROFIT_TARGET_50%
```

**Insights from this table:**
- ✅ Theta accelerated each day (good for sellers)
- ✅ Gamma stayed low until Thu (low gamma risk)
- ⚠️ Vega loss ≈ ₹450 (IV compressed from 14.2% to 13.1%)
- ✅ Exited at 50% profit target on Thu morning

---

# PART 3: MONTE CARLO SIMULATION WITH DATE-WISE VISUALIZATION

## 3.1 — The Issue

**Current:** Monte Carlo shows terminal price distribution at expiry only (generic bell curve).

**What's needed:**
- **Probability cones by date** (show how uncertainty grows day-by-day)
- **Interactive slider** to see "what if I exit on Wednesday vs Thursday?"
- **Table:** P(NIFTY in range) for each day through expiry

---

## 3.2 — Date-Wise Probability Visualization

### Concept: Expanding Probability Cone

```
         Day 0          Day 1          Day 2          Day 3          Day 4
        (Entry)        (Tue)          (Wed)          (Thu open)     (Thu 9:30 AM)
        
        23050          Range:         Range:         Range:         Range:
        ↑              22900–23200    22800–23300    22600–23400    22500–23500
        │              ↓                              ↓
     ┌──┴──┐        ┌────┴────┐                  ┌──────┴──────┐
     │ ▓    │        │  ▓▓     │                  │   ▓▓▓▓      │
     │ ▓▓▓  │        │ ▓▓▓▓▓   │                  │  ▓▓▓▓▓▓▓   │
     │▓▓▓▓▓ │        │▓▓▓▓▓▓▓  │                  │▓▓▓▓▓▓▓▓▓▓▓ │
     └──────┘        └────────┘                  └────────────┘
       68%             90%                           95%
      confident       confident                    confident
```

### Implementation

```python
def monte_carlo_paths_by_date(spot, iv, tte_days, n_sims=50000):
    """
    Generate MC paths and return probability distribution at each day.
    
    Returns:
      paths: array of shape (n_sims, tte_days)
      Each row is one simulated path from entry to expiry
    """
    rng = np.random.default_rng(42)
    
    # Daily log returns: ~ N(μ, σ²)
    mu_daily = (0.065 - 0.5 * iv**2) / 365
    sigma_daily = iv / np.sqrt(365)
    
    daily_returns = rng.normal(mu_daily, sigma_daily, (n_sims, tte_days))
    log_prices = np.concatenate([
        np.zeros((n_sims, 1)),  # Day 0 = spot
        np.cumsum(daily_returns, axis=1)
    ], axis=1)
    
    paths = spot * np.exp(log_prices)
    
    # Calculate percentiles at each day
    results = []
    for day in range(tte_days + 1):
        terminal_dist = paths[:, day]
        results.append({
            'day': day,
            'mean': np.mean(terminal_dist),
            'median': np.median(terminal_dist),
            'p5': np.percentile(terminal_dist, 5),
            'p25': np.percentile(terminal_dist, 25),
            'p75': np.percentile(terminal_dist, 75),
            'p95': np.percentile(terminal_dist, 95),
        })
    
    return paths, results

# Display in Streamlit
def show_date_wise_probabilities(paths, spot, target_price, tte_days):
    """
    Show probability table and cone chart
    """
    
    # Table: P(above target) at each day
    data = []
    for day in range(tte_days + 1):
        dist = paths[:, day]
        prob_above = (dist >= target_price).mean()
        prob_range = ((dist >= spot*0.98) & (dist <= spot*1.02)).mean()
        data.append({
            'Day': day,
            'Date': (entry_date + timedelta(days=day)).strftime('%a, %b %d'),
            'P(above ₹{:,.0f})'.format(target_price): f'{prob_above:.1%}',
            'P(±2% of spot)': f'{prob_range:.1%}',
            'Mean': f"₹{np.mean(dist):,.0f}",
            '5th %ile': f"₹{np.percentile(dist, 5):,.0f}",
            '95th %ile': f"₹{np.percentile(dist, 95):,.0f}",
        })
    
    st.dataframe(pd.DataFrame(data), use_container_width=True)
    
    # Cone chart
    fig = go.Figure()
    
    for day in range(tte_days + 1):
        dist = paths[:, day]
        x = [day] * len(dist)
        fig.add_trace(go.Scatter(
            x=x, y=dist,
            mode='markers',
            marker=dict(size=2, color='rgba(78,205,196,0.1)'),
            showlegend=False,
        ))
    
    # Percentile bands
    days = np.arange(tte_days + 1)
    p5 = [np.percentile(paths[:, d], 5) for d in days]
    p95 = [np.percentile(paths[:, d], 95) for d in days]
    median = [np.median(paths[:, d]) for d in days]
    
    fig.add_trace(go.Scatter(x=days, y=p95, name='95th %ile', 
                            line=dict(color='#a78bfa', dash='dash')))
    fig.add_trace(go.Scatter(x=days, y=median, name='Median',
                            line=dict(color='#fbbf24', width=2)))
    fig.add_trace(go.Scatter(x=days, y=p5, name='5th %ile',
                            line=dict(color='#ff6b6b', dash='dash'),
                            fill='tonexty'))
    
    fig.update_layout(title='Probability Cone: Day-by-Day')
    st.plotly_chart(fig, use_container_width=True)
```

---

# PART 4: MOBILE RESPONSIVENESS & UX

## 4.1 — The Problem

**Current dashboard:**
- Built for desktop (wide screens)
- Metric cards + tables overflow on mobile
- Tabs stack but content doesn't reflow

**Solution:** Responsive CSS grid + Streamlit layout tricks

---

## 4.2 — Mobile-First Refactoring Strategy

### Principle: Progressive Disclosure

On **desktop** → show everything  
On **tablet** → collapse to 2–3 columns  
On **mobile** → 1 column, prioritize most important

### Implementation

```python
# app.py — Add this near the top

# Detect device type (via window width)
device_code = """
<script>
    let w = window.innerWidth;
    window.deviceType = w < 768 ? 'mobile' : w < 1024 ? 'tablet' : 'desktop';
</script>
"""
st.markdown(device_code, unsafe_allow_html=True)

# Helper function for responsive columns
def responsive_columns(n_cols):
    """
    Return appropriate column count based on screen width.
    n_cols is desired count on desktop.
    """
    if st.query_params.get('_device_type') == 'mobile':
        return 1
    elif st.query_params.get('_device_type') == 'tablet':
        return max(1, n_cols // 2)
    else:
        return n_cols

# Usage in top metrics row
metric_cols = st.columns(responsive_columns(6))

# Or: Fixed responsive CSS
responsive_css = """
<style>
@media (max-width: 768px) {
    .metric-card {
        padding: 0.8rem !important;
        margin-bottom: 0.5rem;
    }
    .metric-card .value { font-size: 1.2rem !important; }
    .metric-card .label { font-size: 0.65rem !important; }
    
    /* Stack tables vertically on mobile */
    [data-testid="stDataFrame"] {
        font-size: 0.75rem;
    }
}
</style>
"""
st.markdown(responsive_css, unsafe_allow_html=True)
```

### Key Mobile Changes

| Element | Desktop | Mobile |
|---------|---------|--------|
| Top metrics | 6 columns | Stack (1 col) |
| Option chain | 3-col (Calls / Strikes / Puts) | Tabs: Calls → Strikes → Puts |
| Charts | Full width | Reduce height, swipe to scroll |
| Greeks table | All greeks shown | Key greeks only (delta, theta) |
| Strategy builder | Side-by-side payoff | Stacked (input above chart) |

---

## 4.3 — Mobile-Specific Optimizations

**For metric cards:**
```python
# Show only 4 metrics on mobile (most critical)
if st.query_params.get('device') == 'mobile':
    key_metrics = ['NIFTY SPOT', 'MARKET', 'IV LEVEL', 'DAYS TO EXPIRY']
else:
    key_metrics = all_metrics  # 6 on desktop
```

**For tables:**
```python
# On mobile: reduce columns, increase row height
if is_mobile:
    display_cols = ['strike_price', 'ltp', 'delta', 'theta']  # Key only
else:
    display_cols = all_available_cols

st.dataframe(df[display_cols], height=500 if is_mobile else 800)
```

---

# PART 5: DROPDOWN INFO GUIDES (Per Tab)

## 5.1 — Current State & Gap

**Current:** Only "Strategy Builder" tab has glossary expander.

**Goal:** Each tab gets a contextual **"?"** button that opens a guide specific to that tab.

---

## 5.2 — Implementation Pattern

```python
def info_guide(tab_name, content_md):
    """
    Render an expandable info guide for a tab.
    """
    with st.expander(f"📖 {tab_name} Guide — Click to learn"):
        st.markdown(content_md)

# In each tab:

with tab1:
    info_guide("📈 Market Overview", """
    ### What This Tab Shows
    
    **Price Chart:** NIFTY price + moving averages (SMA 20, SMA 50) + Bollinger Bands
    - Green candles = up days
    - Red candles = down days
    - SMA 20 (turquoise) = short-term trend
    - SMA 50 (orange) = medium-term trend
    
    ### How to Read It
    
    **Bullish setup:**
    - Price above both SMA 20 and SMA 50
    - RSI > 60 (overbought but momentum)
    - Volume increasing
    
    **Bearish setup:**
    - Price below both SMAs
    - RSI < 40 (oversold)
    - Volume declining
    
    **Trade Entry Tip:**
    Enter bull call spreads when price crosses ABOVE SMA 20 from below
    (trend reversal setup, higher probability).
    """)

with tab2:
    info_guide("🔗 Option Chain", """
    ### Understanding the Option Chain
    
    **Columns Explained:**
    - **LTP:** Last traded price (what the option costs right now)
    - **IV:** Implied volatility (market's estimate of future moves, 0–100%)
    - **Delta:** Directional sensitivity (0–1 for calls, 0 to -1 for puts)
    - **Theta:** Daily decay (negative for buyers, positive for sellers)
    - **Open Interest:** Number of open contracts (higher = more liquid)
    - **Volume:** Contracts traded today (higher = easier to enter/exit)
    
    **Color Legend:**
    - 🟡 Yellow strike = ATM (at the money, near spot price)
    - 🔵 Blue = ITM (in the money, profitable if held to expiry)
    - ⚫ Gray = OTM (out of the money, loses value over time)
    
    **Strike Selection Rule:**
    For bull call spreads, pick **delta ≈ 0.5 for the buy strike**
    (50% probability ITM at expiry, balanced risk/reward).
    """)

with tab3:
    info_guide("🎯 Strategy Builder", """
    [Existing strategy glossary...]
    """)

# ... and so on for all tabs
```

---

# PART 6: LIQUIDITY IN MONETARY TERMS (OI & Volume in ₹ Crore)

## 6.1 — The Issue

**Current:** OI and Volume shown as raw numbers (e.g., "80,389" contracts).

**Better:** Convert to **rupees** for intuitive understanding.

---

## 6.2 — Conversion Formula

```
OI in Rupees = OI (in contracts) × Lot Size × LTP
             = OI × 50 × LTP

Volume in Rupees = Volume (in contracts) × 50 × Average_Price_Today
                 = Vol × 50 × (High + Low) / 2
```

### Example

```
23200 CE:
  OI = 60,567 contracts
  LTP = 327.41
  OI in ₹ = 60,567 × 50 × 327.41 = ₹990.9 Crore

  Volume = 7,278 contracts
  Avg Price = (337 + 320) / 2 = 328.5
  Volume in ₹ = 7,278 × 50 × 328.5 = ₹119.6 Crore
```

### Display Changes

```python
# In option chain table

def format_liquidity_rupees(oi_contracts, volume_contracts, ltp, 
                             high, low):
    """
    Convert OI and Volume to ₹ Crore for display.
    """
    oi_rupees = (oi_contracts * 50 * ltp) / 1e7  # ₹ Crore
    avg_price = (high + low) / 2
    vol_rupees = (volume_contracts * 50 * avg_price) / 1e7
    
    return {
        'OI (₹Cr)': f"{oi_rupees:.1f}",
        'Volume (₹Cr)': f"{vol_rupees:.1f}",
    }

# In dataframe
chain_display = enriched_chain.copy()
chain_display['OI_Rupees'] = enriched_chain.apply(
    lambda row: (row['open_interest'] * 50 * row['ltp']) / 1e7, axis=1
)
chain_display['Vol_Rupees'] = enriched_chain.apply(
    lambda row: (row['volume'] * 50 * (row['high'] + row['low']) / 2) / 1e7, axis=1
)

# Display with color-coding (higher ₹ = brighter green)
st.dataframe(
    chain_display[['strike_price', 'ltp', 'OI_Rupees', 'Vol_Rupees', ...]],
    column_config={
        'OI_Rupees': st.column_config.NumberColumn(
            label='OI (₹Cr)',
            format='₹%.1f Cr'
        ),
        'Vol_Rupees': st.column_config.NumberColumn(
            label='Volume (₹Cr)',
            format='₹%.1f Cr'
        ),
    }
)
```

---

# PART 7: MACRO VIEW + STRATEGY RANKING SYSTEM

## 7.1 — Two-Tier Architecture

### Tier 1: Macro View (Decision Tree)

**Purpose:** Help user **quickly choose the right strategy** without diving into tables.

**Design:** Interactive decision tree / flowchart

```
                    ┌─ Is NIFTY likely to go UP? ─┐
                    │   (Check RSI, SMA, IV Rank)  │
                    │                              │
        ┌───────────┴──────────────┬───────────────┴─────────────┐
        │                          │                             │
       YES                        NO                        UNCERTAIN
        │                          │                             │
        ↓                          ↓                             ↓
    BULL CALL          BEAR PUT SPREAD        SHORT STRANGLE
    SPREAD             (or Iron Condor)       (or Short Straddle)
        │                          │                             │
        └──────────────────────────┴─────────────────────────────┘
                          │
                          ↓
        ┌─────────────────────────────────────┐
        │ Tier 2: Combo Ranking (by score)    │
        │ Sort by: Delta + OI + Win Prob      │
        │ Show: Top 3 combos with P&L targets │
        └─────────────────────────────────────┘
```

---

## 7.2 — Macro View Implementation

```python
def macro_decision_view():
    """
    High-level strategy selector based on market regime.
    """
    
    st.markdown("### 🎯 Strategy Selector — Start Here")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bullish_prob = predict_direction()  # 0-1
        st.metric(
            "Bullish Probability",
            f"{bullish_prob:.0%}",
            delta=f"{(bullish_prob - 0.5) * 100:+.0f}pp"
        )
    
    with col2:
        iv_percentile = calculate_iv_rank()  # 0-100
        st.metric(
            "IV Percentile Rank",
            f"{iv_percentile:.0f}%",
            delta=f"{'Elevated' if iv_percentile > 60 else 'Low'}"
        )
    
    with col3:
        days_left = tte_days
        st.metric(
            "Days to Expiry",
            f"{days_left}d",
            delta=f"{'Theta accelerates!' if days_left <= 2 else 'Time still left'}"
        )
    
    with col4:
        best_strategy = recommend_strategy(bullish_prob, iv_percentile)
        st.metric(
            "Recommended Strategy",
            best_strategy,
            delta="High confidence"
        )
    
    st.markdown("---")
    
    # Decision cards
    st.markdown("### Choose Based on Your View")
    
    strategy_cards = [
        {
            'title': '📈 Bull Call Spread',
            'condition': 'You expect NIFTY to rise (or stay flat)',
            'setup': 'Buy ATM or slightly OTM call, Sell OTM call',
            'requires': 'Bullish Probability > 55%',
            'best_for': 'Trending up days with moderate IV',
            'icon': '✅' if bullish_prob > 0.55 else '⚠️'
        },
        {
            'title': '📉 Bear Put Spread',
            'condition': 'You expect NIFTY to fall (or stay flat)',
            'setup': 'Sell ITM put, Buy OTM put',
            'requires': 'Bullish Probability < 45%',
            'best_for': 'Trending down days, high theta',
            'icon': '✅' if bullish_prob < 0.45 else '⚠️'
        },
        {
            'title': '🔄 Short Strangle',
            'condition': 'You expect NIFTY to stay in a range',
            'setup': 'Sell OTM call & OTM put',
            'requires': 'Bullish Prob 45–55% AND IV > 50th percentile',
            'best_for': 'Sideways markets, max theta',
            'icon': '✅' if 0.45 <= bullish_prob <= 0.55 else '⚠️'
        },
        {
            'title': '🎲 Long Strangle',
            'condition': 'You expect a big move (either direction)',
            'setup': 'Buy OTM call & OTM put',
            'requires': 'IV very low (< 30th percentile)',
            'best_for': 'Before earnings or events, cheap vega',
            'icon': '✅' if iv_percentile < 30 else '⚠️'
        },
    ]
    
    for card in strategy_cards:
        display_strategy_card(card)

def display_strategy_card(card):
    """Render a single strategy recommendation card."""
    
    icon = card['icon']
    color = '#00d4aa' if icon == '✅' else '#ff6b6b'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(78,205,196,0.08), rgba(78,205,196,0.02));
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 1rem;
        margin: 0.8rem 0;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; color: #e2e8f0;">{card['title']}</h4>
            <span style="font-size: 1.5rem;">{card['icon']}</span>
        </div>
        
        <p style="color: #cbd5e1; margin: 0.5rem 0; font-size: 0.9rem;">
            <strong>If:</strong> {card['condition']}
        </p>
        
        <p style="color: #8b8fa3; margin: 0.5rem 0; font-size: 0.85rem;">
            <strong>Setup:</strong> {card['setup']}
        </p>
        
        <p style="color: #8b8fa3; margin: 0.5rem 0; font-size: 0.85rem;">
            <strong>Condition:</strong> {card['requires']}
        </p>
        
        <p style="color: #6b7280; margin: 0; font-size: 0.8rem; font-style: italic;">
            🎯 Best for: {card['best_for']}
        </p>
    </div>
    """, unsafe_allow_html=True)
```

---

## 7.3 — Tier 2: Combo Ranking System

### Ranking Logic

For each strategy, rank combos by a **composite score**:

```
Score = (0.4 × Delta_Score) + (0.3 × Liquidity_Score) + (0.2 × Win_Prob_Score) + (0.1 × R:R_Score)

Where:
  Delta_Score = 1.0 if delta near ideal, 0.5 otherwise
  Liquidity_Score = OI_in_Rupees / Max_OI_in_Chain
  Win_Prob_Score = POP / 0.65 (capped at 1.0 if POP > 65%)
  R:R_Score = Risk_Reward / 2.0 (capped at 1.0 if R:R > 2.0)
```

### Display: Ranked Combo Table

```python
def combo_ranking_table(combos, strategy_type, market_condition):
    """
    Rank combos and display top 3.
    """
    
    ranked = []
    for combo in combos:
        score = calculate_combo_score(combo, strategy_type)
        ranked.append({
            'Rank': len(ranked) + 1,
            'Buy Strike': f"₹{combo.buy_strike:,.0f}",
            'Sell Strike': f"₹{combo.sell_strike:,.0f}",
            'Delta': f"{combo.buy_delta:.2f}",
            'OI (₹Cr)': f"{combo.oi_rupees:.1f}",
            'Premium': f"₹{combo.net_premium:,.0f}",
            'Max Profit': f"₹{combo.max_profit:,.0f}",
            'POP': f"{combo.pop:.0%}",
            'R:R': f"{combo.risk_reward:.1f}x",
            'Score': f"{score:.2f}",
            'Recommendation': get_recommendation(score),
        })
    
    ranked_df = pd.DataFrame(ranked)
    ranked_df = ranked_df.sort_values('Score', ascending=False)
    
    # Display top 3
    st.markdown("### Top Combo Recommendations")
    
    for idx, row in ranked_df.head(3).iterrows():
        confidence = (
            'HIGH' if row['Score'] > 0.75 else
            'MEDIUM' if row['Score'] > 0.6 else
            'LOW'
        )
        color = '#00d4aa' if confidence == 'HIGH' else '#fbbf24' if confidence == 'MEDIUM' else '#ff6b6b'
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(78,205,196,0.05), rgba(0,0,0,0.2));
            border: 1px solid {color};
            border-radius: 10px;
            padding: 1rem;
            margin: 0.8rem 0;
        ">
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1rem;">
                <div>
                    <span style="color: #e2e8f0; font-weight: 600;">
                        {row['Buy Strike']} / {row['Sell Strike']}
                    </span>
                    <br>
                    <span style="color: #8b8fa3; font-size: 0.85rem;">
                        Premium: {row['Premium']} | Max Profit: {row['Max Profit']}
                    </span>
                </div>
                <div style="text-align: center;">
                    <div style="color: {color}; font-weight: 700; font-size: 0.9rem;">
                        {confidence}
                    </div>
                    <div style="color: #6b7280; font-size: 0.8rem;">
                        Score: {row['Score']}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #00d4aa; font-weight: 600; font-size: 0.9rem;">
                        POP: {row['POP']}
                    </div>
                    <div style="color: #6b7280; font-size: 0.8rem;">
                        R:R: {row['R:R']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Full table below
    st.markdown("### All Ranked Combos")
    st.dataframe(
        ranked_df[['Rank', 'Buy Strike', 'Sell Strike', 'Delta', 'OI (₹Cr)', 
                   'POP', 'R:R', 'Score', 'Recommendation']],
        use_container_width=True,
        hide_index=True,
    )

def calculate_combo_score(combo, strategy_type):
    """
    Weighted score for combo ranking.
    """
    # Ideal delta depends on strategy
    ideal_delta = {
        'bull_call_spread': 0.5,    # Buy call delta
        'bear_put_spread': 0.3,     # Sell put delta
        'short_strangle': 0.25,     # Both OTM
    }.get(strategy_type, 0.4)
    
    delta_diff = abs(combo.buy_delta - ideal_delta)
    delta_score = max(0, 1.0 - delta_diff * 2)  # Closer = higher
    
    liquidity_score = min(1.0, combo.oi_rupees / 100)  # Normalize to ₹100Cr
    
    pop_score = min(1.0, combo.pop / 0.65)  # 65% = perfect
    
    rr_score = min(1.0, combo.risk_reward / 2.0)  # 2.0x = perfect
    
    composite = (
        0.4 * delta_score +
        0.3 * liquidity_score +
        0.2 * pop_score +
        0.1 * rr_score
    )
    
    return composite

def get_recommendation(score):
    """Get recommendation text based on score."""
    if score > 0.75:
        return "✅ HIGHLY RECOMMENDED"
    elif score > 0.6:
        return "✓ RECOMMENDED"
    elif score > 0.5:
        return "△ CONSIDER"
    else:
        return "✗ AVOID"
```

---

# PART 8: IMPLEMENTATION ROADMAP

## 8.1 — Prioritized Phases

| Phase | Feature | Effort | Impact | Status |
|-------|---------|--------|--------|--------|
| **1A** | Greeks time-series schema | 2 days | 🔴 CRITICAL | Not started |
| **1B** | Greeks display (timeline table) | 2 days | 🔴 CRITICAL | Not started |
| **2A** | Backtest engine (weekly loop) | 5 days | 🔴 CRITICAL | Not started |
| **2B** | Per-trade Greeks progression display | 3 days | 🟠 HIGH | Not started |
| **3A** | Date-wise MC simulation | 3 days | 🟠 HIGH | Not started |
| **4A** | Mobile CSS overhaul | 2 days | 🟠 HIGH | Not started |
| **5A** | Info guides (all tabs) | 1 day | 🟡 MEDIUM | Partial |
| **6A** | Liquidity in ₹ Crore | 1 day | 🟡 MEDIUM | Not started |
| **7A** | Macro strategy selector | 3 days | 🟠 HIGH | Not started |
| **7B** | Combo ranking system | 2 days | 🟠 HIGH | Not started |

**Critical path (months):** 1A → 1B → 2A → 2B (14 days minimum)

---

## 8.2 — Dependency Graph

```
Greeks time-series (1A)
    ↓
Greeks timeline display (1B)
    ↓
Backtest engine (2A) ← needs historical Greeks
    ↓
Per-trade Greeks progression (2B)
    ↓
Date-wise MC (3A)

[Parallel]:
Mobile CSS (4A)
Info guides (5A)
Liquidity ₹ (6A)
Macro selector (7A) → Ranking system (7B)
```

---

## 8.3 — Quick Wins (Start Here)

**Week 1:**
1. Add liquidity in ₹ Crore (6A) — 1 day, high user satisfaction
2. Add info guides to all tabs (5A) — 1 day, ease confusion
3. Responsive CSS (4A) — 2 days, fix mobile
4. Macro strategy selector (7A) — 3 days, improves decision-making

**Week 2–3:**
5. Greeks time-series schema & display (1A, 1B) — 4 days
6. Backtest engine (2A) — 5 days
7. Per-trade Greeks table (2B) — 3 days

**Week 4+:**
8. Date-wise MC (3A)
9. Combo ranking (7B)
10. Live broker integration

---

# PART 9: TECHNICAL ARCHITECTURE RECOMMENDATIONS

## 9.1 — Data Storage

**Current:** Synthetic data in memory (sample_data.py)

**Recommended upgrade:**

```
┌──────────────────────────────┐
│ TimescaleDB (PostgreSQL ext) │ ← Historical Greeks + snapshots
│ - option_chain_snapshots     │
│ - nifty_daily_ohlc          │
│ - iv_history                │
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│ DuckDB / Parquet files       │ ← Cache for fast backtest queries
│ - Compressed weekly snapshots│
│ - Parquet partitioned by date│
└──────────────────────────────┘
            ↓
┌──────────────────────────────┐
│ Streamlit Cache (@st.cache)  │ ← Session cache for charts
│ - Loaded chains              │
│ - MC paths                   │
└──────────────────────────────┘
```

**Why this architecture?**
- **TimescaleDB:** Real-time ingestion + time-series queries are fast
- **Parquet:** Compressed (50% smaller), columnar (fast backtest lookups)
- **Session cache:** Avoid recomputing Greeks for same snapshot

---

## 9.2 — API Payloads (When Connecting to Broker)

**Zerodha Kite example:**

```python
# GET /quote/?i=NSE:NIFTY50
# Returns spot price

# GET /instruments/
# Returns all instruments with token IDs

# WS subscribe to weekly option tokens
# Updates tick data every ~50ms

# Backtest API (if available)
# GET /historical/?i=NFO:NIFTY50JAN2426C23200&interval=5minute
# Returns OHLC for that specific contract in the past
```

---

## 9.3 — Caching Strategy

```python
@st.cache_data(ttl=300)  # 5 min cache
def load_option_chain_snapshot(expiry, timestamp):
    """Load from DB, cache in session."""
    return db.query(f"""
        SELECT * FROM option_chain_snapshots
        WHERE expiry_date = {expiry} AND timestamp = {timestamp}
    """)

@st.cache_data(ttl=3600)  # 1 hour
def run_backtest_full(start_date, end_date):
    """Full backtest (expensive), cache longer."""
    return engine.backtest(start_date, end_date)

# Clear cache if user changes parameters
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

---

# PART 10: SUMMARY & NEXT STEPS

## Key Takeaways

| Question | Answer | Impact |
|----------|--------|--------|
| **How to read Greeks?** | Store per-snapshot in time-series DB, display progression | ✅ Enables theta analysis |
| **How to backtest point-in-time?** | Weekly loop: load chain at entry, simulate day-by-day | ✅ Realistic backtests |
| **How to show MC date-wise?** | Expand probability cone by day (percentile bands) | ✅ Better risk visualization |
| **Mobile friendly?** | Responsive CSS + 1-col on mobile, reduce metric cards | ✅ All-device support |
| **Info guides?** | Expanders in each tab with context-specific glossaries | ✅ Self-serve learning |
| **Liquidity in ₹?** | OI_Rupees = OI × 50 × LTP, Volume_Rupees = similar | ✅ Intuitive understanding |
| **Macro + ranking?** | Decision tree → combo scorer (delta+OI+POP+R:R) | ✅ Faster decision-making |

---

## Immediate Action Items (Next 2 Weeks)

### Week 1
- [ ] **Add ₹ Crore liquidity columns** (1 day)
- [ ] **Add info guides to all tabs** (1 day)
- [ ] **Mobile CSS overhaul** (2 days)
- [ ] **Macro strategy selector cards** (3 days)

### Week 2+
- [ ] **Create Greeks time-series schema** (2 days)
- [ ] **Backtest engine refactor** (5 days)
- [ ] **Greeks progression visualization** (2 days)

---

## Code Structure Improvements

**Current app.py is 1,500+ lines.** Refactor into modules:

```
app.py (main, imports)
├── ui/
│   ├── header.py (top metrics)
│   ├── tabs/
│   │   ├── market_overview.py
│   │   ├── option_chain.py
│   │   ├── strategy_builder.py
│   │   ├── monte_carlo.py
│   │   ├── backtest.py
│   │   └── trade_signals.py
│   └── info_guides.py (shared glossaries)
├── data/
│   ├── loader.py (DB queries, sample generation)
│   └── formatter.py (₹ conversions, Greeks formatting)
├── models/
│   ├── greeks.py (BS calculations)
│   ├── backtest.py (backtesting engine)
│   └── ranking.py (combo scorer)
└── utils/
    ├── responsive.py (mobile detection)
    └── cache.py (Streamlit caching helpers)
```

---

**This plan is comprehensive and actionable. Start with the quick wins (₹ Crore + info guides + mobile), then move to the critical path (Greeks + backtest).** Good luck! 🚀
