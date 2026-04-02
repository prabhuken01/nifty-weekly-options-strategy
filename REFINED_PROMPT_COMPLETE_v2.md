# Nifty/Sensex Short Strangle Backtest — Complete System Specification
## v2.0 (Apr 1, 2026 Cost Update + Frontend + Data Sources)

---

## PART 0: EXECUTIVE SUMMARY

**Objective**: Build a production-grade backtesting + visualization system for short strangle theta-decay strategies on Nifty/Sensex weeklies, with interactive dashboard and data sourcing guide.

**System consists of**:
1. **Python backend** — backtesting engine (pandas-based, 3 modules)
2. **Frontend dashboard** — interactive web UI (React/HTML) for parameter input and results visualization
3. **Data sourcing** — proven routes to obtain NSE Bhavcopy, free broker APIs, or platform free tiers

**Cost structure (updated Apr 1, 2026)**:
- Zerodha brokerage: ₹40/order (₹160 round-trip)
- STT: 0.15% on intrinsic value at exit
- Total costs: ~₹220–250 per trade

**Success threshold**: Win rate ≥70%, return ≥2.0% net per trade (after all costs).

---

## PART 1: BACKEND — BACKTESTING ENGINE

### 1.1 Data Input Schema

Your CSV must include these columns (exact names, case-sensitive):

```csv
Date,Expiry,Spot_Close,Strike,Call_LTP_Entry,Call_LTP_Exit,Call_IV_Entry,Call_IV_Exit,Put_LTP_Entry,Put_LTP_Exit,Put_IV_Entry,Put_IV_Exit,Entry_Time
2025-01-15,2025-01-16,23500,24200,42.50,15.25,18.5,16.2,38.75,12.50,19.2,17.8,10:00
```

**Column descriptions**:
- `Date` (YYYY-MM-DD): Calendar date
- `Expiry` (YYYY-MM-DD): Weekly expiry (Nifty: Thursday)
- `Spot_Close` (float): Closing spot price (reference for strike selection)
- `Strike` (int): Strike price
- `Call_LTP_Entry` (float): Call LTP at entry time
- `Call_LTP_Exit` (float): Call LTP at 3:30 PM close (exit)
- `Call_IV_Entry` (float): Call IV (%) at entry
- `Call_IV_Exit` (float): Call IV (%) at exit
- `Put_LTP_Entry` (float): Put LTP at entry
- `Put_LTP_Exit` (float): Put LTP at 3:30 PM close
- `Put_IV_Entry` (float): Put IV (%) at entry
- `Put_IV_Exit` (float): Put IV (%) at exit
- `Entry_Time` (HH:MM): Entry time (10:00, 14:45, 15:15 for T-1 EOD interpretation)

**Optional columns** (nice-to-have):
- `IV_30d_Percentile` (float): 30-day rolling IV percentile (for vol-based strike logic)
- `Call_Delta_Entry`, `Call_Delta_Exit`, `Put_Delta_Entry`, `Put_Delta_Exit` (float): Greeks

If missing, code will calculate from IV using Black-Scholes.

---

### 1.2 Backtesting Parameters

#### Entry Rules
- **Timing options**: 
  - T-1 EOD (3:15 PM previous day) — max theta decay, gap risk
  - T 10:00 AM — balanced, best liquidity
  - T 2:45 PM — minimal risk, tight window
- **Strike offsets** (parameterized, test all 5):
  - Short Call: Spot × (1 + offset)
  - Short Put: Spot × (1 - offset)
  - Offsets: 0.025, 0.030, 0.035, 0.040, 0.045 (±2.5% to ±4.5%)
- **Both legs OTM at entry** — no exceptions

#### Exit Rules
- **Mandatory exit**: 3:30 PM same day (T-day close)
- **Target exit** (optional): When P&L reaches 30–40% of max premium collected
- **Stop-loss** (hard stops):
  - Unrealized loss ≥ ₹2,500 per contract → exit immediately
  - |delta| > 0.35 on either leg → exit immediately
  - 3:30 PM close → forced exit

---

### 1.3 Cost Structure (Updated Apr 1, 2026)

#### Zerodha Brokerage
```
Entry (short strangle):   ₹40 (call) + ₹40 (put) = ₹80
Exit (square-off):        ₹40 (call) + ₹40 (put) = ₹80
────────────────────────────────────────────────────
Total round-trip:         ₹160 per contract
```

