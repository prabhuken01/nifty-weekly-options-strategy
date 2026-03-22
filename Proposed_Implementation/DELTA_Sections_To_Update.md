# DELTA: Sections to Update in Existing Documents

**This document shows ONLY the changes needed — sections to replace or add.**

---

## 📄 DOCUMENT 1: NIFTY_Dashboard_Quick_Reference.md

### FIND & REPLACE: Section "7️⃣ How to Create Macro View + Ranking System?"

**CURRENT TEXT (to replace):**
```
### 7️⃣ **How to Create Macro View + Ranking System?**

#### The Problem
- Users overwhelmed by all options
- No clear "start here" guidance
- No way to rank combos objectively

#### The Solution: **Two-Tier System**
...
```

**NEW TEXT (replace with):**
```
### 7️⃣ **How to Create Macro View + Ranking System?**

#### The Problem
- Users overwhelmed by all options
- No clear "start here" guidance
- No way to rank combos objectively
- **NEW PROBLEM:** Don't know which Greek to focus on for each strategy
- **NEW PROBLEM:** Greeks requirements change based on Days to Expiry (DTE)

#### The Solution: **Three-Tier System (Updated)**

##### **Tier 0 (NEW): Greeks Decision Matrix**
Shows best Greek to monitor + ideal range, based on strategy + DTE

**Example:**
```
BULL CALL SPREAD (4 DTE):
├─ Best Greek: Delta (should be 0.25–0.35)
├─ Entry Time: 2 PM IST (softest IV)
├─ Why: Directional exposure matters most with time buffer
└─ Watch: If delta drifts >0.15 from entry, reassess

BULL CALL SPREAD (2 DTE):
├─ Best Greek: Gamma (should be 0.008–0.015)
├─ Entry Time: 2 PM IST
├─ Why: High gamma = breakeven pinch risk on final day
└─ Watch: If gamma spikes >2x, exit or reduce size
```

##### **Tier 1: Macro Strategy Selector** (unchanged)
Recommends which strategy based on market outlook

##### **Tier 2: Combo Ranking** (unchanged)
Auto-ranks specific combos by score

---
```

### ADD NEW SUBSECTION: After Question 7 Answer

**ADD THIS NEW CONTENT:**

```
#### 7.3 — Greeks Hierarchy by Strategy & DTE (NEW)

**Best Greeks to Monitor by Strategy:**

| Strategy | 4 DTE | 3 DTE | 2 DTE | Why |
|----------|-------|-------|-------|-----|
| **Bull Call** | Delta 0.25–0.35 | Delta 0.28–0.38 | Gamma 0.008–0.015 | Early: directional. Late: gamma pinch |
| **Bear Put** | Delta -0.24 to -0.35 | Delta -0.27 to -0.38 | Gamma 0.008–0.015 | Mirror of bull call |
| **Short Strangle** | Theta +12/day | Theta +18/day | Gamma 0.015–0.025 | Collect premium from decay |
| **Long Strangle** | Vega +25 | Vega +22 | Gamma 0.020–0.035 | Need IV spike or 2x move |
| **Bull Put** | Theta +8/day | Theta +12/day | Delta -0.15 to -0.25 | Credit decay + spot defense |
| **Iron Condor** | Theta +15/day | Theta +22/day | Vega -20 to -35 | Both-sides decay + IV crush |

**Key Insights:**
- ✅ **DTE 4:** Focus on directional Greeks (Delta for spreads, Vega for strangles)
- ✅ **DTE 3:** Theta accelerates; shift toward time-decay strategies
- ⚠️ **DTE 2:** Gamma spikes (pinch risk); consider exiting or only if profitable

**Entry Checklist (before entering ANY combo):**
1. ✓ Verify best Greek is in ideal range (from above table)
2. ✓ Entry time = 2 PM (softest IV, best spreads)
3. ✓ Market condition matches strategy (bullish for Bull Call, etc.)
4. ✓ OI > ₹80–100 Cr (liquidity)
5. ✓ Bid-ask spread < 0.5% of LTP (cost efficiency)

**Exit Rules (Greeks-aware):**
| Trigger | Action | Why |
|---------|--------|-----|
| Best Greek drifts >threshold | Reassess | Directional assumption broken |
| Profit target hit (50% of max) | Exit | Lock in gains, avoid late pinch |
| Stop loss hit (2× entry premium) | Exit | Risk management |
| Wednesday EOD | Exit | Exit before Thursday gamma explosion |
| Thursday 9:30 AM | Exit | Pre-expiry chaos (avoid) |

**Greeks-Specific Alerts:**
- **Delta alert:** If drifts ±15% from entry (directional thesis broken)
- **Theta alert:** If drops <50% of expected (early profit slowdown)
- **Gamma alert:** If spikes >2× (breakeven pinch, exit warning)
- **Vega alert:** If IV spike (long strangles exit early, short cruises)

---
```

