# Frontend UI Specification — Strangle Backtest Dashboard
## Detailed Component Breakdown & Interaction Flows

---

## SCREEN 1: Main Backtest Interface

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚡ Nifty/Sensex Strangle Backtest Dashboard                        │
│  Version 2.0 | Apr 1, 2026 Cost Update                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────┐  ┌──────────────────────────────────┐  │
│  │                         │  │                                   │  │
│  │  INPUT PANEL (38%)      │  │  RESULTS PANEL (62%)              │  │
│  │  ─────────────────────  │  │  ──────────────────────────────  │  │
│  │                         │  │                                   │  │
│  │  📊 Backtest Setup      │  │  📈 Analytical Findings            │  │
│  │  [Form Fields]          │  │  [Results Table]                  │  │
│  │                         │  │                                   │  │
│  │  🎯 Key Settings        │  │  📊 Comparison Table              │  │
│  │  [Checkboxes/Toggles]   │  │  [A vs B Scenarios]               │  │
│  │                         │  │                                   │  │
│  │  [Run] [Reset] [Load]   │  │  [Charts] [Export]                │  │
│  │                         │  │                                   │  │
│  └─────────────────────────┘  └──────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## DETAILED COMPONENT SPECS

### LEFT PANEL: Input Form (38% width, sticky)

#### Section 1: Data & Instrument Selection
```
┌──────────────────────────────────┐
│ 📁 DATA SOURCE                   │
├──────────────────────────────────┤
│ [NSE Bhavcopy (EOD)]        ▼    │ ← Dropdown
│                                  │
│ ℹ️ Using official EOD data        │
│    Limit: T-1 EOD entries only    │
│                                  │
│ 🎯 INSTRUMENT                    │
├──────────────────────────────────┤
│ ⦿ NIFTY 50  ○ SENSEX ○ BANKEX   │ ← Radio buttons
│                                  │
│ 📊 LOOKBACK PERIOD               │
├──────────────────────────────────┤
│ [6 Months] ▼                     │ ← Dropdown
│ (Or: 1 Year, 2 Years)            │
│ Data range: 2024-10-01 to        │
│            2025-04-01             │
└──────────────────────────────────┘
```

**UI Notes**:
- Dropdowns auto-populate based on available data
- Display date range after selection
- Show "Data loading..." spinner during file upload

#### Section 2: Entry Time & Strike Selection
```
┌──────────────────────────────────┐
│ 🕐 ENTRY TIME                    │
├──────────────────────────────────┤
│ ⦿ T-1 EOD (23.5h)               │ ← Radio, max theta
│ ⦿ T 10:00 AM (5.5h)             │ ← Recommended
│ ⦿ T 2:45 PM (45min)             │ ← Tight window
│                                  │
│ Test all 3? [✓ Run comparisons] │ ← Checkbox
│                                  │
│ 📌 STRIKE OFFSETS                │
├──────────────────────────────────┤
│ ☑ ±2.5%  ☑ ±3.0%  ☑ ±3.5%      │ ← Checkboxes
│ ☑ ±4.0%  ☑ ±4.5%                │    (select all by default)
│                                  │
│ Dynamic IV-based selection?      │
│ ○ No  ⦿ Yes [Show IV logic]      │ ← Radio + info tooltip
│                                  │
│ ℹ️ Wider offsets (±4%+) collect  │
│    more premium but higher loss   │
│    risk. Test all 5 to find edge. │
└──────────────────────────────────┘
```

**Interaction**:
- Clicking "Show IV logic" expands a box showing the algorithm
- Checkboxes are multi-select; unchecking one removes that offset from the run
- Tooltip on hover explains IV percentile logic

#### Section 3: Risk Settings
```
┌──────────────────────────────────┐
│ 💰 RISK MANAGEMENT               │
├──────────────────────────────────┤
│ Max Loss per Trade:              │
│ [₹2,500]  [Adjust slider]        │ ← Input + slider
│                                  │
│ Capital per Contract:            │
│ [₹1,20,000]  (auto-calculated)   │ ← Read-only, info only
│                                  │
│ ⚠️ EXIT RULES                    │
├──────────────────────────────────┤
│ Stop-loss triggers:              │
│ • Unrealized loss ≥ ₹2,500 → exit│
│ • |delta| > 0.35 on either leg   │
│ • 3:30 PM close (forced exit)    │
│                                  │
│ Target P&L (optional):           │
│ [30-40% of max premium]    ▼     │ ← Dropdown or % input
│                                  │
│ ℹ️ Costs (updated Apr 1, 2026):  │
│   Brokerage: ₹40/order           │
│   STT: 0.15% on intrinsic        │
│   Total: ~₹235/trade (7.8% drag) │
└──────────────────────────────────┘
```