**Note**: ₹40/order applies to high-frequency/no-50%-collateral traders. Standard rate is ₹20/order. Use ₹40 for conservatism.

#### STT (Securities Transaction Tax)
```
On entry (short OTM options):     ₹0 (no intrinsic value)
On exit (square-off):             0.15% × intrinsic value
Estimated per trade (if ITM):     ₹50–₹100
────────────────────────────────────────────────────
Total STT (estimate):             ₹50–₹100
```

**Total round-trip cost**: ₹160 (brokerage) + ₹75 (avg STT) = **₹235 per contract**

#### Example Impact
```
₹3,000 gross profit:
  - Brokerage: ₹160
  - STT: ~₹75
  - Total costs: ₹235 (7.8% drag)
  - Net P&L: ₹2,765
  - Return on ₹1.2L: 2.30%

₹2,500 gross profit:
  - Total costs: ₹235 (9.4% drag)
  - Net P&L: ₹2,265
  - Return on ₹1.1L: 2.06%
```

---

### 1.4 Volatility-Based Strike Logic

**Optional**: Dynamically choose strike offset based on IV regime.

```
IV_30d_percentile = (current_IV - 30d_min) / (30d_max - 30d_min)

if IV_percentile < 0.33:
    offset = 0.025  # Low IV → tighter, less premium
elif IV_percentile < 0.67:
    offset = 0.035  # Medium IV → balanced
else:
    offset = 0.045  # High IV → wider, more premium
```

Output separate metrics for dynamic vs fixed strike offsets.

---

### 1.5 Backtesting Output (Per Trade)

```
date, expiry, entry_time, call_strike, put_strike, 
call_entry_premium, put_entry_premium, total_entry_credit,
call_exit_premium, put_exit_premium, total_exit_premium,
gross_pnl, brokerage_cost, stt_cost, net_pnl, 
return_pct, call_delta_entry, put_delta_entry, 
stop_loss_triggered, reason_for_exit
```

---

### 1.6 Summary Metrics (Across All Trades)

**Primary**:
- Win rate (%) = # winning trades / total trades
- Total net P&L (₹)
- Avg net P&L per trade (₹)
- Return on capital (%) = total net P&L / avg capital deployed
- Profit factor = gross wins / gross losses

**Secondary**:
- Max drawdown (₹ and %)
- Sharpe ratio
- Theta decay (₹/hour) = total premium collected / total hours held
- Cost impact (%) = total costs / total gross P&L
- Win rate by strike offset (5 breakdowns)
- Win rate by entry time (3 breakdowns)

---

### 1.7 Code Structure (3 Python Modules)

#### Module 1: `backtest_engine.py`
```python
class StrategyBacktest:
    def __init__(self, data_csv, entry_time, strike_offset, max_risk):
        # Load data, validate schema
        pass
    
    def calculate_iv_percentile(self):
        # 30-day rolling IV min/max
        pass
    
    def run_backtest(self):
        # For each day/expiry:
        #   1. Get candidate strikes (spot ± offset)
        #   2. Verify OTM at entry
        #   3. Calculate entry credit
        #   4. Simulate intraday (if target P&L hit, exit early)
        #   5. Forced exit at 3:30 PM
        #   6. Calculate costs, net P&L
        #   7. Check stop-loss triggers
        # Return trade-by-trade log + summary metrics
        pass
    
    def export_results(self, output_file):
        pass
```

#### Module 2: `estimate_greeks.py` (Optional)
```python
def black_scholes_delta(S, K, T, r, sigma):
    # Estimate delta from IV if not provided
    pass

def black_scholes_theta(S, K, T, r, sigma):
    # Estimate theta decay per day
    pass
```

#### Module 3: `reporting.py`
```python
def generate_summary_table(results):
    # Return DataFrame with win rate, return %, max DD by strike/time
    pass

def plot_equity_curve(trade_log):
    # Cumulative P&L over time
    pass

def plot_pnl_distribution(trade_log):
    # Histogram of per-trade P&L
    pass

def heatmap_strike_vs_entry_time(results):
    # 3×5 matrix: entry time × strike offset
    pass
```

---

