"""Black-Scholes probability of profit estimation."""

import numpy as np
from scipy.stats import norm
from config.settings import RISK_FREE_RATE


def bs_pop_above(spot, target, iv, tte_years, r=RISK_FREE_RATE):
    """Probability that NIFTY finishes above target at expiry."""
    if tte_years <= 0:
        return 1.0 if spot >= target else 0.0
    d2 = (np.log(spot / target) + (r - 0.5 * iv**2) * tte_years) / (iv * np.sqrt(tte_years))
    return float(norm.cdf(d2))


def bs_pop_below(spot, target, iv, tte_years, r=RISK_FREE_RATE):
    """Probability that NIFTY finishes below target at expiry."""
    return 1.0 - bs_pop_above(spot, target, iv, tte_years, r)


def bs_pop_between(spot, lower, upper, iv, tte_years, r=RISK_FREE_RATE):
    """Probability that NIFTY finishes between lower and upper."""
    return bs_pop_above(spot, lower, iv, tte_years, r) - bs_pop_above(spot, upper, iv, tte_years, r)


def spread_pop(spot, buy_strike, sell_strike, net_premium,
               iv, tte_years, spread_type="bull_call"):
    """POP for a vertical spread."""
    if spread_type == "bull_call":
        breakeven = buy_strike + net_premium
        return bs_pop_above(spot, breakeven, iv, tte_years)
    else:
        breakeven = buy_strike - net_premium
        return bs_pop_below(spot, breakeven, iv, tte_years)