#### Section 4: Action Buttons
```
┌──────────────────────────────────┐
│ [🚀 Run Backtest] [Reset Form]   │ ← Primary + secondary buttons
│                                  │
│ [📂 Load Sample Data]            │ ← Tertiary (for demo)
│ [📁 Upload CSV]                  │ ← File input
│                                  │
│ Status: ⊙ Ready                  │ ← Status indicator
│         ⊙ Running (5/287 trades) │ ← Progress during run
│         ✓ Complete (287 trades)  │ ← Final status
│                                  │
│ Time to backtest: 8.3 seconds    │ ← Perf metric
└──────────────────────────────────┘
```

**UI Behavior**:
- Disable "Run Backtest" button until data is loaded
- Show progress bar during backtest
- Display elapsed time
- Auto-scroll results panel when complete
- Show success/error toast notifications

---

### RIGHT PANEL: Results (62% width, scrollable)

#### Section 1: Key Metrics Cards (Top, sticky)
```
┌─────────────────────────────────────────────────────────────┐
│                    📊 DASHBOARD SUMMARY                      │
├─────────────────┬──────────────┬────────────┬──────────────┤
│ Trades Tested   │ Avg Win Rate │ Req. Cap.  │ Best ROCE    │
│     287         │    73.9%      │  ₹2.2L    │   2.33%      │
└─────────────────┴──────────────┴────────────┴──────────────┘
```

**Design**:
- 4 metric cards in a row
- Large, readable fonts (18–24px)
- Color-coded: green for positive, red for risk, blue for neutral
- Hover to show definition (tooltip)

#### Section 2: Main Results Table
```
┌──────────────────────────────────────────────────────────────┐
│  ANALYTICAL FINDINGS BY STRIKE OFFSET                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Columns: Strike Offset | Win Rate % | Avg Net Profit (₹)   │
│           | P&L Ratio | Cost Impact % | Max Drawdown %      │
│                                                              │
│ ┌─────────────┬──────────┬─────────────┬──────────┬─────────┬──────┐
│ │Strike      │Win Rate %│Avg Net P&L  │P&L Ratio │Cost %   │Max DD│
│ │Offset      │          │(₹)          │          │         │%     │
│ ├─────────────┼──────────┼─────────────┼──────────┼─────────┼──────┤
│ │±2.5%       │71%       │₹2,450       │1.76:1    │6.1%     │-3.8% │
│ │±3.0%       │74%       │₹2,680       │2.02:1    │6.9%     │-4.2% │
│ │±3.5%       │76%       │₹2,800       │2.18:1    │7.3%     │-4.6% │◄ BEST
│ │±4.0%       │73%       │₹2,750       │2.14:1    │7.7%     │-5.1% │
│ │±4.5%       │69%       │₹2,600       │1.91:1    │8.2%     │-5.8% │
│ └─────────────┴──────────┴─────────────┴──────────┴─────────┴──────┘
│
│ Legend:
│ • Green row = Best risk-adjusted performance
│ • Cost % = Total costs ÷ gross P&L (lower is better)
│ • Max DD = Largest peak-to-trough loss during backtest
│
│ [📊 Expand View] [Sort by ROCE] [Export Table as CSV]
└──────────────────────────────────────────────────────────────┘
```

**Interactions**:
- Click column header to sort (Win Rate, Avg P&L, ROCE, etc.)
- Hover over row to highlight
- Click row to expand and show trade-by-trade details for that offset
- Color-code best performer (green), worst performer (red), others (neutral)

