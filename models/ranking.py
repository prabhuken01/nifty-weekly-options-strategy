"""Composite combo score + Greek grade integration."""

from typing import Any, Dict, List, Tuple

import pandas as pd

from config.greeks_matrix import grade_value
from models.liquidity import combo_min_leg_oi_cr
from strike_selection.selector import StrikeCombo


def net_greeks_from_chain(combo: StrikeCombo, chain_df: pd.DataFrame) -> Tuple[float, float, float, float]:
    """Net delta, gamma, theta, vega for the combo using chain rows (per-leg)."""
    strat = combo.strategy

    if strat in ("short_strangle", "long_strangle"):
        pe = chain_df[
            (chain_df["instrument_type"] == "PE") & (chain_df["strike_price"] == combo.buy_strike)
        ]
        ce = chain_df[
            (chain_df["instrument_type"] == "CE") & (chain_df["strike_price"] == combo.sell_strike)
        ]
        if pe.empty or ce.empty:
            return 0.0, 0.0, 0.0, 0.0
        pr, cr = pe.iloc[0], ce.iloc[0]
        if strat == "short_strangle":
            # Short both legs: flip signs vs long-option Greeks
            net_d = -float(pr["delta"]) - float(cr["delta"])
            net_g = -float(pr["gamma"]) - float(cr["gamma"])
            net_t = -float(pr["theta"]) - float(cr["theta"])
            net_v = -float(pr["vega"]) - float(cr["vega"])
        else:
            net_d = float(pr["delta"]) + float(cr["delta"])
            net_g = float(pr["gamma"]) + float(cr["gamma"])
            net_t = float(pr["theta"]) + float(cr["theta"])
            net_v = float(pr["vega"]) + float(cr["vega"])
        return net_d, net_g, net_t, net_v

    if strat == "bull_call_spread":
        ce = chain_df[chain_df["instrument_type"] == "CE"]
        b = ce[ce["strike_price"] == combo.buy_strike]
        s = ce[ce["strike_price"] == combo.sell_strike]
        if b.empty or s.empty:
            return 0.0, 0.0, 0.0, 0.0
        br, sr = b.iloc[0], s.iloc[0]
        return (
            float(br["delta"]) - float(sr["delta"]),
            float(br["gamma"]) - float(sr["gamma"]),
            float(br["theta"]) - float(sr["theta"]),
            float(br["vega"]) - float(sr["vega"]),
        )

    if strat == "bear_put_spread":
        pe = chain_df[chain_df["instrument_type"] == "PE"]
        b = pe[pe["strike_price"] == combo.buy_strike]
        s = pe[pe["strike_price"] == combo.sell_strike]
        if b.empty or s.empty:
            return 0.0, 0.0, 0.0, 0.0
        br, sr = b.iloc[0], s.iloc[0]
        return (
            float(br["delta"]) - float(sr["delta"]),
            float(br["gamma"]) - float(sr["gamma"]),
            float(br["theta"]) - float(sr["theta"]),
            float(br["vega"]) - float(sr["vega"]),
        )

    return combo.buy_delta - combo.sell_delta, 0.0, 0.0, 0.0


def score_combo(
    combo: StrikeCombo,
    strategy_key: str,
    stats: Dict[str, Any],
    oi_cr: float,
    net_delta: float,
) -> float:
    """Weighted score 0–1: delta quality, liquidity, POP, R:R."""
    ideal = {
        "bull_call_spread": 0.18,
        "bear_put_spread": 0.18,
        "short_strangle": 0.0,
        "long_strangle": 0.0,
    }
    target = ideal.get(strategy_key, 0.15)
    if strategy_key in ("short_strangle", "long_strangle"):
        delta_score = 0.75
    else:
        delta_score = max(0.0, 1.0 - abs(abs(net_delta) - target) * 4)

    liq_score = min(1.0, oi_cr / 80.0) if oi_cr > 0 else 0.3
    pop = float(stats.get("pop", 0.5))
    pop_score = min(1.0, pop / 0.65)
    rr = float(stats.get("risk_reward", 1.0))
    if rr == float("inf"):
        rr_score = 1.0
    else:
        rr_score = min(1.0, rr / 2.5)

    return 0.35 * delta_score + 0.30 * liq_score + 0.25 * pop_score + 0.10 * rr_score


def full_combo_rank(
    combo: StrikeCombo,
    strategy_key: str,
    stats: Dict[str, Any],
    chain_df: pd.DataFrame,
    tte_days: int,
) -> Dict[str, Any]:
    oi_cr = combo_min_leg_oi_cr(combo, chain_df)
    d_net, g_net, t_net, v_net = net_greeks_from_chain(combo, chain_df)
    sc = score_combo(combo, strategy_key, stats, oi_cr, d_net)
    grade, gmsg = grade_value(strategy_key, tte_days, d_net, g_net, t_net, v_net)
    grade_order = 0 if grade == "A" else 1 if grade == "B" else 2
    return {
        "combo": combo,
        "stats": stats,
        "score": sc,
        "oi_cr": oi_cr,
        "grade": grade,
        "grade_msg": gmsg,
        "net_delta": d_net,
        "sort_key": (grade_order, -sc),
    }


def rank_combos(
    combos: List[StrikeCombo],
    strategy_key: str,
    prob_model: Any,
    chain_df: pd.DataFrame,
    tte_days: int,
    min_pop: float,
    min_rr: float,
) -> List[Dict[str, Any]]:
    out = []
    for combo in combos:
        try:
            stats = prob_model.evaluate(combo, strategy_key)
        except Exception:
            stats = {"pop": 0.5, "risk_reward": 1.5, "expected_payoff": 0}
        if stats.get("pop", 0) < min_pop:
            continue
        rr = stats.get("risk_reward", 0)
        if rr != float("inf") and rr < min_rr:
            continue
        out.append(full_combo_rank(combo, strategy_key, stats, chain_df, tte_days))
    out.sort(key=lambda x: (x["sort_key"][0], x["sort_key"][1]))
    return out