## PART 2: FRONTEND — INTERACTIVE DASHBOARD

### 2.1 Dashboard Layout

**Screen 1: Backtesting Input & Results**

```
┌─────────────────────────────────────────────────────────────┐
│  Strangle Backtest Dashboard                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUTS (Left panel, 40% width)                             │
│  ─────────────────────────────────────────────────────      │
│  📁 Data Source:      [NSE Bhavcopy (EOD)] ▼               │
│  🎯 Instrument:       [NIFTY 50] [SENSEX]                 │
│  📊 Lookback Period:  [1 Year] ▼                           │
│  🕐 Entry Time:       [10:00 AM] ▼                         │
│  📌 Strike Offsets:   [✓2.5% ✓3% ✓3.5% ✓4% ✓4.5%]        │
│  💰 Max Risk/Trade:   [₹2,500]                             │
│  ⚙️ IV-based Strikes? [No / Yes] ▼                         │
│                                                              │
│  [Run Backtest] [Reset] [Load Sample Data]                 │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  RESULTS (Right panel, 60% width)                           │
│  ─────────────────────────────────────────────────────      │
│                                                              │
│  📈 ANALYTICAL FINDINGS BY STRIKE OFFSET                   │
│  ┌──────────────┬──────────┬──────────────┬────────┐       │
│  │Strike Offset │Win Rate %│Avg Net P&L(₹)│ROCE %  │       │
│  ├──────────────┼──────────┼──────────────┼────────┤       │
│  │±2.5%         │71%       │₹2,450        │2.04%   │       │
│  │±3.0%         │74%       │₹2,680        │2.23%   │       │
│  │±3.5%         │76%       │₹2,800        │2.33%   │       │◀ Best
│  │±4.0%         │73%       │₹2,750        │2.29%   │       │
│  │±4.5%         │69%       │₹2,600        │2.17%   │       │
│  └──────────────┴──────────┴──────────────┴────────┘       │
│                                                              │
│  Key Metrics:                                               │
│  • Backtested trades: 287                                   │
│  • Avg strategy win rate: 73%                               │
│  • Required capital: ₹2.2L (per contract)                   │
│                                                              │
│  [📊 Charts] [📋 Detailed Log] [💾 Export CSV]             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Screen 2: Risk/Reward & Strategy Comparison**

```
┌─────────────────────────────────────────────────────────────┐
│  Risk/Reward Analysis & Top Strategies                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 TOP 5 WINNING STRATEGIES (by ROCE %)                   │
│  ┌───┬──────────────┬──────────┬────────────┬────────────┐  │
│  │#  │Entry Time    │ Offset   │Win Rate %  │ROCE %     │  │
│  ├───┼──────────────┼──────────┼────────────┼────────────┤  │
│  │1  │T 10:00 AM    │ ±3.5%    │76%         │2.33%  ✅  │  │
│  │2  │T 10:00 AM    │ ±3.0%    │74%         │2.23%      │  │
│  │3  │T-1 EOD       │ ±3.5%    │71%         │2.15%      │  │
│  │4  │T 10:00 AM    │ ±4.0%    │73%         │2.13%      │  │
│  │5  │T 2:45 PM     │ ±3.0%    │70%         │1.98%      │  │
│  └───┴──────────────┴──────────┴────────────┴────────────┘  │
│                                                              │
│  💡 SCENARIO COMPARISON: Strategy A vs B                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │Strategy A (₹3k profit, ±3.5%, 10 AM)                 │  │
│  │  Gross P&L: ₹3,000                                    │  │
│  │  Costs: ₹235 (brokerage + STT)                        │  │
│  │  Net P&L: ₹2,765                                      │  │
│  │  Capital deployed: ₹1.2L                              │  │
│  │  Return: 2.30% 📊                                     │  │
│  │  Risk:Reward: 1:1.10 ✅                               │  │
│  │  Recommendation: ✅ BEST CHOICE                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │Strategy B (₹2.5k profit, ±2.5%, 10 AM)               │  │
│  │  Gross P&L: ₹2,500                                    │  │
│  │  Costs: ₹235 (brokerage + STT)                        │  │
│  │  Net P&L: ₹2,265                                      │  │
│  │  Capital deployed: ₹1.1L                              │  │
│  │  Return: 2.06%                                        │  │
│  │  Risk:Reward: 1:0.91 ⚠️                               │  │
│  │  Recommendation: ❌ AVOID (risk > reward)              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  [🔄 Run Both] [📈 Show All Combinations] [💾 Export]      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Frontend Technology Stack

