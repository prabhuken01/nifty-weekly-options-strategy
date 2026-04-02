# Decision Framework: Strategy A vs Strategy B

Your exact question: "3000/1.2L vs 2500/1.1L — which should I pick?"

---

## Scenario Comparison

### Strategy A: Higher Capital, Higher Absolute Profit
| Parameter | Value |
|-----------|-------|
| **Capital Deployed** | ₹1,20,000 |
| **Gross P&L Target** | ₹3,000 |
| **Brokerage** | ₹80 |
| **Estimated STT** | ₹75–₹100 |
| **Total Costs** | ₹155–₹180 |
| **Net P&L** | ₹2,820–₹2,845 |
| **Return on Capital** | **2.35–2.37%** |
| **Profit per ₹1 risked** | — |

### Strategy B: Lower Capital, Lower Absolute Profit
| Parameter | Value |
|-----------|-------|
| **Capital Deployed** | ₹1,10,000 |
| **Gross P&L Target** | ₹2,500 |
| **Brokerage** | ₹80 |
| **Estimated STT** | ₹63–₹80 |
| **Total Costs** | ₹143–₹160 |
| **Net P&L** | ₹2,340–₹2,357 |
| **Return on Capital** | **2.13–2.14%** |
| **Profit per ₹1 risked** | — |

---

## Decision Matrix

### When to Choose Strategy A (₹3k, 1.2L)
✅ **Choose A if:**
1. You observe **tighter bid-ask spreads** on the higher-premium legs (lower strike offset → more liquid)
2. Your backtest shows **better fill rates** for the ±3% or ±3.5% strikes
3. **Entry time analysis** shows 10:00 AM achieves best P&L with wider strikes
4. You have **capital efficiency** (e.g., you have ₹10L total; ₹1.2L per contract is fine)
5. **Theta decay is fastest** on the ±3% or ±4% legs (Greek analysis)
6. Your broker gives **margin concessions** on wider strangles (some brokers do)

**Expected**: 2.37% return, slightly more robust win rate at wider strikes

---

### When to Choose Strategy B (₹2.5k, 1.1L)
✅ **Choose B if:**
1. Your backtest shows **Strategy A wins turn into losses** frequently (overleveraged)
2. You want **maximum margin efficiency** (₹1.1L < ₹1.2L means more contracts fit in total capital)
3. Backtesting reveals **tighter strikes (±2.5% or ±3%)** are significantly less liquid
4. Your **max risk tolerance** is exactly ₹2,000/contract (smaller loss edge)
5. You're **risk-averse** and prefer sleeping well over 0.2–0.3% extra return
6. Historical data shows **entry at 2:45 PM is best** (tight window) — cost-sensitive

**Expected**: 2.13% return, but capital locked up more efficiently

---

## Quantitative Decision Rule

### Calculate for YOUR data:

```python
# Strategy A
return_A = (3000 - 155) / 120000 = 2.37%

# Strategy B
return_B = (2500 - 155) / 110000 = 2.13%

# Difference
diff = return_A - return_B = 0.24 percentage points

# What this means:
if num_trades_per_month == 20:
    monthly_return_A = 20 * 2.37% = 47.4%
    monthly_return_B = 20 * 2.13% = 42.6%
    monthly_advantage_A = ₹4,800 (on ₹1.2L base)
```

### Capital Efficiency Angle
```python
total_capital = 2_400_000  # ₹24 lakh for multi-contract deployment

# Strategy A approach: 20 contracts @ ₹1.2L each
contracts_A = 2_400_000 / 120_000 = 20 contracts
monthly_P&L_A = 20 * 3000 * 2.37% = ₹1,42,800

# Strategy B approach: 21-22 contracts @ ₹1.1L each
contracts_B = 2_400_000 / 110_000 = 21.8 ≈ 21 contracts
monthly_P&L_B = 21 * 2500 * 2.13% = ₹1,11,825

# Winner: Strategy A by ₹30,975 per month
```

**Insight**: If you have ₹24L capital, Strategy A (fewer, wider strangles) likely wins because 20×3k at 2.37% > 21×2.5k at 2.13%.

---

## The Theta Decay Argument (Your exact words)

> "...but I may choose latter if theta is faster in the latter..."

**This only changes the decision if:**

```
Theta_decay_rate_B >> Theta_decay_rate_A

Example:
  Strategy A theta: ₹42/hour (₹3000 profit ÷ 71 hours) = 1.25% decay/hour
  Strategy B theta: ₹58/hour (₹2500 profit ÷ 43 hours) = 1.55% decay/hour
  → Strategy B wins on "speed" even though final % is lower
```

**When would this flip the decision?**

If your backtest shows:
- **Strategy A** (wider strikes ±4%): Profit ₹3,000 but takes 60 hours (overnight + day) = ₹50/hour
- **Strategy B** (tighter strikes ±3%): Profit ₹2,500 but takes 20 hours (day-only) = ₹125/hour

Then **B is faster**, and if you can run **multiple trades/day**, B compounds better.

---

## Practical Recommendation

### Step 1: Backtest BOTH with Your Data
Run backtester with:
- Strike offset 1: ±3.5% → profits ~₹3,000 (Strategy A profile)
- Strike offset 2: ±2.5% → profits ~₹2,500 (Strategy B profile)
- All 3 entry times (T-1, 10 AM, 2:45 PM)

