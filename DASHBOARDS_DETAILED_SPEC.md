# Dashboard Screens: Backtesting vs Live Trading
## Complete UI/UX Specification with Update Frequencies

---

## SCREEN A: BACKTESTING DASHBOARD
### (Static analysis, batch processing, no real-time updates)

### A.1 Purpose & Context
- **When**: User is analyzing historical backtest results
- **Refresh**: **NEVER** (results are static; user clicks "Run Backtest" to recalculate)
- **Use case**: "Which strike offset & entry time worked best over the past 12 months?"

### A.2 Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│  Nifty 50 | Strangle Backtest        [⬇️ CSV] [📊 Charts] [🔄 Run] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Summary Metrics (4 cards, horizontal row)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │  287 Trades │ │ 73.9% Win   │ │ ₹1,14,200   │ │  2.31% Avg  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Main Results Table (Strike Offset vs Entry Times)                  │
│  ┌──────────┬─────────┬─────────┬─────────┬─────────┐              │
│  │ Offset   │ T-1EOD  │ T10 AM  │ T2:45PM │ AvgROCE │              │
│  ├──────────┼─────────┼─────────┼─────────┼─────────┤              │
│  │ ±2.5%    │ 68/1.85 │ 71/2.04 │ 65/1.64 │  1.84%  │              │
│  │ ±3.0%    │ 71/2.10 │ 74/2.23 │ 67/1.78 │  2.04%  │              │
│  │ ±3.5%✓   │ 72/2.25 │ 76/2.33 │ 70/1.91 │  2.16%  │ ← Highlight │
│  │ ±4.0%    │ 70/2.18 │ 73/2.29 │ 68/1.85 │  2.11%  │              │
│  │ ±4.5%    │ 68/2.02 │ 69/2.17 │ 65/1.72 │  1.97%  │              │
│  └──────────┴─────────┴─────────┴─────────┴─────────┘              │
│                                                                      │
│  [Format: Win Rate % / Return %]                                   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✓ Best: ±3.5%, T 10:00 AM (76% win, 2.33% ROCE)                  │
│  Cost/trade: ₹235 | Net from ₹3k gross: ₹2,765                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### A.3 Component Specs

#### Metric Cards (Top Row)
```
[Trades Tested]  [Win Rate]  [Total P&L]  [Avg ROCE]
    287            73.9%      ₹1,14,200    2.31%

Format:
• Background: Muted secondary color
• Label: 11px, secondary text, all-caps
• Value: 20px bold, primary text (or green if positive)
• Spacing: 12px gap between cards
• Responsive: Wrap to 2 rows on mobile
```

#### Results Table
```
Columns:
1. Strike Offset (left-aligned, sortable)
2. T-1 EOD (center, Win%/Return%)
3. T 10:00 AM (center, Win%/Return%)
4. T 2:45 PM (center, Win%/Return%)
5. Avg ROCE (center-right, largest value)

Interactions:
• Click column header to sort (Win%, Return%, ROCE)
• Hover row to highlight
• Click row to expand trade-by-trade details
• Green highlight on best performer (±3.5%)
• Red dim on worst performer (±4.5%)

Scrolling:
• Horizontal scroll on mobile
• Max-width 1400px on desktop
```

#### Info Banner
```
✓ Best: ±3.5%, T 10:00 AM
Cost/trade: ₹235 | Net from ₹3k gross: ₹2,765

Style:
• Background: Light green (#EAF3DE)
• Text: Dark green (#27500A), 12px
• Border-left: 3px solid green
• Padding: 12px
• Radius: var(--border-radius-md)
```

### A.4 Data Flow (Batch, No Updates)
```
User clicks "Run Backtest"
        ↓
Python backend processes 287 trades
        ↓
Generates summary metrics + results table
        ↓
Frontend receives JSON with results
        ↓
Renders static table + cards (ONE TIME)
        ↓
User can sort, expand, or export
        ↓
NO REFRESH until user clicks "Run" again
```