#### Section 3: Entry Time Comparison (Tabbed)
```
┌──────────────────────────────────────────────────────────────┐
│  ENTRY TIME ANALYSIS                                          │
│  [📈 T-1 EOD] [📈 T 10:00 AM] [📈 T 2:45 PM] [🔀 Compare All]│
├──────────────────────────────────────────────────────────────┤
│  T 10:00 AM (RECOMMENDED)                                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Hold Duration:    5.5 hours (10 AM to 3:30 PM)         │ │
│  │ Avg Win Rate:     76.5%                                 │ │
│  │ Avg P&L:         ₹2,480 (net)                           │ │
│  │ Best Offset:     ±3.5% (2.33% ROCE)                     │ │
│  │ Cost Impact:     5.4% (lowest)                          │ │
│  │ Max Drawdown:    -3.2% (safest)                         │ │
│  │ Sharpe Ratio:    1.42 (excellent)                       │ │
│  │                                                          │ │
│  │ ✅ Recommendation: BEST CHOICE                           │ │
│  │    - Lowest slippage, tightest spreads                   │ │
│  │    - Most liquid entry/exit window                       │ │
│  │    - Consistent theta decay without overnight gap risk   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Tab switching**:
- Click T-1 EOD to see its metrics (max decay, overnight gap risk shown)
- Click T 2:45 PM to see tight window impact (high cost per profit ratio)
- Compare All shows all three side-by-side

---

## SCREEN 2: Strategy Comparison (Tab or Modal)

### Risk/Reward Analysis

```
┌────────────────────────────────────────────────────────────────┐
│  RISK / REWARD COMPARISON                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🏆 TOP 5 WINNING STRATEGIES (by ROCE %)                       │
│                                                                 │
│  ┌───┬──────────────────┬──────────┬──────────┬──────────────┐  │
│  │ # │ Setup            │Win Rate %│P&L (₹)   │ROCE % ★      │  │
│  ├───┼──────────────────┼──────────┼──────────┼──────────────┤  │
│  │ 1 │T 10AM, ±3.5%     │76%       │₹2,800    │2.33% ✅✅   │  │◄ BEST
│  │ 2 │T 10AM, ±3.0%     │74%       │₹2,680    │2.23%         │  │
│  │ 3 │T-1 EOD, ±3.5%    │71%       │₹2,700    │2.25%         │  │
│  │ 4 │T 10AM, ±4.0%     │73%       │₹2,750    │2.29%         │  │
│  │ 5 │T 2:45PM, ±3.0%   │70%       │₹2,100    │1.91%         │  │
│  └───┴──────────────────┴──────────┴──────────┴──────────────┘  │
│                                                                 │
│  Click strategy #1 to see: [Full trade log] [Equity curve]    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  YOUR SCENARIO: Strategy A vs Strategy B                        │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌─────────────────────────────────┐                            │
│  │   STRATEGY A (±3.5%, T 10 AM)    │                            │
│  ├─────────────────────────────────┤                            │
│  │                                  │                            │
│  │  Gross P&L:      ₹3,000          │                            │
│  │  Costs:          ₹235 (7.8%)     │                            │
│  │  ───────────────────────────     │                            │
│  │  Net P&L:        ₹2,765          │                            │
│  │                                  │                            │
│  │  Capital deployed: ₹1,20,000     │                            │
│  │  Return on capital: 2.30%        │                            │
│  │                                  │                            │
│  │  Risk:Reward:    1:1.10 ✅       │                            │
│  │  Profit Factor:  2.18 ✅         │                            │
│  │  Avg holding:    5.5 hours       │                            │
│  │  Theta decay:    ₹545/hour       │                            │
│  │                                  │                            │
│  │  ✅ VERDICT: BEST CHOICE         │                            │
│  │     - Highest return %            │                            │
│  │     - Best risk:reward ratio      │                            │
│  │     - Tight stops (delta < 0.35)  │                            │
│  │     - Proven 76% win rate         │                            │
│  │                                  │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  ┌─────────────────────────────────┐                            │
│  │   STRATEGY B (±2.5%, T 10 AM)    │                            │
│  ├─────────────────────────────────┤                            │
│  │                                  │                            │
│  │  Gross P&L:      ₹2,500          │                            │
│  │  Costs:          ₹235 (9.4%)     │                            │
│  │  ───────────────────────────     │                            │
│  │  Net P&L:        ₹2,265          │                            │
│  │                                  │                            │
│  │  Capital deployed: ₹1,10,000     │                            │
│  │  Return on capital: 2.06%        │                            │
│  │                                  │                            │
│  │  Risk:Reward:    1:0.91 ⚠️      │                            │
│  │  Profit Factor:  1.72 (weak)     │                            │
│  │  Avg holding:    5.5 hours       │                            │
│  │  Theta decay:    ₹455/hour       │                            │
│  │                                  │                            │
│  │  ❌ VERDICT: AVOID                │                            │
│  │     - Risk > Reward               │                            │
│  │     - 0.24% lower return than A   │                            │
│  │     - Tighter strikes → less      │                            │
│  │       premium collection          │                            │
│  │     - Higher cost drag (%)        │                            │
│  │                                  │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  DECISION MATRIX                                               │
│  ┌──────────────────────┬──────┬──────┬─────────┐              │
│  │Metric               │ A    │ B    │ Winner  │              │
│  ├──────────────────────┼──────┼──────┼─────────┤              │
│  │Return %             │2.30% │2.06% │ A ✅    │              │
│  │Risk:Reward          │1:1.1 │1:0.9 │ A ✅    │              │
│  │Capital efficiency   │ Low  │High  │ B       │              │
│  │Cost absorption      │Good  │Poor  │ A ✅    │              │
│  │Win rate            │76%   │71%   │ A ✅    │              │
│  │Sharpe ratio        │1.42  │0.94  │ A ✅    │              │
│  │────────────────────────────────────────────│              │
│  │OVERALL CHOICE      │  ✅✅ │  ❌  │ A WINS  │              │
│  └──────────────────────┴──────┴──────┴─────────┘              │
│                                                                 │
│  [🔄 Run Both] [📈 Full Comparison] [💾 Export Decision]      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## SCREEN 3: Charts & Visualizations

