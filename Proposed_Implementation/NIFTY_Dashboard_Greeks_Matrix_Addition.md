# NIFTY Dashboard — Greeks-Focused Strategy Selection Matrix

## ADDITION TO: Quick Reference Guide (Section 7 — Macro View + Ranking System)

### NEW SECTION: 7.3 — Greeks Hierarchy by Strategy & DTE

Your dashboard should now include a **dynamic Greeks decision matrix** that recommends the best Greek to monitor based on:
- **Strategy chosen** (Bull Call, Bear Put, Long Strangle, Short Strangle, Bull Put, Iron Condor)
- **Days to Expiry** (4 DTE, 3 DTE, 2 DTE)
- **Entry time** (default 2 PM; can be adjusted)
- **Why monitor** + entry/exit tips

---

## UPDATED ARCHITECTURE: Two-Tier System (Revised)

### **Tier 0 (NEW): Greeks Decision Matrix**
Shows best Greek to monitor + entry conditions based on strategy + DTE

### **Tier 1: Macro Strategy Selector** (unchanged)
Recommends which strategy based on market outlook

### **Tier 2: Combo Ranking** (unchanged)
Auto-ranks specific combos by score

---

## BEST GREEKS SUMMARY TABLE (By Strategy & DTE)

This table should be **rendered as interactive dashboard** (not static image):

```
BULL CALL SPREAD (Mild bull, capped profit)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Delta    | Best: Delta    | Best: Gamma     | ✓ Entry 2 PM if spot > ATM
(+0.25)        | (+0.28)        | (0.012 net)     | ✓ Max profit if Nifty 25-30% above
               |                |                 | ⚠️ Watch gamma on DTE 2 (breakeven risk)
               |                |                 | ✓ Exit Wed EOD if profit > 50%

BEAR PUT SPREAD (Mild bear, capped profit)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Delta    | Best: Delta    | Best: Gamma     | ✓ Mirror of bull call
(-0.24)        | (-0.27)        | (0.011 net)     | ✓ Watch spot hold above short put
               |                |                 | ⚠️ Theta friendly if naked
               |                |                 | ✓ Exit Wed EOD if profit > 50%

LONG STRANGLE (Vol explosion play)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Vega     | Best: Vega     | Best: Gamma     | ✓ Entry when IV < 30th percentile
(+25 net)      | (+22 net)      | (0.025 total)   | ✓ Needs IV spike OR 2x+ move by 2 DTE
               |                |                 | ⚠️ Theta -₹15/day works against you
               |                |                 | ✓ Exit if 50% profit OR IV spikes 5%

SHORT STRANGLE (Range-bound theta grind)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Theta    | Best: Theta    | Best: Gamma     | ✓ Theta ramps (collect 50% of credit by 2 DTE)
(+12 per day)  | (+18 per day)  | (0.020 total)   | ✓ Exit if breach either wing (IV crush bonus)
               |                |                 | ⚠️ Gamma risk on 2 DTE — exit if breach
               |                |                 | ✓ Set alerts ±2% from shorts

BULL PUT SPREAD (Mild bull credit)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Theta    | Best: Theta    | Best: Delta     | ✓ Theta primary; delta if spot tanks
(+8 per day)   | (+12 per day)  | (-0.20 net)     | ✓ Safer than naked short
               |                |                 | ✓ Watch spot hold above short put
               |                |                 | ✓ Exit 50% profit or Wed EOD

IRON CONDOR (Neutral range)
──────────────────────────────────────────────────────────────────────────
4 DTE          | 3 DTE          | 2 DTE           | Entry Tips & Monitor
────────────────────────────────────────────────────────────────────────────
Best: Theta    | Best: Theta    | Best: Vega      | ✓ Theta machine (collect 50% by 2 DTE)
(+15 per day)  | (+22 per day)  | (-28 net)       | ✓ Vega helps on 2 DTE (IV crush bonus)
               |                |                 | ⚠️ Watch both wings (pin risk)
               |                |                 | ✓ Exit if breach or 50% profit (Wed close)

LONG STRANGLE (Same as above)
──────────────────────────────────────────────────────────────────────────
[See Long Strangle above]
```

---

## HOW TO INCORPORATE INTO DASHBOARD (Updated Architecture)

### Step 1: Add Greeks Matrix Database (New)

Create a lookup table in your config/settings.py or a new file:

```python
# config/greeks_matrix.py

GREEKS_PRIORITY_MATRIX = {
    'bull_call_spread': {
        4: {'best_greek': 'delta', 'value_range': (0.25, 0.35), 'monitor': 'Delta 25-30%'},
        3: {'best_greek': 'delta', 'value_range': (0.28, 0.38), 'monitor': 'Delta 28-38%'},
        2: {'best_greek': 'gamma', 'value_range': (0.008, 0.015), 'monitor': 'Gamma (breakeven risk)'},
    },
    'bear_put_spread': {
        4: {'best_greek': 'delta', 'value_range': (-0.35, -0.24), 'monitor': 'Put Delta -24 to -35%'},
        3: {'best_greek': 'delta', 'value_range': (-0.38, -0.27), 'monitor': 'Put Delta -27 to -38%'},
        2: {'best_greek': 'gamma', 'value_range': (0.008, 0.015), 'monitor': 'Gamma (breakeven risk)'},
    },
    'long_strangle': {
        4: {'best_greek': 'vega', 'value_range': (20, 30), 'monitor': 'Vega +20 to +30'},
        3: {'best_greek': 'vega', 'value_range': (18, 28), 'monitor': 'Vega +18 to +28'},
        2: {'best_greek': 'gamma', 'value_range': (0.020, 0.035), 'monitor': 'Gamma (move required)'},
    },
    'short_strangle': {
        4: {'best_greek': 'theta', 'value_range': (10, 15), 'monitor': 'Theta +10 to +15 per day'},
        3: {'best_greek': 'theta', 'value_range': (15, 22), 'monitor': 'Theta +15 to +22 per day'},
        2: {'best_greek': 'gamma', 'value_range': (0.015, 0.025), 'monitor': 'Gamma (pin risk)'},
    },
    'bull_put_spread': {
        4: {'best_greek': 'theta', 'value_range': (6, 10), 'monitor': 'Theta +6 to +10 per day'},
        3: {'best_greek': 'theta', 'value_range': (10, 15), 'monitor': 'Theta +10 to +15 per day'},
        2: {'best_greek': 'delta', 'value_range': (-0.25, -0.15), 'monitor': 'Delta if spot tanks'},
    },
    'iron_condor': {
        4: {'best_greek': 'theta', 'value_range': (12, 18), 'monitor': 'Theta +12 to +18 per day'},
        3: {'best_greek': 'theta', 'value_range': (18, 28), 'monitor': 'Theta +18 to +28 per day'},
        2: {'best_greek': 'vega', 'value_range': (-35, -20), 'monitor': 'Vega (IV crush helps)'},
    },
}

ENTRY_CONDITIONS = {
    'bull_call_spread': {
        'entry_time': '14:00',  # 2 PM
        'market_condition': 'bullish',
        'min_spot_above_atm_pct': 0.01,  # 1% above ATM
        'exit_rules': {
            'profit_target': 0.5,  # 50% of max profit
            'stop_loss': 2.0,  # 2x entry premium
            'time_exit': 'wednesday_eod',  # Wed EOD
        }
    },
    'bear_put_spread': {
        'entry_time': '14:00',
        'market_condition': 'bearish',
        'max_spot_drop_pct': 0.02,  # Watch if drops >2%
        'exit_rules': {
            'profit_target': 0.5,
            'stop_loss': 2.0,
            'time_exit': 'wednesday_eod',
        }
    },
    'long_strangle': {
        'entry_time': '14:00',
        'market_condition': 'high_volatility_low_iv',  # Enter when IV low
        'iv_rank_max': 30,  # Enter when IV rank < 30%
        'exit_rules': {
            'profit_target': 0.5,
            'stop_loss': 1.5,
            'iv_spike_exit': 5,  # Exit if IV spikes 5%
            'move_required': 2.0,  # Need 2x move by 2 DTE
        }
    },
    'short_strangle': {
        'entry_time': '14:00',
        'market_condition': 'sideways',
        'iv_rank_min': 50,  # Enter when IV elevated
        'exit_rules': {
            'profit_target': 0.5,
            'breach_exit': True,  # Exit if breaches either wing
            'time_exit': 'wednesday_eod',
        }
    },
    'bull_put_spread': {
        'entry_time': '14:00',
        'market_condition': 'mildly_bullish',
        'exit_rules': {
            'profit_target': 0.5,
            'stop_loss': 2.0,
            'time_exit': 'wednesday_eod',
        }
    },
    'iron_condor': {
        'entry_time': '14:00',
        'market_condition': 'neutral_range',
        'iv_rank_min': 50,
        'exit_rules': {
            'profit_target': 0.5,
            'breach_exit': True,
            'time_exit': 'wednesday_eod',
        }
    },
}

# Monitor thresholds (alert user if Greek moves outside safe range)
GREEK_ALERT_THRESHOLDS = {
    'delta': {'acceptable_drift': 0.15},  # 15% absolute change triggers alert
    'gamma': {'acceptable_drift': 0.005},  # 0.005 absolute change
    'theta': {'acceptable_drift': 5},  # 5 rupees per day change
    'vega': {'acceptable_drift': 3},  # 3 rupees per 1% IV change
}
```