### A.5 Expected Load Time
- **Backtest execution**: 8–10 seconds (287 trades)
- **Rendering time**: <500ms
- **Total time**: ~10 seconds
- **User feedback**: Progress bar (5/287 trades...) during run

### A.6 Export Options
```
[⬇️ CSV Export]
  ├─ Summary metrics (1 row)
  ├─ Trade log (287 rows, all details)
  └─ Full detailed report (multi-sheet)

[📊 Charts]
  ├─ Equity curve (PNG)
  ├─ P&L distribution (PNG)
  ├─ Heatmap (PNG, 3×5 grid)
  └─ All combined (ZIP)
```

---

## SCREEN B: LIVE TRADING DASHBOARD
### (Real-time positions, frequent updates, fast refresh)

### B.1 Purpose & Context
- **When**: User is actively trading (market hours, 9:15 AM - 3:30 PM IST)
- **Refresh frequency**: **EVERY 5 SECONDS** (configurable: 5s, 10s, 15s)
- **Use case**: "What's my current P&L? Which positions are active? Should I enter the next trade?"

### B.2 Live Data Architecture

#### Real-Time Feeds
```
Data Source 1: Broker API (Zerodha Kite/websocket)
  • Spot price (Nifty index)
  • Option LTP (each position's call/put)
  • Greeks (delta, theta, IV)
  → Update interval: 1–2 second (throttled to every 5s for UI)

Data Source 2: Internal Database
  • Trade history (daily closed trades)
  • Entry parameters (strike, time, premium)
  • Position state (active, closed, stopped)
  → Update on every trade action (immediate)

Data Source 3: Calculated (Client-side)
  • Unrealized P&L = (entry premium - current LTP) × 100
  • Return % = P&L / capital
  • Time to close = 3:30 PM - now
  → Recalculated every 5 seconds
```

#### Update Cascade (Every 5 Seconds)
```
Tick 0s:  ┌─ Fetch latest: Spot, option LTPs, Greeks
          │
Tick 1s:  ├─ Calculate: P&L, returns, deltas
          │
Tick 2s:  ├─ Check stop-losses:
          │   • Loss ≥ ₹2,500?  → EXIT immediately
          │   • |Delta| > 0.35? → EXIT immediately
          │   • 3:30 PM close?  → FORCE EXIT
          │
Tick 3s:  ├─ Update frontend (React state)
          │
Tick 4s:  └─ Re-render UI (only changed values)

Then sleep until Tick 5s, repeat
```

