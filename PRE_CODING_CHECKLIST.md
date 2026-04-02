# Pre-Coding Checklist: Nifty Strangle Backtest

**Before you write a single line of code, verify you have all these items.** This prevents false starts, missing data, and re-work.

---

## PHASE 1: Specification Clarity (5 min)

- [ ] **Read both full prompts** (nifty_strangle_backtest_prompt.md + strategy_a_vs_b_decision.md)
- [ ] **Confirm target entry times** you want tested:
  - [ ] T-1 end-of-day (3:15 PM previous day)
  - [ ] T 10:00 AM (same day)
  - [ ] T 2:45 PM (same day)
- [ ] **Confirm strike offsets** you want tested:
  - [ ] ±2.5%
  - [ ] ±3.0%
  - [ ] ±3.5%
  - [ ] ±4.0%
  - [ ] ±4.5%
- [ ] **Confirm your max risk per contract**: ₹2,500 (yes / adjust to ₹___)
- [ ] **Confirm backtest period**: ___ months / ___ year (e.g., 6 months, 1 year, 2 years)
- [ ] **Confirm output directory** where you want CSV/charts saved: ___

---

## PHASE 2: Data Readiness (10–15 min)

### Locate Your Data
- [ ] **Source identified**: 
  - [ ] NSE historical options data
  - [ ] Broker export (Zerodha/5paisa/other)
  - [ ] AlgoTest / vendor platform
  - [ ] Other: ___
- [ ] **File location**: `___________`
- [ ] **File format**: .CSV / .XLSX / .Parquet / Other: ___

### Data Quality Check
Open the file in Excel or Python and verify:
- [ ] **Column count**: Do you have at least 12+ columns? (date, expiry, spot, strike, call_ltp_entry, call_ltp_exit, call_iv_entry, call_iv_exit, put_ltp_entry, put_ltp_exit, put_iv_entry, put_iv_exit)
- [ ] **Row count**: How many rows? ___ (estimate: 100-200 per month of data)
- [ ] **Date range**: From ___ to ___ (verify it matches your backtest period)
- [ ] **Missing data**: Spot any gaps? (Yes / No — if yes, document the gaps below)
  - Gap 1: ___
  - Gap 2: ___

### Detailed Column Inspection
For each column below, mark ✅ if present, ❌ if missing, or 🤔 if unsure:
- [ ] `Date` (or `DateTime`) — calendar date, format YYYY-MM-DD
- [ ] `Expiry` — weekly expiry date, format YYYY-MM-DD
- [ ] `Spot_Close` (or `IndexValue`) — closing index value
- [ ] `Strike` — strike price (integer or float)
- [ ] `Call_LTP_Entry` (or similar) — call LTP at entry time
- [ ] `Call_LTP_Exit` (or similar) — call LTP at exit time (3:30 PM)
- [ ] `Call_IV_Entry` — call implied volatility (%) at entry
- [ ] `Call_IV_Exit` — call implied volatility (%) at exit
- [ ] `Call_Delta_Entry` — call delta at entry (optional)
- [ ] `Call_Delta_Exit` — call delta at exit (optional)
- [ ] `Call_Theta_Entry` — call theta at entry (optional)
- [ ] `Put_LTP_Entry` — put LTP at entry
- [ ] `Put_LTP_Exit` — put LTP at exit
- [ ] `Put_IV_Entry` — put IV at entry
- [ ] `Put_IV_Exit` — put IV at exit
- [ ] `Put_Delta_Entry` — put delta at entry (optional)
- [ ] `Put_Delta_Exit` — put delta at exit (optional)
- [ ] `Put_Theta_Entry` — put theta at entry (optional)
- [ ] `Volume_Call` — optional, for liquidity assessment
- [ ] `Volume_Put` — optional, for liquidity assessment

### Data Sample
Copy **the first 5 rows** from your data file here (to verify column names and data types):

```
Row 1: [paste here]
Row 2: [paste here]
Row 3: [paste here]
Row 4: [paste here]
Row 5: [paste here]
```

### Data Gaps & Notes
Are there any columns with **missing or NaN values**? List them:
- Column `___`: Missing ~___ rows out of ___
- Column `___`: Missing ~___ rows out of ___

---

## PHASE 3: Environment Setup (5 min)

### Python Version
- [ ] Python 3.8+ installed? (Check: `python --version`)
- [ ] Version: ___