**Option A: React (recommended for deployment)**
- State management: `useState` for parameters, results
- Charts: `recharts` or `plotly`
- API call: Fetch to Python backend (Flask/FastAPI)

**Option B: HTML + Vanilla JS + Chart.js**
- Lighter, no build step
- Run via simple `http-server`

**Option C: Jupyter Notebook**
- Interactive widgets via `ipywidgets`
- Good for iterative exploration

---

### 2.3 Frontend Features

1. **Input form**:
   - Dropdown: Data source, instrument, lookback period
   - Checkboxes: Strike offsets to test
   - Slider: Max risk per trade
   - Toggle: IV-based strike logic

2. **Results display**:
   - Summary table: Strike offset × win rate, avg P&L, ROCE
   - Key metrics cards: Total trades, avg win rate, required capital
   - Charts: Equity curve, P&L distribution, heatmap (strike vs entry time)

3. **Export**:
   - CSV: Trade-by-trade log, summary metrics
   - PNG: Charts

---

## PART 3: DATA SOURCING — 3 Proven Routes

### 3.1 Route 1: NSE F&O Bhavcopy (EOD Data) — **RECOMMENDED for simplicity**

**What you get**: Official NSE daily snapshots (OHLC, OI) for all options contracts.

**Where to get it**:
1. **Manual download**: https://www.nseindia.com/products/content/derivatives/equities/fohist.htm
   - Click "Historical F&O Data" → Download monthly ZIP files
   - Extract CSVs

2. **Automated via Python**:
   ```bash
   pip install nsepython
   # or
   pip install jugaad-data
   ```
   
   **Example code** (nsepython):
   ```python
   from nsepython import *
   
   # Fetch historical options data for Nifty 50
   nifty_options = nse_optchain_scrip_option(
       symbol="NIFTY", 
       expiry_date="26JAN2025", 
       instrument="OPTIDX"
   )
   
   # This returns OHLC, IV, Greeks for all strikes
   # Stitch multiple expiries into a single CSV
   ```

**Pros**:
- ✅ Free, official, reliable
- ✅ Community libraries automate the work
- ✅ EOD data only, no intraday jitter
- ✅ Includes Greeks, IV, OI

**Cons**:
- ❌ EOD only (limits T 10:00 AM and 2:45 PM entry testing)
- ❌ Slight manual wrangling to align schema

**Data structure after stitching**:
```csv
Date,Expiry,Strike,Call_Open,Call_High,Call_Low,Call_Close,Call_IV,Call_OI,Put_Open,Put_High,Put_Low,Put_Close,Put_IV,Put_OI,Spot_Close
2025-01-15,2025-01-16,23200,75.50,78.00,72.25,74.50,18.2,2340000,22.50,23.75,21.00,22.00,19.5,3450000,23547.50
```

Use `Call_Close` as both entry (previous day EOD) and exit (same day EOD).

---

### 3.2 Route 2: Free Broker APIs (Intraday Minute Data) — **BEST for 10 AM & 2:45 PM**

**Why**: Allows minute-level data → test exact entry times (10:00 AM, 2:45 PM).

#### Option A: Fyers API v3 (Completely Free)
```python
from fyers_apiv3 import fyersModel

client = fyersModel.FyersClientID(client_id="YOUR_CLIENT_ID")
# Get historical minute candles
data = client.get_history(
    symbol="NIFTYOPT23580TH2025JAN",
    resolution="1",  # 1-minute candles
    date_format="1",
    range_from="2025-01-01",
    range_to="2025-01-31",
    cont_flag="1"
)

# Returns: {t, o, h, l, c, v} for each minute
```

**Pros**:
- ✅ Completely free
- ✅ Minute-level precision
- ✅ No approval delays

**Cons**:
- ❌ Need to open Fyers demat (no cost, but account required)
- ❌ API integration takes ~2 hours first time

