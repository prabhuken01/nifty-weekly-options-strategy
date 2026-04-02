# Short Strangle Theta-Decay Strategy: Backtesting Specification

## Strategy Overview
**Objective**: Build a robust backtest for a short strangle (sell OTM call + sell OTM put) on Nifty and Sensex weeklies, capturing theta decay with same-day exits.

**Core Thesis**: Sell premium in moderate volatility regimes, collect theta decay over 1 day (T-day entry → T-day exit at 3:30 PM IST), manage risk via strict position sizing and stop-losses.

---

## Strategy Parameters

### Entry Rules
- **Timing**: T-1 end-of-day (3:15 PM) OR T early-morning (10:00 AM) OR T late-afternoon (2:45 PM)
- **Strike Selection**: Spot ± **2.5%, 3%, 3.5%, 4%, 4.5%** (parameterized for testing)
  - Short Call: Spot + X%
  - Short Put: Spot - X%
  - Both legs must be OTM at entry

### Exit Rules
- **Timing**: Same day, 3:30 PM IST (market close) — MANDATORY
- **Target**: Exit when P&L reaches 30-40% of max premium collected (entry credit), whichever first
- **Stop-Loss**: 
  - Hard stop if unrealized loss hits -₹2,500 per contract
  - OR if delta moves beyond ±0.35 per leg (indicates directional move)

### Position Sizing
- **Capital per Contract**: 
  - Margin requirement: ~₹1.2 lakh (Nifty weekly)
  - Max risk per trade: ₹2,500 (2.08% of margin)
  - Adjust lot size accordingly

---

## Data Requirements

### Input Data Format (CSV/Excel)
Your historical options data must include:

| Column | Type | Example | Requirement |
|--------|------|---------|-------------|
| Date | YYYY-MM-DD | 2025-01-15 | Calendar date |
| Expiry | YYYY-MM-DD | 2025-01-16 | Weekly expiry date (Nifty: Thursday) |
| Spot_Close | Float | 23547.50 | Closing spot price (for daily reference) |
| Strike | Int | 23600 | Strike price |
| Call_LTP_Entry | Float | 42.50 | Call LTP at entry time |
| Call_LTP_Exit | Float | 15.25 | Call LTP at exit time (3:30 PM) |
| Call_IV_Entry | Float | 18.5 | Call Implied Vol (%) at entry |
| Call_IV_Exit | Float | 16.2 | Call Implied Vol (%) at exit |
| Call_Greeks_Entry | JSON | {"delta": 0.25, "theta": -0.12, "gamma": 0.001} | Optional: Greeks at entry |
| Call_Greeks_Exit | JSON | {"delta": 0.15, "theta": -0.08, "gamma": 0.001} | Optional: Greeks at exit |
| Put_LTP_Entry | Float | 38.75 | Put LTP at entry time |
| Put_LTP_Exit | Float | 12.50 | Put LTP at exit time (3:30 PM) |
| Put_IV_Entry | Float | 19.2 | Put Implied Vol (%) at entry |
| Put_IV_Exit | Float | 17.8 | Put Implied Vol (%) at exit |
| Put_Greeks_Entry | JSON | {"delta": -0.28, "theta": -0.11, "gamma": 0.001} | Optional: Greeks at entry |
| Put_Greeks_Exit | JSON | {"delta": -0.18, "theta": -0.07, "gamma": 0.001} | Optional: Greeks at exit |
| Entry_Time | HH:MM | 10:00 | Entry time (10:00, 14:45, or 15:15) |
| IV_30d_Percentile | Float | 0.65 | 30-day rolling IV percentile (for vol logic) |

**Note**: If Greeks unavailable, code should calculate from IV using Black-Scholes approximation.

---

## Cost Structure (Zerodha + India STT)

### Brokerage (Zerodha)
- **Options**: ₹20 flat per order (call or put separately)
- **Per short strangle round-trip**: 
  - Entry: ₹20 (call) + ₹20 (put) = **₹40**
  - Exit: ₹20 (call) + ₹20 (put) = **₹40**
  - **Total: ₹80 per contract**