### Required Libraries
Run this in your terminal to check:
```bash
pip list | grep -E "pandas|numpy|matplotlib|scipy"
```

Confirm installed (mark ✅ or run `pip install` if missing):
- [ ] `pandas` (version ___) — data manipulation
- [ ] `numpy` (version ___) — numerical computing
- [ ] `matplotlib` (version ___) — charting
- [ ] `scipy` (version ___) — Black-Scholes Greeks calculation

If any are missing, install:
```bash
pip install pandas numpy matplotlib scipy
```

### IDE / Editor
- [ ] Preferred: Jupyter / VS Code / PyCharm / Command-line / Other: ___
- [ ] Ready to run? (Yes / No — if no, set up now)

### Output Directory
- [ ] Create output folder: `mkdir ~/backtest_output` (or wherever you prefer)
- [ ] Full path: `___________`

---

## PHASE 4: Code Modules Checklist (Preparation for Step 3)

When you receive the backtesting code, you will get ~4 Python files. Verify structure:

- [ ] **`backtest_strangle.py`** — main backtest engine
  - Inputs: CSV, entry_time, strike_offset, max_risk
  - Outputs: trade_log.csv, metrics_summary.txt
  
- [ ] **`calc_iv_percentile.py`** — IV rolling window calculation
  - Input: raw options CSV
  - Output: enriched CSV with IV_30d_Percentile column
  
- [ ] **`estimate_greeks.py`** — Black-Scholes approximation (if needed)
  - Input: Spot, Strike, IV, DTE, RFR
  - Output: delta, theta, gamma
  
- [ ] **`generate_report.py`** — reporting and visualization
  - Input: trade_log.csv
  - Output: comparison_table.csv, charts (PNG)

- [ ] **`requirements.txt`** — dependency list
  - [ ] Can you run `pip install -r requirements.txt` without errors?

---

## PHASE 5: Baseline Assumptions Agreement (5 min)

### Costs (Zerodha)
- [ ] Brokerage per order: ₹20 (flat, confirmed for weeklies)
- [ ] Round-trip per contract: ₹80 (entry + exit)
- [ ] STT on exit (if ITM): 0.05% of intrinsic value (estimated ₹50–₹150)
- [ ] **Total cost assumption**: ₹130–₹230 per trade ✅

### Entry/Exit Rules
- [ ] Entry: **Sell OTM call + OTM put at spot ± X%** (strike offset parameterized)
- [ ] Exit: **Mandatory 3:30 PM same-day close** (no exceptions)
- [ ] Target: Exit at **30–40% of max premium collected** (optional, or hold to close)
- [ ] Stop-loss: **-₹2,500 per contract** or **|delta| > 0.35** per leg

### Cost Example (Your Scenario)
- [ ] Strategy A: ₹3,000 gross - ₹155 cost = ₹2,845 net (2.37% on ₹1.2L) ✅
- [ ] Strategy B: ₹2,500 gross - ₹155 cost = ₹2,345 net (2.13% on ₹1.1L) ✅

---

## PHASE 6: Test Case Preparation (Validation)

Before running the full backtest, prepare a **tiny test case** to validate the code works:

### Create a Test CSV
Create a file `test_data.csv` with **exactly 2–3 rows** covering one full day:

```csv
Date,Expiry,Spot_Close,Strike,Call_LTP_Entry,Call_LTP_Exit,Call_IV_Entry,Call_IV_Exit,Put_LTP_Entry,Put_LTP_Exit,Put_IV_Entry,Put_IV_Exit,Entry_Time
2025-01-15,2025-01-16,23500,24200,42.50,15.25,18.5,16.2,38.75,12.50,19.2,17.8,10:00
2025-01-15,2025-01-16,23500,23100,45.00,18.50,17.8,16.0,40.25,14.75,20.1,18.5,10:00
```

- [ ] Test CSV created and saved as: `___________`

### Expected Output
When you run the test:
```bash
python backtest_strangle.py --data test_data.csv --entry-time "10:00 AM" --strike-offset 0.035 --output test_results.csv
```

You should get:
- [ ] `test_results.csv` with 2 rows (one per strike)
- [ ] Columns: date, strike_call, strike_put, entry_premium, exit_premium, gross_pnl, costs, net_pnl
- [ ] Example row: `2025-01-15, 24200, 23100, 81.25, 27.75, 5350, 155, 5195`

---

## PHASE 7: Backtest Parameters Setup

