"""Unified POP estimator combining Black-Scholes and Monte Carlo."""

from probability.black_scholes import spread_pop as bs_spread_pop
from probability.monte_carlo import spread_expected_payoff, mc_pop_above


def _normalize_strategy_type(strategy_type: str) -> str:
    """Map StrikeCombo.strategy keys to BS/MC engine keys."""
    return {
        "bull_call_spread": "bull_call",
        "bear_put_spread": "bear_put",
        "short_strangle": "short_strangle",
        "long_strangle": "long_strangle",
    }.get(strategy_type, strategy_type)


class POPEstimator:
    def __init__(self, spot, iv, tte_years):
        self.spot = spot
        self.iv = iv
        self.tte_years = tte_years

    def evaluate(self, combo, strategy_type):
        """Evaluate a strike combo with both BS and MC methods."""
        net_premium = abs(combo.net_premium)
        engine_type = _normalize_strategy_type(strategy_type)

        mc_result = spread_expected_payoff(
            self.spot, combo.buy_strike, combo.sell_strike,
            self.iv, self.tte_years, net_premium, engine_type
        )

        # Vertical BS formula does not apply to strangles — align BS with MC there.
        if engine_type in ("short_strangle", "long_strangle"):
            bs_pop = float(mc_result["pop"])
        else:
            bs_pop = bs_spread_pop(
                self.spot, combo.buy_strike, combo.sell_strike,
                net_premium, self.iv, self.tte_years, engine_type
            )

        blended_pop = 0.4 * bs_pop + 0.6 * mc_result["pop"]

        return {
            "bs_pop": round(bs_pop, 4),
            "mc_pop": round(mc_result["pop"], 4),
            "blended_pop": round(blended_pop, 4),
            "expected_payoff": round(mc_result["expected_payoff"], 2),
            "risk_reward": round(mc_result["risk_reward"], 2),
            "max_profit": round(mc_result["max_profit"], 2),
            "max_loss": round(mc_result["max_loss"], 2),
            "pop": round(blended_pop, 4),
        }