---

## 📄 DOCUMENT 2: NIFTY_Dashboard_Strategic_Plan.md

### FIND & REPLACE: Section "# PART 7: MACRO VIEW + RANKING SYSTEM"

**LOCATION:** Sections 7.1, 7.2, 7.3

**CHANGE:** Add new subsection 7.3B after current 7.3

**NEW SUBSECTION TO ADD:**

```
## 7.3B — Greeks-Focused Combo Selection (Architecture Update)

### The Insight
Combos ranked by score, but Greeks vary wildly by DTE. A delta of 0.5 is:
- **Ideal for 4 DTE** (directional balance)
- **Too low for 3 DTE** (time decay matters more)
- **Irrelevant for 2 DTE** (gamma pinch dominates)

**Solution:** Add Greeks validation layer **before** displaying combos.

### Implementation Flow

```
User Flow (Updated):

1. User selects strategy: "Bull Call Spread"
2. Dashboard calculates DTE: 3 days remaining
3. Query Greeks config: "Bull Call 3 DTE" → "Best: Delta 0.28–0.38"
4. Generate all possible combos
5. For EACH combo:
   a) Calculate Greeks (already done)
   b) Extract best Greek value (e.g., delta = 0.32)
   c) Check if within range: 0.28 ≤ 0.32 ≤ 0.38? YES ✓
   d) Mark as "✓ Greeks ideal"
6. Calculate combo score (as before)
7. SORT by: Greeks validity (✓ > △ > ✗), then score
8. Display top 3 with:
   a) Combo strikes + premium
   b) Greeks validity badge (✓ IDEAL | △ ACCEPTABLE | ✗ AVOID)
   c) Best Greek value in chart
   d) Entry checklist (5 items)
   e) Exit rules (profit target, stop loss, time exit)
   f) Alerts (what to watch daily)
```

### Data Structure: Greeks Config Matrix

Create lookup table (in config/greeks_matrix.py):

```python
GREEKS_MATRIX = {
    'bull_call_spread': {
        4: {
            'best_greek': 'delta',
            'value_range': (0.25, 0.35),
            'why': 'Direction matters; time buffer allows some drift',
            'entry_checklist': [
                'Spot > ATM (bullish setup)',
                'Delta in range (0.25–0.35)',
                'RSI not extreme (40–70)',
                'OI > ₹100 Cr',
            ],
            'exit_rules': {
                'profit_target': 0.5,  # 50% of max
                'stop_loss': 2.0,      # 2× premium
                'time_exit': 'wed_eod',
                'alerts': ['delta_drift_0.15', 'theta_drop_50pct'],
            },
        },
        3: {
            'best_greek': 'delta',
            'value_range': (0.28, 0.38),
            'why': 'Theta accelerates; need more directional confirmation',
            # ... rest of config
        },
        2: {
            'best_greek': 'gamma',
            'value_range': (0.008, 0.015),
            'why': 'Gamma pinch risk; only enter if profitable, monitor hourly',
            # ... rest of config
        },
    },
    'bear_put_spread': {
        # ... similar structure ...
    },
    # ... other strategies ...
}
```

### Display: Greeks Validity Badge

When showing recommended combos, add Greeks validation:

```
✅ HIGHEST RECOMMENDATION (Greeks ✓ + Score 0.87)