### B.3 Live Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ 🔴 LIVE TRADING | Nifty Weekly      Updates: 5s | Spot: 23,547.50    │
│                                      Time: 14:42:18 IST | Daily P&L: +₹8,400
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Quick Metrics (4 cards)                                             │
│  [Active: 3] [Win Rate: 75%] [Optimal: ±3.5%] [Max DD: -₹1,850]     │
│                                                                        │
├─────────────────────────────────┬──────────────────────────────────┤
│ ACTIVE POSITIONS (3)            │ OPTIMAL STRATEGY (LIVE)          │
├─────────────────────────────────┼──────────────────────────────────┤
│                                 │                                   │
│ Trade #127 [24200C/23100P]       │ Next Entry:                      │
│ +₹2,840 (28s ago) ✓ CLOSED      │ • 24500 Call / 22900 Put         │
│ Entry: 10:00 | Δ: 0.28/-0.26    │ • Offset: ±3.5% [Approved ✓]   │
│ Target: ₹25 [████████░░] 78%    │ • IV Percentile: 68% (HIGH)      │
│ Risk: ₹2,500                     │ • Expected Premium: ₹78–82       │
│                                 │ • Theta: ₹540/hr                 │
│ Trade #128 [24300C/23000P]       │                                  │
│ +₹3,120 (12s ago) ✓ CLOSED      │ Live vs Backtest:                │
│ Entry: 10:07 | Δ: 0.31/-0.29    │ • Win Rate: 76% → 75% ✓         │
│ Target: ₹23 [█████████░] 85%    │ • ROCE: 2.33% → 2.28% ✓         │
│ Risk: ₹2,500                     │ • Max Loss: ₹2,500 → ₹1,850 ✓   │
│                                 │ • Trades: 6 done / 2 active     │
│ Trade #129 [24400C/22900P]       │                                  │
│ +₹1,440 (now) ⏱️ ACTIVE         │ Status: ✓ Live matches backtest │
│ Entry: 14:35 | Δ: 0.35/-0.32 ⚠️  │            within ±2%           │
│ Target: ₹22 [█████░░░░░] 55%    │ Action: Continue deploying      │
│ Risk: ₹2,500 | ⏱️ 55 min to 3:30 │                                  │
│                                 │                                   │
└─────────────────────────────────┴──────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ CLOSED TRADES TODAY (8)                                              │
├─────────────────────────────────────────────────────────────────────┤
│ #120 | 10:00 | 2h 15m | ₹79.50 | +₹2,840 | 2.37% ✓                │
│ #121 | 10:22 | 1h 58m | ₹74.25 | +₹2,250 | 1.88% ✓                │
│ #122 | 11:05 | 2h 02m | ₹81.75 | +₹3,100 | 2.58% ✓                │
│ #123 | 13:30 | 2h 10m | ₹76.00 | +₹2,600 | 2.17% ✓                │
│ #124 | 14:00 | 0h 42m | ₹72.50 | -₹2,500 | -2.08% ✗ (SL)          │
│ #125 | 14:25 | 1h 10m | ₹78.00 | +₹2,950 | 2.46% ✓                │
│ #126 | 15:10 | 0h 28m | ₹69.75 | +₹1,860 | 1.55% ✓                │
│ #127 | (continuing...)                                               │
└──────────────────────────────────────────────────────────────────────┘
```

### B.4 Component Specs (Live Dashboard)

#### Header (Always Visible)
```
Left:     🔴 LIVE TRADING | Nifty Weekly
Center:   Updates every 5 seconds | Spot: 23,547.50 | Time: 14:42:18 IST
Right:    Daily P&L: +₹8,400 (green if positive, red if negative)

Font:     14px bold (header), 11px secondary (subtitle)
Update:   Time updates every 5s (HH:MM:SS)
Spot:     Updates every 5s from broker API
```

#### Quick Metrics Cards
```
[Active Trades] [Today Win Rate] [Optimal Strikes] [Max Drawdown]
       3             75%             ±3.5%          -₹1,850

