"""Unified POP estimator combining Black-Scholes and Monte Carlo."""

from probability.black_scholes import spread_pop as bs_spread_pop
from probability.monte_carlo import spread_expected_payoff, mc_pop_above


class POPEstimator:
    def __init__(self, spot, iv, tte_years):
        self.spot = spot
        self.iv = iv
        self.tte_years = tte_years

    def evaluate(self, combo, strategy_type):
        """Evaluate a strike combo with both BS and MC methods."""
        net_premium = abs(combo.net_premium)

        bs_pop = bs_spread_pop(
            self.spot, combo.buy_strike, combo.sell_strike,
            net_premium, self.iv, self.tte_years, strategy_type
        )

        mc_result = spread_expected_payoff(
            self.spot, combo.buy_strike, combo.sell_strike,
            self.iv, self.tte_years, net_premium, strategy_type
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