23200 / 23400 Bull Call Spread
├─ Greeks Check: Delta 0.32 ✓ (ideal 0.28–0.38)
├─ Score: 0.87 (Delta 0.4, OI 0.3, POP 0.2, R:R 0.1)
├─ Premium: ₹85 | Max Profit: ₹115 | Max Loss: ₹85
├─ Entry Checklist:
│  ✓ Spot > ATM ✓
│  ✓ Delta in range ✓
│  ✓ RSI 48–55 ✓
│  ✓ OI ₹131 Cr ✓
├─ Exit Rules:
│  • Profit Target: 50% (₹43)
│  • Stop Loss: 2× (₹170)
│  • Time: Wednesday EOD
└─ Watch Daily: Delta drift >0.47 or <0.17 → reassess

---

⚠️ ACCEPTABLE (Greeks △ + Score 0.72)

23150 / 23350 Bull Call Spread
├─ Greeks Check: Delta 0.24 △ (ideal 0.28–0.38)
├─ Note: Slightly lower directional exposure (less premium cost)
└─ ... rest of info ...

---

❌ NOT RECOMMENDED (Greeks ✗ + Score 0.61)

23250 / 23450 Bull Call Spread
├─ Greeks Check: Delta 0.18 ✗ (ideal 0.28–0.38)
├─ Issue: Too low delta = less directional + theta loss
└─ Skip this combo
```

### Why This Matters

**Problem:** User picks best-scoring combo, but Greeks are wrong for DTE.

**Example:**
- 4 DTE: Bull Call with Delta 0.5 is "perfect balance"
- 2 DTE: Same Delta 0.5 is "too low for time decay, needs gamma focus"
- **Without Greeks matrix:** User doesn't know the setup is wrong
- **With Greeks matrix:** System flags it as △ ACCEPTABLE but not ideal

**Solution:** Greeks validation filters out mismatched combos, leaving only those with optimal Greeks for the DTE.

### Implementation Pseudocode

```python
def validate_combo_vs_greeks(combo, strategy, dte_days):
    """
    Validate if combo's Greeks match ideal for this strategy & DTE.
    
    Returns: (is_valid: bool, message: str, grade: 'A'|'B'|'C')
    """
    
    # Get Greeks config for this strategy & DTE
    config = GREEKS_MATRIX[strategy].get(dte_days)
    if not config:
        return True, "No Greeks config", 'B'  # Unknown, accept
    
    # Get best Greek for this DTE
    best_greek = config['best_greek']
    expected_range = config['value_range']
    actual_value = getattr(combo, best_greek, None)
    
    # Check if within range
    if expected_range[0] <= actual_value <= expected_range[1]:
        return True, f"✓ {best_greek} {actual_value:.2f} is ideal", 'A'
    elif abs(actual_value - expected_range[0]) < 0.05 or \
         abs(actual_value - expected_range[1]) < 0.05:
        return True, f"△ {best_greek} {actual_value:.2f} is acceptable", 'B'
    else:
        return False, f"✗ {best_greek} {actual_value:.2f} out of range", 'C'

# Usage:
for combo in all_combos:
    is_valid, msg, grade = validate_combo_vs_greeks(combo, strategy, dte_days)
    
    # Sort by grade, then by score
    combo.greeks_grade = grade
    combo.greeks_msg = msg

sorted_combos = sorted(all_combos, 
                      key=lambda c: (c.greeks_grade, -c.score))
```

---
```

### ADD TO SECTION 8.2 (Dependency Graph)

**FIND:**
```
[Parallel]:
Mobile CSS (4A)
Info guides (5A)
Liquidity ₹ (6A)
Macro selector (7A) → Ranking system (7B)
```

**REPLACE WITH:**
```
[Parallel]:
Mobile CSS (4A)
Info guides (5A)
Liquidity ₹ (6A)
Macro selector (7A) → Ranking system (7B) → Greeks Matrix (7C, NEW)

7C depends on 7B: Once ranking works, add Greeks validation layer
```

---

## 📄 DOCUMENT 3: NIFTY_Dashboard_Code_Snippets.md

### ADD NEW SECTION 7: Greeks Matrix Configuration

