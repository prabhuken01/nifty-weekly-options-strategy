# Consolidated implementation plan

**Purpose:** Single source of truth after reviewing **all** deliverables in this folder, including files that were only partially summarized in earlier planning.

**Audience:** Anyone implementing or reviewing scope — ties together README, Executive Summary, Strategic Plan, Quick Reference, Code Snippets, Greeks Matrix Addition, DELTA updates, and GREEKS_MATRIX_IMPLEMENTATION_GUIDE.

---

## 1. Source document coverage (read-through status)

| Document | Role | Notes for implementers |
|----------|------|-------------------------|
| [README_DELIVERABLES.txt](README_DELIVERABLES.txt) | Index + 7-question answers + 4-week roadmap + formulas | Use as checklist against this plan. |
| [NIFTY_Dashboard_Executive_Summary.md](NIFTY_Dashboard_Executive_Summary.md) | Same 7 themes, week priorities, success criteria | Aligns 1:1 with README. |
| [NIFTY_Dashboard_Strategic_Plan.md](NIFTY_Dashboard_Strategic_Plan.md) | Deep dive: schemas, backtest pseudo-code, MC-by-day, mobile, liquidity, macro+ranking, refactor tree | **Data realism** requires external or reconstructed chains; see §5. |
| [NIFTY_Dashboard_Quick_Reference.md](NIFTY_Dashboard_Quick_Reference.md) | Condensed Q&A, **data source table**, MC date-wise pseudocode, phased week roadmap, success metrics | OI ₹Cr formula: use **`(OI × lot × LTP) / 1e7`** for crores (some examples in docs use equivalent algebra; avoid ad-hoc “÷10” shortcuts). |
| [NIFTY_Dashboard_Code_Snippets.md](NIFTY_Dashboard_Code_Snippets.md) | **Six concrete sections** (below) + long-form glossary strings + ranking/macro code patterns | Snippets assume `combo.oi_rupees`, `BacktestTrade.daily_progression`, etc. — wire or adapt to current `StrikeCombo` / `generate_backtest_results`. |
| [NIFTY_Dashboard_Greeks_Matrix_Addition.md](NIFTY_Dashboard_Greeks_Matrix_Addition.md) | **Tier 0** interactive matrix: strategy × DTE → best Greek, ranges, tips | Extends macro (Tier 1) + ranking (Tier 2). |
| [DELTA_Sections_To_Update.md](DELTA_Sections_To_Update.md) | Doc-edit instructions + **§7.3 Greeks hierarchy table** + **Strategic Plan §7.3B** flow: **sort by Greeks validity first, then score** | Critical for product behavior, not only docs. |
| [GREEKS_MATRIX_IMPLEMENTATION_GUIDE.txt](GREEKS_MATRIX_IMPLEMENTATION_GUIDE.txt) | Step-by-step: `config/greeks_matrix.py`, `validate_combo_greeks`, Trade Signals order, validation checklist | **Must-do path:** matrix → validate → badges → Trade Signals. |

**Previously agreed product extras (from stakeholder requests, not all in every PDF):**

- Merit / ranked **backtest** results; optionally **cap at 1–2 strategies per calendar day** when presenting “daily picks.”
- **Dark (default) vs light** theme with contrasting text and Plotly templates.
- **Point-in-time (“then”)** CE/PE Greeks for a chosen trade date — feasible as **BS-reconstructed** until broker data exists.

---

## 2. What each major file adds (unique value)

### 2.1 Code_Snippets.md — six implementation blocks

| § | Deliverable | Depends on |
|---|-------------|------------|
| **1** | Greeks timeline table (strike selector, CE row per simulated day) + **theta acceleration** Plotly chart + captions | Synthetic multi-day series or DB; current app has single snapshot — must simulate or load history. |
| **2** | `WeeklyBacktestEngine` + `BacktestTrade` with `entry_greeks`, `daily_progression`; per-trade **Greeks progression** UI + **P&L attribution** (theta/vega/gamma split — simplified) | `data_loader.load_chain(expiry, time)` abstraction; not in current repo as-is. |
| **3** | **Mobile CSS** (`@media` breakpoints, table font, chart height, touch targets) + **placeholder** `get_screen_width()` / fewer metrics on “mobile” | Real client width needs `st.components` or accept CSS-only behavior without true device detection. |
| **4** | **`render_info_guide`** + **long markdown constants** (`MARKET_OVERVIEW_GUIDE`, `OPTION_CHAIN_GUIDE`, … through `TRADE_SIGNALS_GUIDE`) | Pure UI module; no data dependency. |
| **5** | **`add_liquidity_rupees`** + `column_config` for OI/Vol ₹Cr | Chain `DataFrame` + lot size. |
| **6** | **`render_macro_strategy_view`** (cards + bullish_prob, iv_rank) + **`score_combo` / `show_ranked_combos`** with 40/30/20/10 weights | Needs `bullish_prob`, `iv_rank` definitions; `combo.oi_rupees` on `StrikeCombo` or computed. |