### Step 2: Add Greeks Monitor Table to Trade Signals Tab

In **tab6 (Trade Signals)** — Add this after combo ranking:

```python
# NEW FUNCTION: Display Greeks-focused entry conditions

def show_greeks_monitoring_guide(selected_strategy, dte_days, entry_time='14:00'):
    """
    Show best Greek to monitor + entry conditions for chosen strategy.
    """
    
    st.markdown("### 🎯 Greeks Monitoring Guide")
    st.markdown(f"**Strategy:** {selected_strategy} | **DTE:** {dte_days}d | **Entry Time:** {entry_time} IST")
    
    # Get Greeks priority for this strategy and DTE
    strategy_key = selected_strategy.lower().replace(' ', '_')
    greeks_config = GREEKS_PRIORITY_MATRIX.get(strategy_key, {})
    entry_config = ENTRY_CONDITIONS.get(strategy_key, {})
    
    if dte_days in greeks_config:
        greek_info = greeks_config[dte_days]
        
        # Display best Greek to monitor
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🎯 Best Greek to Monitor",
                greek_info['best_greek'].upper(),
                delta=f"Focus: {greek_info['monitor']}"
            )
        
        with col2:
            st.metric(
                "Expected Range",
                f"{greek_info['value_range'][0]} to {greek_info['value_range'][1]}",
                delta="Ideal for this DTE"
            )
        
        with col3:
            st.metric(
                "Entry Time",
                entry_config.get('entry_time', '14:00'),
                delta="2 PM IST (softest IV)"
            )
        
        with col4:
            st.metric(
                "Market Condition",
                entry_config.get('market_condition', 'varies').title(),
                delta="Optimal setup"
            )
        
        st.markdown("---")
        
        # Entry Rules Card
        st.markdown("#### 📋 Entry Conditions & Rules")
        
        entry_html = f"""
        <div style="background: rgba(78,205,196,0.08); border: 1px solid rgba(78,205,196,0.3); 
                    border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                
                <div>
                    <h5 style="color: #e2e8f0; margin-top: 0;">✓ Entry Checklist</h5>
                    <ul style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.8;">
        """
        
        # Dynamic entry checklist based on strategy
        if 'bull' in selected_strategy.lower():
            entry_html += """
                        <li>✓ Spot > ATM (bullish momentum confirmed)</li>
                        <li>✓ RSI 40–70 range (not extreme)</li>
                        <li>✓ Delta 0.25–0.35 range (balanced risk)</li>
                        <li>✓ OI > ₹100 Cr (liquid strikes)</li>
            """
        elif 'bear' in selected_strategy.lower():
            entry_html += """
                        <li>✓ Spot drop confirmed (bearish momentum)</li>
                        <li>✓ RSI 30–60 range (not extreme)</li>
                        <li>✓ Delta -0.24 to -0.35 (balanced)</li>
                        <li>✓ Watch spot hold above short put</li>
            """
        elif 'strangle' in selected_strategy.lower():
            entry_html += """
                        <li>✓ IV rank (check sidebar config)</li>
                        <li>✓ Probability of breach < 20%</li>
                        <li>✓ OI > ₹80 Cr both wings</li>
                        <li>✓ Spreads tight (< 0.5% bid-ask)</li>
            """
        
        entry_html += """
                    </ul>
                </div>
                
                <div>
                    <h5 style="color: #e2e8f0; margin-top: 0;">⏱️ Exit Rules</h5>
                    <ul style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.8;">
        """
        
        exit_rules = entry_config.get('exit_rules', {})
        entry_html += f"""
                        <li><strong>Profit Target:</strong> {exit_rules.get('profit_target', 0.5)*100:.0f}% of max profit</li>
                        <li><strong>Stop Loss:</strong> {exit_rules.get('stop_loss', 2.0):.1f}× entry premium</li>
                        <li><strong>Time Exit:</strong> {exit_rules.get('time_exit', 'Thursday 9:30 AM').title()}</li>
        """
        
        if 'iv_spike_exit' in exit_rules:
            entry_html += f"<li><strong>IV Spike:</strong> Exit if IV moves {exit_rules['iv_spike_exit']}%</li>"
        
        entry_html += """
                    </ul>
                </div>
                
            </div>
        </div>
        """
        
        st.markdown(entry_html, unsafe_allow_html=True)
        
        # Greeks Evolution Chart
        st.markdown("#### 📈 Expected Greeks Evolution (Mon → Thu)")
        
        # Simulate Greeks evolution for this DTE trajectory
        dte_array = np.arange(dte_days, 0, -1)
        best_greek = greek_info['best_greek']
        
        if best_greek == 'theta':
            # Theta accelerates
            greek_values = [10 * (dte_days / dte) ** 1.5 for dte in dte_array]
            greek_label = 'Theta (₹ per day)'
        elif best_greek == 'delta':
            # Delta drifts slightly
            greek_values = [0.30 + 0.02 * np.sin(i) for i in range(len(dte_array))]
            greek_label = 'Delta'
        elif best_greek == 'gamma':
            # Gamma accelerates last 2 days
            greek_values = [0.002 * (dte_days / dte) ** 2 for dte in dte_array]
            greek_label = 'Gamma'
        else:  # vega
            # Vega stable, then spikes on events
            greek_values = [20 + 2 * i for i in range(len(dte_array))]
            greek_label = 'Vega'
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[f"{d}d to expiry" for d in dte_array],
            y=greek_values,
            mode='lines+markers',
            name=best_greek.upper(),
            line=dict(width=3, color='#00d4aa'),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(0,212,170,0.2)',
        ))
        
        fig.update_layout(
            title=f"{best_greek.upper()} Evolution ({selected_strategy})",
            xaxis_title='Days to Expiry',
            yaxis_title=greek_label,
            template='plotly_dark',
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15,12,41,0.5)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Highlight Greeks to Watch
        st.markdown("#### ⚠️ Critical Greeks Checkpoints")
        
        checkpoints = {
            'delta': "✓ If delta drifts >0.15 from entry, adjust or exit (directional exposure changed)",
            'theta': "✓ If theta drops <50% of expected, consider exiting early (profit slowing)",
            'gamma': "✓ If gamma spikes >2x, reduce size or exit (breakeven pinch risk on 2 DTE)",
            'vega': "✓ If IV rises unexpectedly, exit long strangles early (cost increases); accept bear in short (bonus)",
        }
        
        st.markdown(f"""
        <div style="background: rgba(255,107,107,0.08); border-left: 4px solid #ff6b6b; 
                    border-radius: 8px; padding: 1rem;">
            <strong>{best_greek.upper()} Focus:</strong> {checkpoints.get(best_greek, "Monitor changes")}
        </div>
        """, unsafe_allow_html=True)
```

