"""Generate realistic synthetic NIFTY option chain data for the dashboard."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import norm

from config.settings import NIFTY_LOT_SIZE, RISK_FREE_RATE


def _bs_price(S, K, T, r, sigma, option_type="CE"):
    """Black-Scholes option price."""
    if T <= 0:
        if option_type == "CE":
            return max(S - K, 0)
        return max(K - S, 0)

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "CE":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def _bs_greeks(S, K, T, r, sigma, option_type="CE"):
    """Compute Greeks using Black-Scholes."""
    if T <= 0:
        return {"delta": 1.0 if option_type == "CE" else -1.0,
                "gamma": 0, "theta": 0, "vega": 0}

    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100

    if option_type == "CE":
        delta = norm.cdf(d1)
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


def generate_option_chain(spot=22450.0, tte_days=5, base_iv=0.14):
    """Generate a realistic NIFTY option chain around the spot price."""
    rng = np.random.default_rng(42)
    T = tte_days / 365.0
    r = RISK_FREE_RATE

    strikes = np.arange(
        round(spot / 50) * 50 - 500,
        round(spot / 50) * 50 + 550,
        50
    )

    rows = []
    for strike in strikes:
        for opt_type in ["CE", "PE"]:
            distance_pct = (strike - spot) / spot
            moneyness_val = distance_pct if opt_type == "CE" else -distance_pct

            iv_smile = base_iv + 0.03 * abs(moneyness_val) * 10 + rng.normal(0, 0.005)
            iv_smile = max(0.08, min(0.40, iv_smile))

            price = _bs_price(spot, strike, T, r, iv_smile, opt_type)
            greeks = _bs_greeks(spot, strike, T, r, iv_smile, opt_type)

            if moneyness_val < -0.005:
                moneyness = "ITM"
            elif moneyness_val > 0.005:
                moneyness = "OTM"
            else:
                moneyness = "ATM"

            base_oi = int(rng.exponential(200_000) + 20_000)
            if abs(moneyness_val) < 0.02:
                base_oi = int(base_oi * 2.5)
            volume = int(base_oi * rng.uniform(0.01, 0.15))

            spread = price * rng.uniform(0.01, 0.04)
            bid = max(0.05, price - spread / 2)
            ask = price + spread / 2

            rows.append({
                "strike_price": strike,
                "instrument_type": opt_type,
                "ltp": round(price, 2),
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "bid_ask_spread": round(ask - bid, 2),
                "iv": round(iv_smile, 4),
                "delta": round(greeks["delta"], 4),
                "gamma": round(greeks["gamma"], 6),
                "theta": round(greeks["theta"], 2),
                "vega": round(greeks["vega"], 2),
                "volume": volume,
                "open_interest": base_oi,
                "oi_change": int(rng.normal(0, base_oi * 0.05)),
                "moneyness": moneyness,
                "distance_from_atm_pct": round(distance_pct * 100, 2),
                "spot_price": spot,
                "time_to_expiry": tte_days,
            })

    return pd.DataFrame(rows)


def generate_nifty_history(days=252, start_price=21000.0):
    """Generate realistic NIFTY daily price history."""
    rng = np.random.default_rng(123)
    mu = 0.12 / 252
    sigma = 0.14 / np.sqrt(252)

    log_returns = rng.normal(mu, sigma, days)
    regime_shifts = rng.choice([-1, 0, 1], size=days, p=[0.15, 0.55, 0.30])
    log_returns += regime_shifts * sigma * 0.3

    prices = start_price * np.exp(np.cumsum(log_returns))
    dates = pd.bdate_range(end=datetime.now(), periods=days)

    high = prices * (1 + rng.uniform(0.002, 0.015, days))
    low = prices * (1 - rng.uniform(0.002, 0.015, days))
    volume = rng.integers(100_000, 500_000, days)

    return pd.DataFrame({
        "date": dates,
        "open": np.round(np.roll(prices, 1), 2),
        "high": np.round(high, 2),
        "low": np.round(low, 2),
        "close": np.round(prices, 2),
        "volume": volume,
    }).iloc[1:]


def generate_backtest_results(n_weeks=52):
    """Generate realistic weekly backtest trade results."""
    rng = np.random.default_rng(77)
    strategies = ["Bull Call Spread", "Bear Put Spread", "Short Strangle", "Iron Condor"]

    trades = []
    base_date = datetime.now() - timedelta(weeks=n_weeks)

    for i in range(n_weeks):
        expiry = base_date + timedelta(weeks=i + 1)
        strategy = rng.choice(strategies, p=[0.35, 0.25, 0.25, 0.15])

        if strategy == "Bull Call Spread":
            win_prob, avg_win, avg_loss = 0.58, 3200, 4800
        elif strategy == "Bear Put Spread":
            win_prob, avg_win, avg_loss = 0.55, 3000, 5000
        elif strategy == "Short Strangle":
            win_prob, avg_win, avg_loss = 0.68, 2500, 7500
        else:
            win_prob, avg_win, avg_loss = 0.65, 2000, 6000

        won = rng.random() < win_prob
        pnl = rng.normal(avg_win, avg_win * 0.3) if won else -rng.normal(avg_loss, avg_loss * 0.3)

        trades.append({
            "expiry": expiry.strftime("%Y-%m-%d"),
            "strategy": strategy,
            "entry_premium": round(abs(pnl) * rng.uniform(0.8, 1.2), 2),
            "pnl": round(pnl, 2),
            "won": won,
            "pop": round(rng.uniform(0.40, 0.75), 2),
            "risk_reward": round(rng.uniform(1.2, 3.5), 2),
            "market_condition": rng.choice(["bullish", "bearish", "sideways", "high_volatility"]),
        })

    return pd.DataFrame(trades)