### Step 2: Compare Outputs
```
Metric                    | Strike ±3.5%  | Strike ±2.5%  | Winner
Win Rate                  | 73%           | 71%           | A
Avg P&L (net)            | ₹2,845        | ₹2,345        | A
Return %                 | 2.37%         | 2.13%         | A
Theta (₹/hour)           | ₹40/hr        | ₹55/hr        | B ← Faster decay
Max Drawdown             | -₹4,200       | -₹3,200       | B ← Safer
Cost Impact %            | 5.2%          | 6.2%          | A ← Cheaper
Sharpe Ratio             | 1.28          | 0.94          | A ← Smoother
```

### Step 3: Decision
- **If Sharpe(A) > 1.2 and Win Rate(A) > 72%**: Go with **A**
- **If Theta/hour(B) is 2x+ faster AND max DD(B) < half of A**: Go with **B**
- **Otherwise**: Default to **A** (higher return on deployed capital)

---

## Risk-Adjusted View

### Your Max Loss per Trade = ₹2,500 (you said this earlier)

If max loss is fixed at ₹2,500:

```
Strategy A:
  Capital deployed: ₹1.2L
  Max loss: ₹2,500 (2.08% of capital)
  Expected P&L: ₹2,845
  Risk:Reward: 2,500 : 2,845 = 1 : 1.14 ✅

Strategy B:
  Capital deployed: ₹1.1L
  Max loss: ₹2,500 (2.27% of capital)
  Expected P&L: ₹2,345
  Risk:Reward: 2,500 : 2,345 = 1 : 0.94 ❌ (Risk > Reward!)
```

**This suggests Strategy B is **riskier** — you're risking more relative to potential profit.**

**Conclusion: Strategy A is better on risk:reward.**

---

## Final Answer for YOUR Question

| Scenario | Pick | Reason |
|----------|------|--------|
| **Normal case** (balanced risk/return) | **A** | 2.37% return, better risk:reward (1:1.14) |
| **If capital is tight** (₹24L limit, optimize contracts) | **A** | More contracts fit, 20×3k > 21×2.5k |
| **If theta decay 2x+ faster on B** (rare) | **B** | Speed compounds over multiple same-day trades |
| **If B has way tighter spreads** (less cost) | **B** | Cost advantage could flip returns |
| **If you're conservative** (prefer small losses) | **B** | Tighter strikes = narrower max loss |

**TL;DR**: Go with **Strategy A (₹3k, 1.2L = 2.37%)** unless your backtest explicitly shows theta decay is dramatically faster in B or B has materially better liquidity.

---

## Next: How to Integrate This into Backtest Code

```python
# Pseudo-code structure

for offset in [0.025, 0.03, 0.035, 0.04, 0.045]:
    for entry_time in ['T-1 EOD', '10:00 AM', '2:45 PM']:
        # Run full backtest
        trades = run_backtest(data, offset, entry_time)
        
        # Calculate metrics
        gross_pnl = sum([t['gross_pnl'] for t in trades])
        costs = sum([t['brokerage'] + t['stt'] for t in trades])
        net_pnl = gross_pnl - costs
        
        capital = 1.2e5 if offset >= 0.035 else 1.1e5
        return_pct = (net_pnl / capital) / len(trades)
        
        theta_per_hour = gross_pnl / total_holding_hours
        
        # Store for comparison table
        results.append({
            'offset': offset,
            'entry_time': entry_time,
            'gross_pnl': gross_pnl,
            'costs': costs,
            'net_pnl': net_pnl,
            'return_pct': return_pct,
            'theta_per_hour': theta_per_hour,
            'win_rate': win_rate,
            'max_dd': max_drawdown,
            'sharpe': sharpe_ratio
        })

# Export comparison DataFrame
comparison_df = pd.DataFrame(results)
comparison_df.to_csv('strategy_comparison_A_vs_B.csv')
print(comparison_df.sort_values('return_pct', ascending=False))
```

This gives you the exact numbers to make the call.

---

## Example: What Good Output Looks Like

```
    offset  entry_time  gross_pnl  costs  net_pnl  return_pct  theta_per_hour  win_rate  max_dd  sharpe
0    0.035    10:00 AM   125600    4200   121400      2.37%        ₹46/hr       73%    -4.2k   1.28
1    0.040    10:00 AM   128500    4800   123700      2.42%        ₹38/hr       71%    -4.8k   1.15
2    0.025    10:00 AM   105200    3100   102100      2.13%        ₹58/hr       71%    -3.1k   0.98
3    0.045    10:00 AM   135000    5200   129800      2.49%        ₹32/hr       68%    -5.5k   1.05
4    0.035    T-1 EOD    142000    5800   136200      2.21%        ₹62/hr       72%    -5.2k   1.32
...
```

**From this output**: 
- Best absolute return: ±4.5%, 10 AM (2.49%)
- Best risk-adjusted (Sharpe): T-1 EOD (1.32)
- Best theta decay speed: ±2.5%, 10 AM (₹58/hr)

**Your call**: Pick A (2.37%) unless the speed bonus from B is compelling.