### Step 3: Integrate into Combo Selection

When showing recommended combos, add Greeks validation:

```python
def validate_combo_greeks(combo, selected_strategy, dte_days):
    """
    Check if combo's Greeks match the ideal range for this strategy & DTE.
    """
    
    strategy_key = selected_strategy.lower().replace(' ', '_')
    greeks_config = GREEKS_PRIORITY_MATRIX.get(strategy_key, {})
    
    if dte_days not in greeks_config:
        return True, "N/A"
    
    greek_info = greeks_config[dte_days]
    best_greek = greek_info['best_greek']
    expected_range = greek_info['value_range']
    
    # Get actual Greek value from combo
    actual_value = getattr(combo, best_greek, None)
    
    if actual_value is None:
        return True, "Greeks data unavailable"
    
    # Check if within range
    in_range = expected_range[0] <= actual_value <= expected_range[1]
    
    if in_range:
        return True, f"✓ {best_greek.upper()} {actual_value:.2f} is ideal"
    else:
        deviation = min(abs(actual_value - expected_range[0]), 
                       abs(actual_value - expected_range[1]))
        return False, f"⚠️ {best_greek.upper()} {actual_value:.2f} outside ideal {expected_range}"

# When displaying combos:
for combo in top_combos:
    is_valid, greeks_msg = validate_combo_greeks(combo, selected_strategy, dte_days)
    
    color = '#00d4aa' if is_valid else '#fbbf24'
    
    st.markdown(f"""
    <div style="border-left: 4px solid {color}; padding: 0.5rem; margin: 0.5rem 0;">
        {greeks_msg}
    </div>
    """, unsafe_allow_html=True)
```