### Available Charts (Display 2–3 max, toggle via buttons)

#### Chart 1: Equity Curve (Cumulative P&L)
```
Nifty 50 | STRATEGY A (T 10AM, ±3.5%) | 1-Year Backtest

P&L (₹)
  100K  │
        │       ╱╲    ╱╲
   75K  │      ╱  ╲  ╱  ╲   ╱╲
        │     ╱    ╲╱    ╲ ╱  ╲╱
   50K  │────╱           ╲╱
        │
   25K  │  ╱╱
        │╱╱
    0K  └──────────────────────────── Time
        Jan  Feb  Mar  Apr  May  Jun

Stats:
• Total profit: ₹1,14,200
• # of trades: 287
• Avg P&L/trade: ₹2,765
• Max DD: -₹3,200 (8.4% of capital)
```

#### Chart 2: P&L Distribution (Histogram)
```
Frequency
  │       ╱╲
  │      ╱  ╲      ╱╲
  │     ╱    ╲╱╲  ╱  ╲
  │    ╱       ╲╱    ╲     ╱╲
  │   ╱              ╲────╱  ╲
  │  ╱                        ╲
  │ ╱─────────────────────────  ╲
  └─────────────────────────────────→ P&L (₹)
   -3K -2K -1K  0   1K  2K  3K  4K

Stats:
• Win: 218 trades (76%)  [Green bars]
• Loss: 69 trades (24%)  [Red bars]
• Avg Win: ₹3,625
• Avg Loss: -₹1,420
• Profit factor: 2.18:1
```

#### Chart 3: Heatmap (Strike Offset × Entry Time)
```
ROCE % by Strike Offset & Entry Time

           ±2.5%  ±3.0%  ±3.5%  ±4.0%  ±4.5%
T-1 EOD    1.85%  2.10%  2.25%  2.18%  2.02%
T 10AM     2.04%  2.23%  2.33%  2.29%  2.17%  ← Green (best)
T 2:45PM   1.64%  1.78%  1.91%  1.85%  1.72%

Color scale:
  Dark green: > 2.2%
  Light green: 2.0-2.2%
  Yellow: 1.8-2.0%
  Orange: 1.6-1.8%
  Red: < 1.6%
```

**Chart Controls**:
- `[📈 Equity Curve] [📊 P&L Dist] [🔥 Heatmap] [📋 Trade Log]` (buttons)
- Toggle between chart types
- Hover to see exact values
- Download chart as PNG

---

## SCREEN 4: Detailed Trade Log (Expandable)