Colors:
• Active: Green bg (#EAF3DE)
• Win Rate: Green (if ≥70%), yellow (if 50–70%), red (if <50%)
• Optimal: Blue bg (#E6F1FB)
• Max DD: Red bg (#FCEBEB)
```

#### Active Positions Panel
```
For each active trade:

┌─ Trade #129 [24400 Call / 22900 Put]
│  Status: +₹1,440 (now) ⏱️ ACTIVE
│  Entry: 14:35 | Call Δ: 0.35 | Put Δ: -0.32 ⚠️ (delta > 0.30)
│  Target: ₹22 | Progress bar [█████░░░░░] 55%
│  Risk: ₹2,500 | Time to close: ⏱️ 55 minutes
│
│  Live updating fields:
│  • P&L: Recalc every 5s from broker API
│  • Δ: Recalc every 5s from IV + spot
│  • Progress bar: Animate smoothly as P&L changes
│  • Time: Decrement every 1s (or every 5s)
│
│  Stop-loss triggers:
│  • If P&L ≤ -₹2,500 → Turn red, show "EXIT IMMEDIATELY"
│  • If |Δ| > 0.35 → Show ⚠️ warning
│  • If time < 5 min → Show "⏱️ CRITICAL"
│
└─ Card styling:
   • Border-left: 2px solid (green if winning, blue if active, red if warning)
   • Background: Subtle (light secondary color)
   • Padding: 10px
   • Radius: var(--border-radius-md)
```

#### Optimal Strategy Panel
```
Next Entry Recommendation:

┌─ Strike: 24500 (Call) / 22900 (Put) ✓ Approved
│  Offset: ±3.5% | IV Percentile: 68% (HIGH)
│  Expected Premium: ₹78–82 | Theta: ₹540/hr
│  Matches: T 10AM, ±3.5% optimal
│
│  Data sources (updated every 5s):
│  • IV Percentile: Calculated from rolling 30-day IV history
│  • Current Spot: From broker API (updated 1–2s cadence)
│  • Theta estimate: Black-Scholes from IV + DTE
│
│  Approval logic:
│  • GREEN ✓: Matches optimal (show "APPROVED")
│  • YELLOW ⚠️: Close to optimal, but not perfect
│  • RED ✗: Deviates significantly (show "AVOID")
│
└─ Panel styling:
   • Card with subtle background
   • Show next entry parameters prominently
   • Refresh approval status every 5s
```

#### Live vs Backtest Comparison
```
Metric               | Backtest | Live | Status
─────────────────────┼──────────┼──────┼─────────
Win Rate             │ 76%      │ 75%  │ ✓ Within ±2%
Avg ROCE             │ 2.33%    │ 2.28%│ ✓ Within ±2%
Max Loss Seen        │ ₹2,500   │ -₹1,850| ✓ Better
Trades Executed      │ 287 (6mo)│ 8 (1d) │ On pace

Refresh: Every 5 seconds
Purpose: Reassure trader that live performance matches backtest
Color: Green if all metrics ✓, yellow if any drift > 3%, red if > 5%
```

#### Closed Trades Table
```
Columns: Trade # | Entry Time | Duration | Premium | P&L | Return %

Sorting: Newest first (LIFO)
Rows shown: 7–10 most recent
Scroll: Allow horizontal scroll on mobile
Colors:
  • Green text for winners (P&L > 0, Return > 1.5%)
  • Red text for losers (P&L < 0)
  • Muted gray for borderline (0 < P&L < 1.5%)
  • ⚠️ icon for SL hits

Refresh: Add new row when trade closes (immediate, not delayed)
```

### B.5 Real-Time Update Frequencies

#### By Component (Seconds)
```
Component                 | Refresh | Reason
──────────────────────────┼─────────┼─────────────────────
Spot price (header)       | 5       | Broker API (1–2s), UI batches
Time (HH:MM:SS)          | 1       | Client-side timer
P&L (active positions)    | 5       | Depends on broker API
Greeks (delta, theta)     | 5       | Calculated from IV + spot
Progress bars             | 5       | Smooth animation fill
Stop-loss checks          | 5       | Check ≤ -₹2,500 or |Δ| > 0.35
Next entry recommendation | 5       | IV percentile, theta recalc
Closed trades table       | Immediate | Add when trade closes
Daily P&L (header)        | 5       | Sum of all trade P&Ls
```

#### Why 5-Second Batching?
```
1. Broker APIs typically update 1–2 times/second
2. UI rendering every 1s causes jitter + high CPU
3. 5s batches capture movement without excessive rendering
4. Traders don't need 100ms precision for position monitoring
5. Reduces network load (fewer fetch calls)
```

#### How to Implement (React Pseudo-Code)
```javascript
useEffect(() => {
  const interval = setInterval(async () => {
    // Every 5 seconds:
    const spot = await broker.getSpot();
    const positions = await broker.getOptions(activeTrades);
    
    // Calculate in parallel
    const pnl = positions.map(p => ({
      ...p,
      unrealizedPnL: (p.entryPremium - p.currentLTP) * 100,
      delta: calculateDelta(p),
      shouldExit: calculateStopLoss(p)
    }));
    
    // Update state (triggers re-render)
    setPositions(pnl);
    setSpot(spot);
    setTime(new Date());
    
    // Check for SL hits
    pnl.forEach(p => {
      if (p.shouldExit) {
        triggerExit(p);  // Immediate action
      }
    });
  }, 5000);  // 5-second interval
  
  return () => clearInterval(interval);
}, [activeTrades]);
```

---

## B.6 Visual Feedback on Updates

#### What Changes Every 5 Seconds?
```
Stable (don't re-animate):      Updated (smooth transition):
• Card titles                    • P&L numbers (green ↑ or red ↓)
• Strike prices                  • Progress bar fill
• Entry times                    • Greeks display
• Position counts                • Time to close (decrement)
```

#### Animation Guidance
```
P&L change:
  OLD: ₹2,840
  NEW: ₹2,880
  Effect: Color flash (green) + 200ms slide-up, then settle
  Code: transition: color 200ms ease-out, transform 200ms ease-out

Progress bar:
  OLD: 78%
  NEW: 82%
  Effect: Smooth width animation (0.3s cubic-bezier)
  Code: transition: width 300ms ease-out

Avoid: Jittering, flashing, or spinning indicators
        (Unsettling for trader monitoring positions)
```

---

## B.7 Error Handling (Live Data Loss)

```
Scenario 1: Broker API down (no new data for 30 seconds)
  → Show ⚠️ warning: "Live data stale (last update 30s ago)"
  → Keep old values on screen (don't clear)
  → Suggest: "Refresh manually" or "Retry"

Scenario 2: Network latency (updates delayed)
  → Show "(update delayed)" next to time
  → Still process calculations with last known data
  → Don't block user from closing positions

Scenario 3: Calculation error (delta NaN, sigma invalid)
  → Show "—" (em-dash) instead of broken value
  → Log error; display: "Unable to calc Greeks (IV stale)"
  → User can still exit by target price, not by delta
```

---

## B.8 Mobile Responsiveness (Live Trading)

```
Desktop (> 1024px):  2-column layout (Positions | Optimal Strategy)
Tablet (640-1024px): Stack vertically (Positions → Optimal → Trades)
Mobile (< 640px):    Single column, all content flows down
                     • Active positions: Vertical cards
                     • Trades table: Horizontal scroll

Touch interactions:
  • Swipe to dismiss position card (not close trade, just UI)
  • Tap "EXIT" button to close immediately
  • Long-press position for more details (modal)
```

---

## B.9 Configuration Panel

```
User settings (accessible via gear icon):

[⚙️ SETTINGS]
├─ Refresh Rate: [5s] [10s] [15s] [30s] dropdown
├─ Alert sounds: [ON] [OFF] toggle
├─ Max risk per trade: [₹2,500] input
├─ Auto-exit at 3:30 PM: [ON] [OFF] toggle
├─ Dark mode: [ON] [OFF] toggle
└─ [Save] [Reset to defaults]

Data persistence: localStorage for user preferences
```

---

## Summary: A vs B

| Aspect | Backtesting (Screen A) | Live Trading (Screen B) |
|--------|----------------------|----------------------|
| **Refresh** | Never (static) | Every 5 seconds |
| **Data source** | CSV file (batch) | Broker API (stream) |
| **Use case** | Analyze history | Monitor active positions |
| **Real-time? ** | No | Yes |
| **User action** | Click "Run Backtest" | Watch & react |
| **Update timing** | 8–10s per run | 5s per update |
| **Scroll tables** | Yes, static | Yes, append new rows |
| **Stop-loss logic** | Post-hoc analysis | Real-time check (exit immediately) |
| **Charts** | Export PNG | Live P&L line (optional) |

---

## Implementation Checklist

### For Backtesting Dashboard
- [ ] Input form (data source, entry time, strikes)
- [ ] Summary metrics cards (4 KPIs)
- [ ] Results table (strike offset × entry time, 15 cells)
- [ ] Export buttons (CSV, charts)
- [ ] Info banner (best performer highlight)

### For Live Trading Dashboard
- [ ] Header with time, spot, daily P&L (updating every 5s)
- [ ] Quick metrics cards (4 values)
- [ ] Active positions panel (3 card stack, live P&L)
- [ ] Optimal strategy panel (next entry recommendation)
- [ ] Closed trades table (LIFO, new rows append)
- [ ] WebSocket connection to broker API
- [ ] Stop-loss checker (runs every 5s)
- [ ] Configuration panel (refresh rate, alerts, etc.)
- [ ] Error handling (data stale, API down)
- [ ] Mobile responsive design

---

This completes the specifications for both dashboards.