#### Option B: Shoonya by Finvasia (Also Free)
```python
from NorenRestApiPy.NorenRestApi import NorenApi

api = NorenApi()
api.login(userid="YOUR_ID", password="YOUR_PASS", twofa="YOUR_2FA")

# Get minute candles
candles = api.get_time_price_series(
    exchange="NFO",
    token="12345",  # NIFTY options token
    starttime="2025-01-15 10:00:00",
    endtime="2025-01-15 15:30:00",
    interval="1"  # 1-minute
)
```

**Pros**: ✅ Free, ✅ Reliable, ✅ Good documentation

**Cons**: ❌ Finvasia account required

---

### 3.3 Route 3: Platform Free Tiers (Quick Validation) — **FASTEST for proof of concept**

**AlgoTest Free Tier**:
- 25 backtests/week (free signup)
- Clean UI, minute-level data
- Runs instantly without coding

**How to use**:
1. Sign up: https://algotest.algotech.com
2. Create strategy with parameters:
   - Entry: 10:00 AM, strike = Spot ± 3.5%
   - Exit: 3:30 PM close
   - Max loss: ₹2,500
3. Backtest on Nifty weeklies (Jan 2025 onwards)
4. Compare results with your Python backtest for validation

**Pros**: ✅ Instant, ✅ Visual, ✅ No coding, ✅ Live market support

**Cons**: ❌ Limited backtests/week, ❌ Paid for production use

---

### 3.4 Data Sourcing Decision Tree

```
Do you want minute-level entry times (10 AM, 2:45 PM)?
│
├─ NO  → Use NSE Bhavcopy (EOD)
│        └─ Simpler, free, official
│
└─ YES → Use Free Broker API (Fyers or Shoonya)
         └─ More work upfront, but full precision
         
Want to validate strategy before building the full system?
│
├─ YES → Use AlgoTest free tier
│        └─ 5 minutes to see results
│
└─ NO  → Skip straight to NSE/API data engineering
```

---

## PART 4: IMPLEMENTATION ROADMAP

### Phase 1: Data Preparation (Week 1)
- [ ] Choose data source (NSE, Fyers, AlgoTest, or combination)
- [ ] Download/fetch 6–12 months of historical data
- [ ] Wrangle into CSV schema (see Part 1.1)
- [ ] Validate: 100+ rows, no NaN, correct date range

### Phase 2: Backend Development (Week 2)
- [ ] Code `backtest_engine.py` (main logic)
- [ ] Code `estimate_greeks.py` (if Greeks missing)
- [ ] Code `reporting.py` (summary metrics, charts)
- [ ] Test on sample data (5–10 rows)
- [ ] Run full backtest on 6 months data

### Phase 3: Frontend Development (Week 3)
- [ ] Choose stack (React, HTML+JS, or Jupyter)
- [ ] Build input form (dropdowns, checkboxes, sliders)
- [ ] Wire backend → frontend API
- [ ] Display results table + charts
- [ ] Build Strategy Comparison screen

### Phase 4: Validation & Tuning (Week 4)
- [ ] Compare backtest results vs AlgoTest (if used)
- [ ] Walk-forward testing (retrain monthly, check forward P&L)
- [ ] Paper trade 1 week
- [ ] Document findings, refine parameters

### Phase 5: Live Deployment (Week 5+)
- [ ] Deploy frontend (Vercel, Heroku, or local)
- [ ] Deploy backend API
- [ ] Go live with 1 contract
- [ ] Monitor vs backtest expectations
- [ ] Scale to 2–3 contracts if live matches backtest

---

## PART 5: SUCCESS CRITERIA

### Backtest Thresholds (Green Light to Trade)
✅ Win rate ≥ 70%
✅ Return ≥ 2.0% net per trade (after all costs)
✅ Profit factor ≥ 1.8
✅ Max drawdown < 10% of total capital
✅ Sharpe ratio > 1.0

### Dashboard Validation
✅ Metrics match manual trade calculations
✅ Charts are readable and informative
✅ Export CSV is importable into Excel without errors

### Live Validation
✅ Paper-traded P&L matches backtest within ±20%
✅ No "surprise" gaps or slippage
✅ Win rate holds at ≥65% (some drift expected)

---

## PART 6: FILE STRUCTURE (Minimal)