**ADD THIS ENTIRE NEW SECTION after "Section 6. Combo Ranking":**

```
## 7. GREEKS MATRIX & VALIDATION

### 7.1 — Greeks Matrix Configuration (New File: config/greeks_matrix.py)

```python
# config/greeks_matrix.py

from dataclasses import dataclass
from typing import Tuple, Dict, List

@dataclass
class GreeksConfig:
    """Greeks requirements for a strategy at a given DTE."""
    best_greek: str
    value_range: Tuple[float, float]
    why: str
    entry_checklist: List[str]
    exit_rules: Dict
    alert_thresholds: Dict

# === GREEKS MATRIX: Best Greek to Monitor by Strategy & DTE ===

GREEKS_MATRIX = {
    'bull_call_spread': {
        4: GreeksConfig(
            best_greek='delta',
            value_range=(0.25, 0.35),
            why='Early in week: directional (net delta) matters most. Time buffer allows some drift.',
            entry_checklist=[
                'Spot > ATM (bullish momentum confirmed)',
                'Delta 0.25–0.35 (balanced risk)',
                'RSI 40–70 (not extreme)',
                'OI > ₹100 Cr (good liquidity)',
                'Bid-ask spread < 0.5% of LTP',
            ],
            exit_rules={
                'profit_target_pct': 0.5,  # 50% of max profit
                'stop_loss_mult': 2.0,      # 2× entry premium
                'time_exit': 'wednesday_eod',
                'delta_drift_alert': 0.15,  # If delta changes ±15%
                'theta_drop_alert': 0.5,    # If theta drops >50%
            },
            alert_thresholds={
                'delta_drift': 0.15,
                'theta_drop_pct': 0.5,
            },
        ),
        3: GreeksConfig(
            best_greek='delta',
            value_range=(0.28, 0.38),
            why='Mid-week: theta accelerates. Need stronger directional conviction.',
            entry_checklist=[
                'Spot ≥ ATM (minimum bullish confirmation)',
                'Delta 0.28–0.38 (higher directional bar)',
                'Theta > -18 per day (adequate decay)',
                'Gamma < 0.010 (not too volatile yet)',
                'OI > ₹80 Cr',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 2.0,
                'time_exit': 'wednesday_eod',
                'delta_drift_alert': 0.15,
            },
            alert_thresholds={
                'delta_drift': 0.15,
                'gamma_spike_mult': 2.5,
            },
        ),
        2: GreeksConfig(
            best_greek='gamma',
            value_range=(0.008, 0.015),
            why='FINAL 2 DAYS: Gamma pinch dominates. High gamma = breakeven gets narrow. Only enter if already profitable.',
            entry_checklist=[
                '⚠️ Only enter if position already +50% profitable',
                'Gamma < 0.015 (avoid pinch)',
                'Watch every 30 minutes',
                'Be ready to exit quickly',
                'Have stop-loss set BEFORE enter',
            ],
            exit_rules={
                'profit_target_pct': 0.75,  # Be aggressive, take more off table
                'stop_loss_mult': 1.5,       # Tighter stop
                'time_exit': 'thursday_930am',  # Exit 30 min before expiry
                'gamma_spike_alert': 3.0,    # Very sensitive
            },
            alert_thresholds={
                'gamma_spike_mult': 3.0,
                'delta_drift': 0.20,
            },
        ),
    },
    
    'bear_put_spread': {
        4: GreeksConfig(
            best_greek='delta',
            value_range=(-0.35, -0.24),  # Negative = put delta
            why='Mirror of bull call. Early: directional delta on short put.',
            entry_checklist=[
                'Spot drop confirmed (bearish momentum)',
                'Delta -0.24 to -0.35 (balanced)',
                'Watch spot stay above short put',
                'RSI 30–60 (not oversold extreme)',
                'OI > ₹100 Cr',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 2.0,
                'time_exit': 'wednesday_eod',
            },
            alert_thresholds={
                'delta_drift': 0.15,
            },
        ),
        3: GreeksConfig(
            best_greek='delta',
            value_range=(-0.38, -0.27),
            why='Mid-week: need stronger bearish confirmation.',
            entry_checklist=[
                'Spot drop sustained (>1%)',
                'Delta -0.27 to -0.38',
                'Theta accelerating (>-18)',
                'Support holding below short strike',
                'OI > ₹80 Cr',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 2.0,
                'time_exit': 'wednesday_eod',
            },
            alert_thresholds={
                'delta_drift': 0.15,
                'gamma_spike_mult': 2.5,
            },
        ),
        2: GreeksConfig(
            best_greek='gamma',
            value_range=(0.008, 0.015),
            why='Final 2 days: gamma risk on short put (if spot tanks, delta explodes).',
            entry_checklist=[
                'Only if already profitable',
                'Spot well above short strike',
                'Gamma < 0.015',
                'Have tight stop-loss',
                'Monitor hourly',
            ],
            exit_rules={
                'profit_target_pct': 0.75,
                'stop_loss_mult': 1.5,
                'time_exit': 'thursday_930am',
            },
            alert_thresholds={
                'gamma_spike_mult': 3.0,
                'delta_drift': 0.20,
            },
        ),
    },
    
    'short_strangle': {
        4: GreeksConfig(
            best_greek='theta',
            value_range=(10, 15),
            why='Early week: theta is your profit machine. Collect time decay.',
            entry_checklist=[
                'Sideways market (RSI 40–60)',
                'IV rank > 50% (elevated)',
                'Theta >12 per day (reasonable)',
                'Probability of breach < 15%',
                'OI > ₹80 Cr both sides',
            ],
            exit_rules={
                'profit_target_pct': 0.5,  # Collect 50% of credit in first few days
                'stop_loss_mult': 2.0,
                'time_exit': 'wednesday_eod',
                'breach_alert': True,      # Alert if breaches either wing ±2%
            },
            alert_thresholds={
                'theta_drop_pct': 0.5,
                'breach_pct': 0.02,
            },
        ),
        3: GreeksConfig(
            best_greek='theta',
            value_range=(15, 22),
            why='Mid-week: theta ACCELERATES. Grind mode.',
            entry_checklist=[
                'Market still sideways',
                'Theta >15 per day (acceleration)',
                'Breach still unlikely (<15%)',
                'OI > ₹70 Cr',
                'Price in middle of strangle',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 2.0,
                'time_exit': 'wednesday_eod',
                'breach_alert': True,
            },
            alert_thresholds={
                'theta_drop_pct': 0.4,
                'breach_pct': 0.015,
                'gamma_spike_mult': 2.0,
            },
        ),
        2: GreeksConfig(
            best_greek='gamma',
            value_range=(0.015, 0.025),
            why='Final 2 days: gamma explosion + theta last gasp. Exit if breach.',
            entry_checklist=[
                '⚠️ Exit if breach either side (gamma pinch)',
                'Gamma watching (0.015–0.025 max)',
                'Price still in middle',
                'Ready to exit any minute',
                'Don\'t be greedy, collect 70%+ of credit',
            ],
            exit_rules={
                'profit_target_pct': 0.7,  # Be aggressive
                'stop_loss_mult': 1.5,
                'time_exit': 'thursday_930am',
                'breach_alert': True,
                'breach_exit': 'immediate',  # Exit if breach
            },
            alert_thresholds={
                'gamma_spike_mult': 3.0,
                'breach_pct': 0.01,  # Very sensitive
            },
        ),
    },
    
    'long_strangle': {
        4: GreeksConfig(
            best_greek='vega',
            value_range=(20, 30),
            why='Early: you need IV spike. Vega is your friend.',
            entry_checklist=[
                'IV rank < 30% (low IV)',
                'Vega +20 to +30 (decent leverage)',
                'No major events this week',
                'Ready for IV to spike 5%+',
                'OI > ₹70 Cr both sides',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 1.5,
                'iv_spike_exit': 5,  # If IV rises >5%, exit (take profit)
                'time_exit': 'wednesday_if_no_move',
            },
            alert_thresholds={
                'vega_loss_pct': 0.3,
                'iv_spike': 5,
            },
        ),
        3: GreeksConfig(
            best_greek='vega',
            value_range=(18, 28),
            why='Mid-week: still need IV spike OR a large move (2x+).',
            entry_checklist=[
                'Either: IV spikes incoming (events, earnings)',
                'Or: Need ≥2% move in either direction',
                'Vega +18 to +28',
                'Theta -10 to -15 (still losing daily)',
                'OI > ₹70 Cr',
            ],
            exit_rules={
                'profit_target_pct': 0.5,
                'stop_loss_mult': 1.5,
                'iv_spike_exit': 4,  # Lower threshold, more urgent
                'move_required': 2.0,  # Need 2x move by 2 DTE
                'time_exit': 'wednesday_eod',
            },
            alert_thresholds={
                'vega_loss_pct': 0.4,
                'iv_spike': 4,
            },
        ),
        2: GreeksConfig(
            best_greek='gamma',
            value_range=(0.020, 0.035),
            why='Final 2 days: Gamma + Theta race. Need BIG move NOW or exit.',
            entry_checklist=[
                '⚠️ ONLY if expecting move or IV spike TODAY',
                'Gamma 0.020–0.035 (need high leverage)',
                'Spot near either strike? EXIT.',
                'Theta working against you (-15 to -30/day)',
                'Don\'t wait for expiry, exit early if move happens',
            ],
            exit_rules={
                'profit_target_pct': 0.75,
                'stop_loss_mult': 1.0,  # Tight
                'iv_spike_exit': 3,      # Exit immediately on spike
                'move_required': 2.5,    # Need huge move
                'time_exit': 'thursday_930am',
            },
            alert_thresholds={
                'gamma_spike_mult': 3.0,
                'theta_loss_daily': 30,
            },
        ),
    },
    
    # Add more strategies as needed...
}