### Securities Transaction Tax (STT)
- **On entry (short selling OTM options)**: ₹0 (OTM → no intrinsic value)
- **On exit (square-off)**:
  - If still OTM: ₹0
  - If ITM: 0.05% of intrinsic value payable
  - **Estimate**: ₹50–₹150 per contract (varies by exit profitability)

### Total Round-Trip Cost
- **Typical**: ₹80–₹230 per contract (brokerage + STT)
- **As % of P&L**: 
  - If profit ₹3,000 → cost impact ~5.3–7.7%
  - If profit ₹2,500 → cost impact ~6.4–9.2%

### Cost Impact Rule in Code
```
net_P&L = gross_P&L - (80 + estimated_STT)
where estimated_STT = 0.0005 * max(intrinsic_value_call_exit + intrinsic_value_put_exit, 0)
```

---

## Profitability Metrics

### Primary Metrics
1. **Win Rate (%)**: % of trades with net P&L > 0 (after costs)
2. **Total Profit (₹)**: Sum of all net P&L across trades
3. **Return on Capital (%)**: Total Profit / (Avg Capital Deployed per Trade)
4. **Average P&L per Trade (₹)**: Total Profit / Number of Trades
5. **Profit Factor**: Gross Profit / Gross Loss (> 1.5 is healthy)

### Secondary Metrics
6. **Max Drawdown (%)**: Largest peak-to-trough loss
7. **Theta Decay per Hour**: Average premium collected ÷ holding period
8. **Cost Impact %**: Total costs / Total Profit
9. **Win Rate by Entry Time**: Separate stats for 10:00 AM vs 2:45 PM vs T-1 EOD
10. **Win Rate by Strike Offset**: Separate stats for ±2.5%, ±3%, ±3.5%, ±4%, ±4.5%

### Comparison Format
Your exact use case:

| Metric | Strategy A (₹3k profit, 1.2L capital) | Strategy B (₹2.5k profit, 1.1L capital) |
|--------|----------------------------------------|----------------------------------------|
| Gross P&L | ₹3,000 | ₹2,500 |
| Cost Impact | ₹155 | ₹155 |
| Net P&L | ₹2,845 | ₹2,345 |
| **Return %** | **2.37%** | **2.13%** |
| Theta Decay (per hour) | — | — |
| Decision | ✅ Choose | ❌ Reject |

---

## Volatility-Based Strike Selection Logic

### IV Percentile Calculation
```
IV_30d_percentile = (Current_IV - 30d_IV_MIN) / (30d_IV_MAX - 30d_IV_MIN)
```

### Strike Offset Rules (Parameterized)
Test each rule independently; output metrics for all:

#### Rule 1: IV Regime-Based
```
if IV_30d_percentile < 0.33:          # Low IV
    strike_offset = 0.025  # 2.5% → collect less premium, lower risk
elif IV_30d_percentile < 0.67:        # Medium IV
    strike_offset = 0.035  # 3.5% → balanced
else:                                  # High IV
    strike_offset = 0.045  # 4.5% → collect more premium, higher risk
```

#### Rule 2: Fixed Strike (Baseline)
- Use fixed 3.0% or 4.0% for all trades (control variable)

#### Rule 3: Hybrid (IV + DTE)
```
offset = 0.03 + (0.015 * IV_percentile) + (0.005 * DTE)
# More sophisticated, optional
```

### Output
For each rule: Win rate, total profit, avg theta decay, max drawdown.

---

## Entry Time Analysis

### Three Entry Windows (Test All)

#### 1. T-1 End-of-Day (3:15 PM Previous Day)
- **Hold period**: ~23.5 hours (until 3:30 PM next day)
- **Pros**: Full overnight theta decay, largest calendar decay
- **Cons**: Gap risk (news, RBI announcements), overnight volatility spikes
- **Backtesting insight**: Measure P&L impact if spot moves ±1%, ±2% overnight