**Note:** Code_Snippets references “Section 7” for Greeks matrix in **GREEKS_MATRIX_IMPLEMENTATION_GUIDE**; the snippets file’s numbered sections stop at **6** — the matrix/validation code is specified in the **guide + DELTA + Strategic Plan §7.3B**, not as a separate “§7” in Code_Snippets.md.

### 2.2 Quick_Reference.md — extras not repeated elsewhere

- **Data you’ll need** table (NIFTY OHLC, chain snapshots, IV history, Greeks source).
- **Date-wise MC** loop sketch (`monte_carlo_date_wise` / `simulate_gbm_paths`).
- **Conditional metrics** idea (fewer cards when narrow — needs width detection or user toggle).
- **End-to-end phased roadmap** (Weeks 1–5+) and **success metrics** table.

### 2.3 GREEKS_MATRIX_IMPLEMENTATION_GUIDE.txt — operational sequence

1. Create **`config/greeks_matrix.py`** — `GREEKS_MATRIX[strategy][dte]` with `best_greek`, `value_range`, `why`, `entry_checklist`, `exit_rules`, `alert_thresholds`.
2. **`validate_combo_greeks(combo, strategy, dte_days)`** → grades **A / B / C**.
3. Combo UI: badges, checklist, exit rules, alerts (see guide examples).
4. **`show_greeks_monitoring_guide()`** **before** combo list on Trade Signals (tab 6).
5. Optional: Greeks evolution chart Mon→Thu.

**Sort order (from DELTA / Strategic §7.3B):** **Greeks grade first** (✓ > △ > ✗), **then** composite score.

**Strategies to cover:** Bull Call, Bear Put, Long Strangle, Short Strangle, Bull Put, Iron Condor × **DTE buckets** (e.g. 4, 3, 2) — guide validation checklist §299–311.

### 2.4 DELTA_Sections_To_Update.md — product behavior change

- Upgrades “two-tier” to **three-tier**: **Tier 0 Greeks matrix → Tier 1 macro → Tier 2 ranking**.
- Inserts **§7.3** table (strategy × DTE × best Greek) and **exit/alert** tables into Quick Reference (when docs are edited).
- **§7.3B** in Strategic Plan: **validation layer before ranking**, `GREEKS_MATRIX` structure, **Greeks validity badge** copy.

### 2.5 Strategic Plan (already used) — backbone

- TimescaleDB / Parquet story, weekly backtest loop, date-wise MC cones, refactor to `ui/` + `models/`.
- **Dependency graph:** Greeks storage → timeline → backtest → per-trade progression ∥ parallel UX tracks.

---

## 3. Master deliverable list (single checklist)

Use this as the **authoritative scope** list (checkboxes for your tracker).

**Data & backtest**

- [ ] Time-series option snapshots schema (DB or Parquet); optional 5–15 min granularity.
- [ ] Data loader: `load_chain(expiry, timestamp)` for backtest loop.
- [ ] Weekly expiry loop: entry Mon ~2 PM IST, exit rules (50% max profit, 2× stop, Wed EOD per docs).
- [ ] `BacktestTrade` extended: `entry_greeks`, `daily_progression`, `exit_reason`.
- [ ] Backtest tab: trade picker, Greeks progression table, 2×2 Greeks charts, **P&L attribution** (simplified).
- [ ] **Ranked backtest view**: sort by merit score; optional **max 1–2 strategy lines per calendar day**.

**Greeks UX**

- [ ] **Tier 0:** `greeks_matrix.py` + validation + **A/B/C** badges + sort **before** composite score.
- [ ] Greeks timeline + theta acceleration chart (§1 snippets) on Option Chain or subpanel.
- [ ] **Point-in-time panel:** date (+ time) + strike + CE/PE → show BS Greeks (reconstructed IV until live API).

**Monte Carlo**

- [ ] **Date-wise** probabilities table + percentile cone (per day to expiry).

**Macro & ranking**