def get_greeks_config(strategy: str, dte_days: int) -> GreeksConfig:
    """Retrieve Greeks config for a strategy & DTE."""
    strategy_key = strategy.lower().replace(' ', '_')
    if strategy_key in GREEKS_MATRIX and dte_days in GREEKS_MATRIX[strategy_key]:
        return GREEKS_MATRIX[strategy_key][dte_days]
    return None
```

### 7.2 — Combo Greeks Validation Function

```python
def validate_combo_greeks(combo, strategy: str, dte_days: int) -> Tuple[bool, str, str]:
    """
    Validate if combo's Greeks match the ideal for this strategy & DTE.
    
    Returns:
        (is_valid, message, grade) where grade is 'A' (ideal), 'B' (acceptable), or 'C' (avoid)
    """
    
    config = get_greeks_config(strategy, dte_days)
    if config is None:
        return True, "No Greeks config for this strategy", 'B'
    
    # Get the best Greek for this DTE
    best_greek = config.best_greek
    expected_min, expected_max = config.value_range
    actual_value = getattr(combo, best_greek, None)
    
    if actual_value is None:
        return True, f"Greeks data not available", 'B'
    
    # Check if within range
    if expected_min <= actual_value <= expected_max:
        return True, f"✓ {best_greek.upper()} {actual_value:.2f} is IDEAL (range {expected_min}–{expected_max})", 'A'
    
    # Check if marginally off (within 10% of range)
    range_width = expected_max - expected_min
    if (actual_value < expected_min and actual_value >= expected_min - range_width * 0.1) or \
       (actual_value > expected_max and actual_value <= expected_max + range_width * 0.1):
        return True, f"△ {best_greek.upper()} {actual_value:.2f} is ACCEPTABLE (ideal {expected_min}–{expected_max})", 'B'
    
    # Outside acceptable range
    distance = min(abs(actual_value - expected_min), abs(actual_value - expected_max))
    return False, f"✗ {best_greek.upper()} {actual_value:.2f} is AVOID (ideal {expected_min}–{expected_max})", 'C'