---

## UPDATED: Quick Reference (Question 2 Modification)

### 2️⃣ **Point-in-Time Greeks + Strategy-Specific Monitoring**

**Problem:** You don't know which Greek to focus on for each strategy and how many DTE are left.

**Solution:** 
1. Store Greeks time-series (same as before)
2. **Add strategy-specific Greek hierarchy** (new):
   - Bull Call → Monitor **Delta** (0.25–0.35 range for 4 DTE, shift to Gamma on 2 DTE)
   - Bear Put → Monitor **Delta** (negative, -0.24 to -0.35)
   - Short Strangle → Monitor **Theta** (accelerates Mon→Wed, watch Gamma on 2 DTE)
   - Long Strangle → Monitor **Vega** (IV spike profit, Gamma for move)
   - Bull Put → Monitor **Theta** first, Delta second
   - Iron Condor → Monitor **Theta** (both sides), Vega bonus on 2 DTE

3. **Add entry checkpoints** (new):
   - ✓ Right Greek in right range
   - ✓ Entry time: 2 PM (softest IV)
   - ✓ Market condition matches strategy
   - ✓ Liquidity OK

4. **Add exit alerts** (new):
   - Greeks drift >threshold → warning
   - Profit target hit → take profit
   - Time-based exit → Wed EOD or Thu 9:30 AM

**Implementation:**
- config/greeks_matrix.py (lookup table of best Greeks per strategy/DTE)
- entry_conditions (what to check before entering)
- Monitor alerts (watch out for these changes)

**Display:** Before showing combos, display Greeks monitoring guide with:
- Best Greek for this combo + DTE
- Expected range for this Greek
- Charts showing Greek evolution (Mon→Thu)
- Entry checklist
- Exit rules
- Critical checkpoints

---

## UPDATED: Strategic Plan (Section 7 Modification)

### Section 7.3B — Greeks-Focused Combo Selection (NEW)

**Add this subsection to Strategic Plan, Section 7:**

Instead of just ranking combos by score, add a **Greeks validation layer**:

```
Combo Selection Flow (Revised):

1. User selects strategy: Bull Call Spread
2. System detects DTE: 3 days
3. Look up best Greek: DELTA (from matrix)
4. Look up expected range: 0.28–0.38
5. Generate combos
6. For each combo:
   - Calculate Greeks
   - Check if best Greek is in range
   - If YES: mark ✓ (recommended)
   - If NO: mark △ (acceptable) or ✗ (avoid)
7. Rank by combo score (as before)
8. Display with Greeks indicator
9. Show Greeks evolution chart
10. Show entry/exit checklist
```

**Why this matters:**
- ✅ User enters combos with optimal Greeks for that DTE (not just generic scoring)
- ✅ Knows which Greek to watch hourly (Delta, Theta, Gamma, or Vega)
- ✅ Gets alerts if Greeks drift >threshold
- ✅ Understands why this combo is better: "Higher Delta = more directional, right for bullish 3 DTE"
- ✅ Knows exact exit conditions (profit target, time, Greeks alert)

**Example output:**
```
Recommended Combo: 23200 buy / 23400 sell (Bull Call, 3 DTE)

✓ Greeks Check: Delta 0.32 (ideal range 0.28–0.38)
✓ Score: 0.84 (HIGHLY RECOMMENDED)
✓ Entry Checklist:
  • Spot > ATM ✓
  • RSI 40–70 ✓
  • OI > ₹100 Cr ✓

Exit Rules:
  • Profit Target: 50% (₹150)
  • Stop Loss: 2× premium (₹200)
  • Time: Wed EOD

⚠️ Watch Daily: If Delta drifts >0.47 or <0.17, reassess
```

---

## UPDATED: Code Snippets (Greeks Matrix Section)

Add this to Code Snippets document:

```python
# File: config/greeks_matrix.py — Strategy-specific Greeks monitoring

from dataclasses import dataclass
from typing import Tuple, Dict

@dataclass
class GreeksMonitor:
    """Configuration for Greeks monitoring per strategy & DTE."""
    
    strategy: str
    dte: int
    best_greek: str
    value_range: Tuple[float, float]
    entry_checklist: list
    exit_rules: dict
    alert_thresholds: dict
    
def get_greeks_config(strategy: str, dte_days: int) -> GreeksMonitor:
    """
    Return Greeks monitoring config for a strategy & DTE.
    
    Args:
        strategy: 'bull_call_spread', 'bear_put_spread', etc.
        dte_days: 4, 3, or 2 days to expiry
    
    Returns:
        GreeksMonitor config object
    """
    
    config_map = {
        'bull_call_spread': {
            4: GreeksMonitor(
                strategy='bull_call_spread',
                dte=4,
                best_greek='delta',
                value_range=(0.25, 0.35),
                entry_checklist=[
                    'Spot > ATM (bullish momentum)',
                    'Delta 0.25–0.35 (balanced)',
                    'RSI 40–70 (not extreme)',
                    'OI > ₹100 Cr (liquid)',
                ],
                exit_rules={
                    'profit_target_pct': 0.5,
                    'stop_loss_mult': 2.0,
                    'time_exit': 'wednesday_eod',
                    'delta_alert': 0.15,
                },
                alert_thresholds={
                    'delta_drift': 0.15,
                    'theta_drop_pct': 0.5,
                    'gamma_spike_mult': 2.0,
                },
            ),
            3: GreeksMonitor(
                strategy='bull_call_spread',
                dte=3,
                best_greek='delta',
                value_range=(0.28, 0.38),
                entry_checklist=[
                    'Spot ≥ ATM',
                    'Delta 0.28–0.38',
                    'Gamma < 0.01',
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
            2: GreeksMonitor(
                strategy='bull_call_spread',
                dte=2,
                best_greek='gamma',
                value_range=(0.008, 0.015),
                entry_checklist=[
                    'Only if already profitable',
                    'Gamma alert (breakeven pinch)',
                    'Consider closing early',
                    'Watch every 30 min',
                ],
                exit_rules={
                    'profit_target_pct': 0.75,  # Take more off the table
                    'stop_loss_mult': 1.5,
                    'time_exit': 'thursday_930am',
                },
                alert_thresholds={
                    'gamma_spike_mult': 3.0,  # Very sensitive
                    'delta_drift': 0.20,
                },
            ),
        },
        # ... add other strategies similarly ...
    }
    
    if strategy in config_map and dte_days in config_map[strategy]:
        return config_map[strategy][dte_days]
    else:
        return None

# Usage in dashboard:

selected_strategy = 'bull_call_spread'
dte = 3

greeks_config = get_greeks_config(selected_strategy, dte)

if greeks_config:
    st.metric("Best Greek to Monitor", greeks_config.best_greek.upper())
    st.metric("Ideal Range", f"{greeks_config.value_range[0]} to {greeks_config.value_range[1]}")
    
    with st.expander("Entry Checklist"):
        for item in greeks_config.entry_checklist:
            st.checkbox(item)
    
    with st.expander("Exit Rules"):
        for rule_name, rule_value in greeks_config.exit_rules.items():
            st.write(f"• {rule_name}: {rule_value}")
```

---

## SUMMARY: What Changed

### Documents to Update:

1. **NIFTY_Dashboard_Quick_Reference.md**
   - **Section 7:** Macro View → Add **7.3: Greeks Hierarchy by Strategy & DTE**
   - Add table showing best Greek per strategy per DTE
   - Update Question 2 answer to include Greeks-focused monitoring

2. **NIFTY_Dashboard_Strategic_Plan.md**
   - **Section 7:** Add **7.3B: Greeks-Focused Combo Selection**
   - Explain how to validate combos against Greeks ranges
   - Show combo selection flow with Greeks validation layer

3. **NIFTY_Dashboard_Code_Snippets.md**
   - **Add Section 6:** Greeks Matrix Configuration
   - Config/greeks_matrix.py (lookup table)
   - get_greeks_config() function
   - Validation logic: validate_combo_greeks()

4. **Tab 6 (Trade Signals) — Update:**
   - Add show_greeks_monitoring_guide() function
   - Display best Greek + evolution chart
   - Entry checklist + exit rules
   - Alert thresholds

---

## KEY BENEFITS OF THIS APPROACH

✅ **Personalized Greek focus:** Each strategy has a different star performer
✅ **DTE-aware:** Theta dominates early, Gamma pinch late
✅ **Contextual entry:** Know exactly which Greek to validate before entering
✅ **Visual evolution:** See how best Greek changes over week
✅ **Alert system:** Get warnings if Greek drifts beyond safe range
✅ **Professional:** Matches how real traders think ("What's the theta on this strangle?")

---

**This addition transforms your dashboard from a generic tool into a Greeks-aware trading assistant.**