#### 2. T Early-Morning (10:00 AM Same Day)
- **Hold period**: ~5.5 hours (10 AM to 3:30 PM)
- **Pros**: Higher liquidity, tighter spreads, lower slippage, known overnight outcome
- **Cons**: Shorter decay window, lower absolute theta collection
- **Backtesting insight**: Compare "profit per hour" vs entry 1

#### 3. T Late-Afternoon (2:45 PM Same Day)
- **Hold period**: ~45 minutes (2:45 PM to 3:30 PM)
- **Pros**: Minimal gap risk, steepest theta curve late-day
- **Cons**: Very tight window, liquidity worst at close, commission overhead dilutes tiny P&L
- **Backtesting insight**: Check if ₹155 cost + wide spreads kill profits here

### Output Table
```
Entry Time       | Win Rate | Avg P&L | Avg P&L/Hour | Max Drawdown | Recommendation
T-1 EOD (23.5h)  | 72%      | ₹2,800  | ₹119         | -₹3,200      | Best theta, high gap risk
T 10:00 AM (5.5h)| 76%      | ₹2,200  | ₹400         | -₹2,000      | ← Balanced
T 2:45 PM (0.75h)| 68%      | ₹800    | ₹1,067       | -₹1,500      | Too tight, cost kills it
```

---

## Risk Management Framework

### Max Loss Calculation
For a short strangle (short call strike = Sc, short put strike = Sp):

```
Intrinsic Loss at Exit = max(Spot_Exit - Sc, 0) + max(Sp - Spot_Exit, 0)
Max Loss = Intrinsic Loss - Premium Collected
Position Max Loss = Max Loss * Contracts * 100 (for Nifty/Sensex)

Risk per Trade = Min(Position Max Loss, ₹2,500)
```

### Position Sizing Rule
```
Contracts_per_Trade = min(
    Total_Capital / 1.2_lakh,  # Can afford
    ₹2,500_max_risk / Risk_per_Trade  # Don't exceed risk limit
)
```

### Stop-Loss Implementation
Exit immediately if ANY of these hit:
1. Unrealized loss ≥ ₹2,500 per contract
2. Delta of short call > +0.35 (upside breach)
3. Delta of short put < -0.35 (downside breach)
4. 3:30 PM market close (forced exit)

**Output**: Track % of trades stopped vs % exited at target vs % forced at close.

---

## Code Deliverables

### 1. Main Backtesting Engine (`backtest_strangle.py`)
- Input: CSV with options data (format above)
- Parameters: Entry time, strike offset, stop-loss, target profit %
- Output:
  - Trade-by-trade breakdown (entry, exit, P&L, Greeks, cost impact)
  - Summary metrics (win rate, total profit, Sharpe, max DD)
  - CSV export of all trades
  - Matplotlib charts: Equity curve, P&L distribution, win rate by strike/time

### 2. IV Percentile Calculator (`calc_iv_percentile.py`)
- Compute 30-day rolling IV min/max/percentile
- Append to input data
- Output: Enriched CSV with IV_30d_Percentile column

### 3. Greeks Approximator (`estimate_greeks.py`)
- If Greeks not in data: use Black-Scholes to estimate delta, theta, gamma at entry/exit
- Input: Spot, Strike, IV, Days-to-expiry, Risk-free rate
- Output: Greeks appended to data

### 4. Reporting Module (`generate_report.py`)
- Aggregate metrics by entry time, strike offset, expiry date
- Produce:
  - Summary table (win rate, total P&L, Sharpe, max DD)
  - Comparison table (3 entry times, 5 strike offsets)
  - Trade log (first 10 + last 10 trades)
  - Matplotlib dashboard: 4-panel chart with equity curve, P&L hist, entry time heatmap, strike offset heatmap

---

## Assumptions & Limitations

### Assumptions
1. **Entry liquidity**: Can always enter at LTP with 1-2 pt slippage
2. **Exit liquidity**: Can always exit at 3:30 PM close price (worst case, bid-ask spread = 2 pts)
3. **Greeks calculation**: If unavailable, estimated via Black-Scholes (standard assumptions: zero dividends, no corporate actions)
4. **Cost**: Zerodha brokerage flat ₹20/order; STT 0.05% of intrinsic value on exit only
5. **No adjustments**: Tested as-is; no rolling, no legging, no intra-day monitoring