```
nifty_strangle_backtest/
│
├── README.md                    [Setup instructions, data sources]
│
├── requirements.txt             [pandas, numpy, matplotlib, scipy, flask/fastapi]
│
├── backend/
│   ├── backtest_engine.py       [Main backtesting logic]
│   ├── estimate_greeks.py       [Black-Scholes Greeks if needed]
│   └── reporting.py             [Charts, summary metrics]
│
├── frontend/
│   └── dashboard.html           [Single HTML file with embedded JS + CSS]
│   (OR)
│   └── dashboard.jsx            [React component, if using React build]
│
├── data/
│   ├── raw/
│   │   └── nifty_options_2025.csv   [Your downloaded/fetched data]
│   └── outputs/
│       ├── backtest_results.csv     [Trade-by-trade log]
│       ├── summary_metrics.txt      [Win rate, ROCE, etc.]
│       └── charts/
│           ├── equity_curve.png
│           ├── pnl_distribution.png
│           └── heatmap.png
│
└── main.py                      [CLI: Run backtest, serve frontend]
```

---

## PART 7: QUICK START (TL;DR)

### 1. Get Data (Choose ONE)
```bash
# Option A: NSE Bhavcopy (easiest)
pip install nsepython
# Then use code snippet in Part 3.1

# Option B: Fyers API (best for intraday)
pip install fyers-apiv3
# Setup account, get API key, use code in Part 3.2

# Option C: Validate with AlgoTest (fastest)
# Sign up, backtest 3 strategies, compare with your code
```

### 2. Prepare Data
```bash
# Your CSV should match Part 1.1 schema
# Minimum: 100 rows, 6+ months of data
python backend/wrangle_data.py --input raw_nifty.csv --output nifty_clean.csv
```

### 3. Run Backtest
```bash
python main.py --data nifty_clean.csv --entry-time "10:00" --strikes "0.025,0.03,0.035,0.04,0.045"
# Outputs: backtest_results.csv, charts, summary metrics
```

### 4. View Dashboard
```bash
python main.py --serve
# Opens http://localhost:5000 in browser
# Input parameters, click "Run Backtest"
# View results, export CSV
```

---

## PART 8: COMMON PITFALLS & SOLUTIONS

| Issue | Cause | Fix |
|-------|-------|-----|
| P&L values are huge (₹50k+) | Decimal point missing in data | Check: is premium ₹42.50 or ₹4250? |
| Win rate 100% or 0% | Logic bug in stop-loss or target logic | Print first 5 trades, manually verify |
| Data has gaps (missing dates) | NSE holidays, no trading | Skip those weeks, document in log |
| Greeks way off (delta > 1) | Black-Scholes assumptions wrong | Check: RFR = 6%, dividend yield = 2% |
| Frontend doesn't load | Python backend not running | Ensure `flask run` or `uvicorn main:app` |
| CSV is empty | Strike offset has no matching trades | Use ±3% if ±2.5% has no data |

---

## PART 9: COST SUMMARY (Updated Apr 1, 2026)

**Per-trade costs**:
- Brokerage: ₹160 (₹40 × 4 orders)
- STT: ~₹75 (0.15% of intrinsic value)
- **Total: ~₹235 per trade (7.8% of ₹3k profit)**

**Annual impact** (100 trades/year):
- Old structure (₹20 brokerage, 0.10% STT): ~₹118/trade → ₹11,800/year
- New structure (₹40 brokerage, 0.15% STT): ~₹235/trade → ₹23,500/year
- **Incremental cost: ~₹11,700/year (doubled)**

**Strategy viability threshold**:
- Minimum gross profit needed to break even on costs: ≥₹400/trade
- To achieve 1.5% net return: ≥₹635/trade
- To achieve 2%+ net return: ≥₹850/trade (our target)

---

## PART 10: NEXT STEPS

1. **Confirm data source** (NSE Bhavcopy, Fyers API, or AlgoTest)
2. **Download/fetch 6–12 months** of historical options data
3. **Share data sample** (first 10 rows) so I can validate schema
4. **Choose frontend tech** (React, HTML+JS, or Jupyter)
5. **Start backend development** or request code templates

**Questions before you begin?**
- Do you have historical options data ready?
- Preferred IDE? (Jupyter, VS Code, PyCharm)
- Frontend preference? (interactive web app or CLI-only)

---

**Status**: Ready to build. Let's validate data first. 🚀
