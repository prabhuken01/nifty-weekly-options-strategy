"""Shared Black–Scholes price & Greeks (points engine + analytics)."""

import numpy as np
from scipy.stats import norm

from config.settings import RISK_FREE_RATE


def bs_greeks(
    S: float,
    K: float,
    T: float,
    sigma: float,
    option_type: str = "CE",
    r: float = RISK_FREE_RATE,
) -> dict:
    """Delta, gamma, theta (per day), vega (per 1% IV move), theoretical price."""
    if T <= 0:
        if option_type == "CE":
            return {"delta": 1.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "price": max(S - K, 0)}
        return {"delta": -1.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0, "price": max(K - S, 0)}

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    gamma = float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))
    vega = float(S * norm.pdf(d1) * np.sqrt(T) / 100)

    if option_type == "CE":
        delta = float(norm.cdf(d1))
        price = float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
        theta = float(
            (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        )
    else:
        delta = float(norm.cdf(d1) - 1.0)
        price = float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))
        theta = float(
            (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        )

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega, "price": price}