Fill in your final parameters for the full backtest run:

### Backtest 1: All Combinations (Comprehensive)
```bash
python backtest_strangle.py \
  --data [your_data.csv] \
  --start-date 2024-[MM-DD] \
  --end-date 2025-[MM-DD] \
  --entry-times "T-1 EOD,10:00 AM,2:45 PM" \
  --strike-offsets "0.025,0.03,0.035,0.04,0.045" \
  --max-risk 2500 \
  --brokerage 20 \
  --stt-rate 0.0005 \
  --output comprehensive_backtest.csv
```

- [ ] Start date: ___
- [ ] End date: ___
- [ ] Output file name: ___

### Backtest 2: Strategy A Profile (₹3k, 1.2L)
```bash
python backtest_strangle.py \
  --data [your_data.csv] \
  --entry-times "10:00 AM" \
  --strike-offsets "0.035" \
  --max-risk 2500 \
  --capital-deployed 120000 \
  --output strategy_A_profile.csv
```

### Backtest 3: Strategy B Profile (₹2.5k, 1.1L)
```bash
python backtest_strangle.py \
  --data [your_data.csv] \
  --entry-times "10:00 AM" \
  --strike-offsets "0.025" \
  --max-risk 2500 \
  --capital-deployed 110000 \
  --output strategy_B_profile.csv
```

---

## PHASE 8: Success Criteria (Acceptance)

After running the backtest, you should have:

### Output Files
- [ ] `comprehensive_backtest.csv` — all 15 test combinations (3 times × 5 strikes)
- [ ] `strategy_A_profile.csv` — Strategy A deep dive
- [ ] `strategy_B_profile.csv` — Strategy B deep dive
- [ ] `comparison_table.csv` — summary table (win rate, return %, Sharpe, max DD)
- [ ] `equity_curve.png` — cumulative P&L chart
- [ ] `pnl_distribution.png` — histogram of per-trade P&L
- [ ] `heatmap_entry_vs_strike.png` — return % by entry time × strike offset

### Data Quality Checks
- [ ] Total trades backtested: ___ (expect 30–50 per strike offset)
- [ ] No NaN or error values in output
- [ ] All P&L values are numeric (₹)
- [ ] Win rate is between 0–100%
- [ ] Max drawdown is negative (₹)

### Business Logic Validation
- [ ] At least one trade per entry-time × strike-offset combination
- [ ] Costs are deducted from gross P&L
- [ ] P&L aligns with (entry premium - exit premium - costs)
- [ ] Stop-loss logic triggers when expected (loss ≥ ₹2,500 or |delta| > 0.35)

---

## PHASE 9: Red Flags (Stop & Debug)

If you see ANY of these, **stop and debug before proceeding**:

- [ ] 🚩 Huge P&L (₹50k+): Likely data error (missing decimal, wrong strike)
- [ ] 🚩 Win rate 100% or 0%: Possible logic bug (always triggering or never triggering)
- [ ] 🚩 Costs >30% of profit: Either your data or cost assumptions are wrong
- [ ] 🚩 CSV is empty: Entry time / strike offset combination has no matching data
- [ ] 🚩 Greeks way off: Black-Scholes assumptions (dividend, RFR) need adjustment
- [ ] 🚩 Back-test crashes: Likely a missing column in your data; verify column names match code

---

## PHASE 10: Next Steps (After Backtest)

- [ ] **Review comprehensive output** — which entry time + strike combo wins?
- [ ] **Compare A vs B** — does Strategy A return 2.37% as expected?
- [ ] **Check Sharpe ratio** — is it > 1.0 (good)?
- [ ] **Analyze by expiry** — does performance vary by week/month?
- [ ] **Paper trade 1 week** — test on live market data before real capital
- [ ] **Walk-forward test** — re-optimize params monthly, check for overfitting
- [ ] **Final decision** — go live with 1 contract, scale to 2–3 if live matches backtest

---

## Contact / Support

If you get stuck:

1. **Data column mismatch**: Double-check column names in your CSV match code expectations (case-sensitive)
2. **Missing Greeks**: Run `estimate_greeks.py` first; it generates them from IV
3. **Weird P&L**: Print first 5 trades, manually verify premium math (entry LTP - exit LTP = approx P&L)
4. **Crashes**: Check Python version, all libraries installed, file paths correct

---

**Status**: Ready to code? ☐ Yes, all items checked ☐ No, missing items above
