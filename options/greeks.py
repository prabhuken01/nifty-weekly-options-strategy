"""Greeks calculation using Black-Scholes model."""

import numpy as np
from scipy.stats import norm
from config.settings import RISK_FREE_RATE


def bs_price(S, K, T, sigma, option_type="CE", r=RISK_FREE_RATE):
    """Black-Scholes option price."""
    if T <= 0:
        return max(S - K, 0) if option_type == "CE" else max(K - S, 0)

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "CE":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def delta(S, K, T, sigma, option_type="CE", r=RISK_FREE_RATE):
    if T <= 0:
        return float(S > K) if option_type == "CE" else float(S > K) - 1
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.cdf(d1) if option_type == "CE" else norm.cdf(d1) - 1


def gamma(S, K, T, sigma, r=RISK_FREE_RATE):
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))


def theta(S, K, T, sigma, option_type="CE", r=RISK_FREE_RATE):
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    common = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
    if option_type == "CE":
        return (common - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    return (common + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365


def vega(S, K, T, sigma, r=RISK_FREE_RATE):
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return S * norm.pdf(d1) * np.sqrt(T) / 100


def all_greeks(S, K, T, sigma, option_type="CE", r=RISK_FREE_RATE):
    return {
        "delta": round(delta(S, K, T, sigma, option_type, r), 4),
        "gamma": round(gamma(S, K, T, sigma, r), 6),
        "theta": round(theta(S, K, T, sigma, option_type, r), 2),
        "vega": round(vega(S, K, T, sigma, r), 2),
    }