- [ ] **Tier 1:** Macro cards (`bullish_prob`, `iv_rank`, `tte`) + four strategy cards.
- [ ] **Tier 2:** `score_combo` 40/30/20/10; `oi_rupees` on combos; top 3 + full table.
- [ ] Trade Signals: **monitoring guide before combos** (guide step 4–5).

**Liquidity & education**

- [ ] OI / Volume **₹ Crore** columns (`/ 1e7` convention).
- [ ] `render_info_guide` + six glossary constants (or split `ui/info_guides.py`).

**Layout & theme**

- [ ] Responsive CSS (§3) + optional fewer metrics without real width (or **compact mode** toggle).
- [ ] **Dark (default) / light** theme: `st.session_state`, CSS variables, Plotly `template`.

**Engineering hygiene**

- [ ] Refactor `app.py` into `ui/tabs/*`, `models/ranking.py`, `config/greeks_matrix.py` per Strategic Plan §10.

**Future / optional**

- [ ] Broker API (Zerodha/Upstox) for live chains and **true** historical Greeks.

---

## 4. Phased execution order (recommended)

**Phase A — UI and education (no new DB)**  
Liquidity ₹Cr, info guides, macro cards (with explicit **synthetic** bullish_prob / iv_rank from existing indicators), responsive CSS, **dark/light theme**, wire `score_combo` once `oi_rupees` exists.

**Phase B — Greeks matrix and signal flow**  
`greeks_matrix.py`, `validate_combo_greeks`, Trade Signals order (guide → combos), dual sort (Greeks grade then score), extend `StrikeCombo` or wrapper with `oi_rupees`.

**Phase C — Analytics on synthetic extensions**  
Multi-day simulated Greeks timeline, theta acceleration chart, date-wise MC table/cone, point-in-time BS panel, ranked backtest aggregation + **1–2 strategies/day** rule.

**Phase D — Production data path**  
Parquet/TimescaleDB, real or broker EOD chains, replace synthetic loaders in `WeeklyBacktestEngine`.

---

## 5. Feasibility and honesty boundaries

| Item | Feasibility | Comment |
|------|-------------|---------|
| Tier 0 matrix + validation + UI | **High** | Pure config + math on current chain. |
| ₹Cr, guides, CSS, theme, macro cards | **High** | |
| Ranking + oi_rupees | **High** | Add notional columns. |
| Date-wise MC | **High** | Extend existing MC module. |
| Snippets backtest engine + daily progression | **Medium** | Needs loader abstraction + trade shape changes. |
| “True” historical intraday Greeks | **Low** without data | Reconstruct with BS + spot/IV **or** broker API. |
| Real `window.innerWidth` in Streamlit | **Medium** | Use `streamlit-js-eval` or accept CSS-only behavior. |

---

## 6. Conflicts / clarifications to resolve during build

1. **Net vs leg Greek for matrix:** Guide often cites “delta 0.25–0.35” for bull call — confirm whether **buy leg**, **spread net**, or **abs** — document in `greeks_matrix.py` and use consistently in `validate_combo_greeks`.
2. **`get_entry_time` in snippet:** Calendar logic must match **Indian weekly Thursday expiry** conventions; verify against `holidays` / actual NSE calendar.
3. **`combo.oi_rupees`:** Code_Snippets table references it — define as **min(OI notional)** of legs or **sum** per product preference.
4. **1–2 strategies per day:** Define **calendar day** vs **session**, and tie-breaker (score vs liquidity).

---

## 7. Traceability: doc → this plan

| Concept | Primary sources |
|--------|-----------------|
| 7 questions | README, Executive Summary, Quick Reference |
| DB schema & backtest loop | Strategic Plan Part 2 |
| MC by day | Strategic Plan Part 3, Quick Reference §3 |
| Mobile + metrics | Strategic Plan Part 4, Code_Snippets §3 |
| Info expanders + glossary text | Code_Snippets §4 |
| ₹Cr liquidity | Strategic Plan Part 6, Code_Snippets §5, Quick Reference §6 |
| Macro + ranking weights | Strategic Plan Part 7, Code_Snippets §6 |
| Tier 0 matrix + validation order | Greeks_Matrix_Addition, DELTA, GREEKS_MATRIX_IMPLEMENTATION_GUIDE |
| Copy-paste engine / UI blocks | Code_Snippets §§1–2, 6 |

---

*Last consolidated: aligns implementation work with all eight listed deliverables and stakeholder add-ons (theme, ranked daily backtest cap, point-in-time BS Greeks).*