### Limitations
1. **Realized vs Mark-to-Market**: Uses LTP at exit; slippage on actual execution may vary ±₹100–₹300
2. **Greeks**: If using Black-Scholes, ignores dividends (Nifty has ~2% dividend yield)
3. **Gap risk**: Cannot model overnight gap > data resolution allows
4. **Execution**: Assumes perfect execution; real markets have friction
5. **STT**: Estimated; actual depends on ITM amount and exact settlement rules

---

## Interpretation Guide

### When is this backtest "passing"?
✅ **Green flags**:
- Win rate ≥ 70%
- Profit factor ≥ 1.8
- Return % ≥ 2.0% per trade (net of all costs)
- Max drawdown < 10% of total capital
- Sharpe ratio > 1.0

❌ **Red flags**:
- Win rate < 60%
- Profit factor < 1.2
- Return % < 1.0% per trade
- Max drawdown > 15%
- Large trades are winners, small trades are losers (randomness indicator)

### What to test first?
1. **Entry time**: Which of 3 windows has best win rate + cost-adjusted return?
2. **Strike offset**: 3% or 4% better? Does higher offset = higher theta decay or just higher risk?
3. **IV regime**: Does switching strike offset based on IV help (rule 1) vs fixed 3.5% (rule 2)?

---

## Example Output Snippet

```
BACKTEST SUMMARY: Nifty Weeklies (Jan 2025 - Mar 2026)
=====================================================

Total Trades: 42
Winning Trades: 31 (73.8%)
Losing Trades: 11 (26.2%)

Total Gross P&L: ₹1,24,560
Total Cost Impact: ₹6,510 (brokerage + STT)
Total NET P&L: ₹1,18,050

Avg Capital Deployed: ₹1.2L per trade
Return on Capital: 2.34% per trade
Annual Return (if scaled): 121.7% (42 trades * 2.34% ÷ 12 months * 365)

Max Drawdown: -₹4,200 (3.5% of capital)
Sharpe Ratio: 1.24

BY ENTRY TIME:
  T-1 EOD:     Win Rate 72.0% | Avg P&L ₹2,800  | Return 2.33%
  T 10:00 AM:  Win Rate 76.5% | Avg P&L ₹2,100  | Return 1.75% ← Best risk-adjusted
  T 2:45 PM:   Win Rate 68.0% | Avg P&L ₹950    | Return 0.79% ← Cost overhead kills it

BY STRIKE OFFSET:
  ±2.5%:  Win Rate 68% | Avg P&L ₹1,800
  ±3.0%:  Win Rate 71% | Avg P&L ₹2,200  ← Best
  ±3.5%:  Win Rate 75% | Avg P&L ₹2,400
  ±4.0%:  Win Rate 73% | Avg P&L ₹2,600
  ±4.5%:  Win Rate 69% | Avg P&L ₹2,900

RECOMMENDATION:
  Deploy T-day 10:00 AM entry with ±3.5% strikes, IV-regime based sizing.
  Expected win rate 75%, return 2.1% per trade, max risk ₹2,500.
```

---

## Next Steps (After Backtest)

1. **Paper trading**: Run the strategy live for 1 week on paper without real capital
2. **Walk-forward test**: Reoptimize parameters every month; check for overfitting
3. **Stress test**: Test on high-volatility periods (FOMC days, RBI decisions)
4. **Position correlation**: If running Nifty + Sensex in parallel, measure correlation of P&L
5. **Live deployment**: Start with 1 contract, scale to 2-3 only if live matches backtest

---

## Questions Before Code Runs?

- What's your preferred IDE/environment? (Jupyter, VS Code, PyCharm?)
- Do you have historical Nifty/Sensex options data ready? (NSE, broker export, AlgoTest, etc.)
- Backtest period preferred? (6 months, 1 year, 2 years?)
- Priority: Speed (fast code) or granularity (detailed Greeks per trade)?