```
┌────────────────────────────────────────────────────────────────┐
│  TRADE-BY-TRADE BREAKDOWN (First 10 of 287)                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌───┬────────┬──────┬──────────┬──────┬─────────┬──────────┐   │
│ │#  │ Date   │Entry │Strikes   │Entry │Exit P&L │Reason    │   │
│ │   │        │Time  │C/P       │Prem  │(₹)      │          │   │
│ ├───┼────────┼──────┼──────────┼──────┼─────────┼──────────┤   │
│ │ 1 │15Jan25 │10:00 │24200/    │81.25 │+2,850   │Target    │   │
│ │   │        │      │23100     │      │         │hit 35%   │   │
│ ├───┼────────┼──────┼──────────┼──────┼─────────┼──────────┤   │
│ │ 2 │16Jan25 │10:00 │24300/    │76.50 │+3,125   │3:30 PM   │   │
│ │   │        │      │23000     │      │         │close     │   │
│ ├───┼────────┼──────┼──────────┼──────┼─────────┼──────────┤   │
│ │ 3 │22Jan25 │10:00 │24100/    │85.00 │-2,500   │SL: loss  │   │
│ │   │        │      │23200     │      │         │hit       │   │
│ ├───┼────────┼──────┼──────────┼──────┼─────────┼──────────┤   │
│ │... │  ...   │ ...  │  ...     │ ...  │  ...    │  ...     │   │
│ └───┴────────┴──────┴──────────┴──────┴─────────┴──────────┘   │
│                                                                 │
│ Columns: Date | Entry Time | Strikes (Call/Put) | Premiums     │
│          Entry Credit | Exit Credit | Gross P&L | Costs        │
│          Net P&L | Return % | Reason for Exit                  │
│                                                                 │
│ [🔍 Expand Row 3] [⬇️ Load 10 More] [💾 Export All Trades]    │
│                                                                 │
│ Filtering: [All] [Winners] [Losers] [SL Hits]                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## EXPORT OPTIONS

### Available Exports
```
[💾 Export CSV] dropdown:
  ├─ Summary metrics (1 row, all KPIs)
  ├─ Trade log (all trades, full details)
  ├─ Strike offset comparison (5 rows)
  ├─ Entry time comparison (3 rows)
  └─ Full detailed report (multiple sheets)

[📄 Export PDF] dropdown:
  ├─ Executive summary (1 page)
  ├─ Full report with charts (5 pages)
  └─ Trade analysis (10+ pages)

[📊 Export Charts] dropdown:
  ├─ Equity curve (PNG)
  ├─ P&L distribution (PNG)
  ├─ Heatmap (PNG)
  └─ All charts zipped (ZIP)
```

---

## UX/UI PRINCIPLES

### Color Scheme
```
✅ Green (#10B981):  Winners, recommended choices, positive metrics
⚠️ Amber (#F59E0B):  Caution, average performance, info
❌ Red (#EF4444):    Losers, avoid, warnings
🔵 Blue (#3B82F6):   Primary actions, information, charts
⚪ Gray (#6B7280):   Neutral, secondary, disabled states
```

### Typography
```
Heading (h1):    24px, bold (600), primary blue
Heading (h2):    18px, bold (600), primary text
Heading (h3):    16px, semi-bold (500), primary text
Label:           12px, medium (500), secondary text
Input/Data:      14px, regular (400), primary text
Small text:      11px, regular (400), tertiary text
```

### Spacing
```
Padding:   8px, 16px, 24px, 32px
Gap:       8px, 12px, 16px, 24px
Radius:    4px, 8px, 12px (cards)
Shadow:    Light: 0 1px 2px rgba(0,0,0,0.05)
           Medium: 0 4px 6px rgba(0,0,0,0.1)
```

### Interactions
```
Hover:    Opacity +10%, shadow +1px
Active:   Accent color highlight, scale 0.98
Focus:    Blue outline (2px), box-shadow
Disabled: Opacity 50%, cursor not-allowed
Loading:  Spinner animation, disable form
Success:  Green toast, 3-sec timeout
Error:    Red toast, persistent
```

---

## RESPONSIVE DESIGN

### Breakpoints
```
Mobile (< 640px):      Stack panels vertically
Tablet (640-1024px):   2-column with narrower input
Desktop (> 1024px):    Optimal 38-62 split
```

### Mobile Layout
```
Input panel becomes 100% width at top
Results panel scrolls below
Charts take full width
Table becomes scrollable horizontally
```

---

## ACCESSIBILITY (a11y)

- All inputs have associated labels
- Color is not the only way to convey info (use icons + text)
- Keyboard navigation (Tab, Enter, Arrow keys)
- Screen reader support (ARIA labels, semantic HTML)
- Contrast ratio ≥ 4.5:1 for text
- Form validation messages are clear and actionable

---

## BROWSER SUPPORT

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest version
- Mobile browsers: iOS Safari 13+, Chrome Android

---

## PERFORMANCE TARGETS

- Page load: < 2 seconds
- Backtest run (287 trades): < 10 seconds
- Chart render: < 1 second
- CSV export: < 500ms
- Responsive to input: < 100ms

---

This completes the frontend UI specification. Ready to build.
