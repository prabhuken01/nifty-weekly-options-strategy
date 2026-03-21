"""Decision engine: signal generator + strategy mapper."""

from dataclasses import dataclass
from typing import List
from strike_selection.selector import StrikeSelector, StrikeCombo
from config.settings import STRATEGY_PARAMS


@dataclass
class TradeSignal:
    strategy: str
    combo: StrikeCombo
    entry_price: float
    stop_loss: float
    target_price: float
    pop: float
    expected_payoff: float
    risk_reward: float
    confidence: str
    rationale: str


STRATEGY_MAP = {
    "bullish": ["bull_call_spread"],
    "bearish": ["bear_put_spread"],
    "sideways": ["short_strangle"],
    "high_volatility": ["long_strangle"],
}

CONFIDENCE_LABELS = {
    "high": {"min_pop": 0.60, "min_rr": 2.0},
    "medium": {"min_pop": 0.50, "min_rr": 1.5},
}


def generate_signals(selector: StrikeSelector, market_condition: str,
                     prob_evaluator, spot: float, iv: float,
                     tte_days: float) -> List[TradeSignal]:
    """Generate ranked trade signals for the current market condition."""
    strategies = STRATEGY_MAP.get(market_condition, [])
    signals = []

    dispatch = {
        "bull_call_spread": selector.get_bull_call_combos,
        "bear_put_spread": selector.get_bear_put_combos,
        "long_strangle": selector.get_long_strangle_combos,
        "short_strangle": selector.get_short_strangle_combos,
    }

    for strategy in strategies:
        combos = dispatch.get(strategy, lambda: [])()
        for combo in combos:
            stats = prob_evaluator.evaluate(combo, strategy)

            if (stats["risk_reward"] >= STRATEGY_PARAMS["min_risk_reward"]
                    and stats["pop"] >= STRATEGY_PARAMS["min_pop"]):

                confidence = "low"
                for level, thresholds in CONFIDENCE_LABELS.items():
                    if (stats["pop"] >= thresholds["min_pop"]
                            and stats["risk_reward"] >= thresholds["min_rr"]):
                        confidence = level
                        break

                signals.append(TradeSignal(
                    strategy=strategy,
                    combo=combo,
                    entry_price=combo.net_premium,
                    stop_loss=round(combo.net_premium * STRATEGY_PARAMS["stop_loss_multiplier"], 2),
                    target_price=round(combo.max_profit * STRATEGY_PARAMS["target_pct_of_max"], 2),
                    pop=stats["pop"],
                    expected_payoff=stats["expected_payoff"],
                    risk_reward=stats["risk_reward"],
                    confidence=confidence,
                    rationale=_build_rationale(strategy, market_condition, stats),
                ))

    return sorted(signals, key=lambda s: s.risk_reward, reverse=True)


def _build_rationale(strategy, condition, stats):
    return (f"{strategy.replace('_', ' ').title()} selected for "
            f"{condition} market. POP={stats['pop']:.0%}, "
            f"R:R={stats['risk_reward']:.1f}x, "
            f"Expected Payoff=₹{stats['expected_payoff']:.0f}")