# Usage:
for combo in all_combos:
    is_valid, msg, grade = validate_combo_greeks(combo, selected_strategy, dte_days)
    combo.greeks_valid = is_valid
    combo.greeks_msg = msg
    combo.greeks_grade = grade

# Sort: Greeks grade first, then score
sorted_combos = sorted(all_combos, key=lambda c: (c.greeks_grade, -c.score))
```

### 7.3 — Streamlit Display: Greeks Validation in Combo Cards

```python
# In tab6 (Trade Signals), when displaying recommended combos:

st.markdown("### 📊 Top Recommended Combos (with Greeks Validation)")

for rank, combo in enumerate(sorted_combos[:3], 1):
    # Color by Greeks grade
    color_map = {'A': '#00d4aa', 'B': '#fbbf24', 'C': '#ff6b6b'}
    color = color_map.get(combo.greeks_grade, '#6b7280')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(78,205,196,0.08), rgba(0,0,0,0.2));
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
    ">
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1.5rem; align-items: center;">
            
            <!-- Left: Combo info -->
            <div>
                <div style="color: #e2e8f0; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.4rem;">
                    🥇 Rank #{rank}: {combo.label}
                </div>
                <div style="color: #8b8fa3; font-size: 0.9rem;">
                    Buy: ₹{combo.buy_strike:,.0f} | Sell: ₹{combo.sell_strike:,.0f}
                </div>
                <div style="color: #6b7280; font-size: 0.85rem; margin-top: 0.4rem;">
                    Premium: ₹{combo.net_premium:,.0f} | Max Profit: ₹{combo.max_profit:,.0f}
                </div>
            </div>
            
            <!-- Center: Score & Greeks -->
            <div style="text-align: center;">
                <div style="color: {color}; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.4rem;">
                    Score: {combo.score:.2f}
                </div>
                <div style="color: {color}; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.4rem;">
                    {combo.greeks_grade} Grade
                </div>
                <div style="color: #6b7280; font-size: 0.75rem;">
                    {combo.greeks_msg}
                </div>
            </div>
            
            <!-- Right: Key metrics -->
            <div style="text-align: right;">
                <div style="margin-bottom: 0.5rem;">
                    <span style="color: #6b7280; font-size: 0.75rem;">POP</span><br>
                    <span style="color: #00d4aa; font-weight: 600; font-size: 0.95rem;">
                        {combo.pop:.0%}
                    </span>
                </div>
                <div>
                    <span style="color: #6b7280; font-size: 0.75rem;">R:R</span><br>
                    <span style="color: #a78bfa; font-weight: 600; font-size: 0.95rem;">
                        {combo.risk_reward:.1f}x
                    </span>
                </div>
            </div>
            
        </div>
        
        <!-- Entry Checklist (from Greeks config) -->
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
            <div style="color: #cbd5e1; font-weight: 600; margin-bottom: 0.5rem;">✓ Entry Checklist:</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; font-size: 0.85rem;">
    """, unsafe_allow_html=True)
    
    # Get entry checklist from Greeks config
    config = get_greeks_config(selected_strategy, dte_days)
    for i, item in enumerate(config.entry_checklist[:4]):  # Show first 4
        st.markdown(f"• {item}", unsafe_allow_html=False)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
```

### 7.4 — Greeks Monitoring Guide (Display in Trade Signals Tab)

```python
def show_greeks_monitoring_guide(selected_strategy, dte_days):
    """
    Display Greeks evolution chart + entry/exit rules specific to strategy & DTE.
    """
    
    st.markdown(f"### 📊 Greeks Monitoring Guide ({selected_strategy}, {dte_days} DTE)")
    
    config = get_greeks_config(selected_strategy, dte_days)
    if config is None:
        st.warning("No Greeks config for this combination")
        return
    
    # Display best Greek + range
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "🎯 Best Greek",
        config.best_greek.upper(),
        delta=f"Range: {config.value_range[0]}–{config.value_range[1]}"
    )
    col2.metric(
        "Why Monitor",
        config.why[:30] + "...",
        delta=config.why[30:]
    )
    col3.metric(
        "Entry Time",
        "2:00 PM IST",
        delta="Softest IV, best spreads"
    )
    
    # Entry checklist
    with st.expander("✓ Entry Checklist (5 items)"):
        for item in config.entry_checklist:
            st.checkbox(item)
    
    # Exit rules
    with st.expander("⏱️ Exit Rules"):
        for rule_name, rule_value in config.exit_rules.items():
            st.write(f"• **{rule_name}:** {rule_value}")
    
    # Alert thresholds
    with st.expander("⚠️ Alert Thresholds (watch these daily)"):
        for alert_name, alert_value in config.alert_thresholds.items():
            st.write(f"• **{alert_name}:** {alert_value}")

# Call in tab6:
st.markdown("---")
show_greeks_monitoring_guide(selected_strategy, dte_days)
```

---
```

---

## 📄 DOCUMENT 4: NIFTY_Dashboard_Executive_Summary.md

### ADD NEW ROW to "Your 7 Questions — Answered" table

**FIND:**
```
| **7** | Macro view + ranking system? | Decision tree + auto-score combos (4 metrics) | 🟠 **HIGH** |
```

**REPLACE WITH:**
```
| **7** | Macro view + ranking system? | Decision tree + auto-score combos (4 metrics) | 🟠 **HIGH** |
| **7.1** | Which Greek to monitor per strategy/DTE? | Greeks matrix: Delta (bull), Theta (short), Vega (long strangle) + validation | 🔴 **CRITICAL** |
```

---

## 📄 DOCUMENT 5: NIFTY_Dashboard_Quick_Reference.md

### ADD NEW TABLE after "7.3 Greeks Hierarchy" section

Create **Quick Lookup Table**:

```markdown
#### Quick Lookup: "What Greek Should I Monitor?"

**By Strategy (at 4 DTE, adjust for 3 DTE and 2 DTE):**

| Strategy | 4 DTE | 3 DTE | 2 DTE | Entry Tips |
|----------|-------|-------|-------|-----------|
| Bull Call | Δ 0.25–0.35 | Δ 0.28–0.38 | Γ 0.008–0.015 | Directional first, pinch last |
| Bear Put | Δ -0.24 to -0.35 | Δ -0.27 to -0.38 | Γ 0.008–0.015 | Mirror of bull call |
| Short Strangle | Θ +12–15/day | Θ +15–22/day | Γ 0.015–0.025 | Theta decay machine |
| Long Strangle | Ν +20–30 | Ν +18–28 | Γ 0.020–0.035 | Need IV spike or 2x move |
| Bull Put | Θ +6–10/day | Θ +10–15/day | Δ -0.15 to -0.25 | Credit decay + defense |
| Iron Condor | Θ +12–18/day | Θ +18–28/day | Ν -20 to -35 | Both-sides decay |

**Key Insight:** Last 2 DTE = Gamma dominates all strategies (pinch risk)
```

---

## 🎯 SUMMARY OF CHANGES

### Files to Update:
1. ✅ **NIFTY_Dashboard_Quick_Reference.md** — Replace Q7 answer + add Greeks table
2. ✅ **NIFTY_Dashboard_Strategic_Plan.md** — Add 7.3B subsection (Greeks validation layer)
3. ✅ **NIFTY_Dashboard_Code_Snippets.md** — Add entire Section 7 (Greeks matrix + validation)
4. ✅ **NIFTY_Dashboard_Executive_Summary.md** — Add row to 7 questions table
5. ✅ **New file created:** NIFTY_Dashboard_Greeks_Matrix_Addition.md (this file as reference)

### What's NEW (not replacing existing):
- Greeks priority matrix (config/greeks_matrix.py)
- Greeks validation function (validate_combo_greeks)
- Greeks monitoring guide (show_greeks_monitoring_guide)
- Combo Greeks validation badges (✓ A | △ B | ✗ C grades)
- Strategy-specific entry checklists & exit rules
- Alert thresholds (watch these daily)

### How It Integrates:
```
User selects strategy + DTE
    ↓
System looks up best Greek (from matrix)
    ↓
User sees recommended combos
    ↓
System validates each combo's Greeks
    ↓
Combos ranked: Greeks grade (A/B/C) > Score
    ↓
User sees top 3 with Greeks validation message
    ↓
User sees entry checklist + exit rules + alerts (from config)
    ↓
User enters trade with clear Greek to monitor
```

---

**All changes are additive (not replacing core logic), so existing backtest + ranking systems still work. This just adds a Greeks validation layer on top.**
