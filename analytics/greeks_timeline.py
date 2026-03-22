"""Synthetic Greeks vs days-to-expiry (mean path or flat spot)."""

import numpy as np
import pandas as pd

from config.settings import RISK_FREE_RATE
from options.bs_greeks import bs_greeks


def greeks_vs_time_for_strike(
    spot_schedule: np.ndarray,
    strike: float,
    iv: float,
    tte_days: int,
    option_type: str = "CE",
    r: float = RISK_FREE_RATE,
) -> pd.DataFrame:
    """
    For each day index d, remaining T = (tte_days - d) / 365.
    Re-values CE or PE at `strike` along spot path.
    """
    rows = []
    for d in range(int(tte_days) + 1):
        S = float(spot_schedule[min(d, len(spot_schedule) - 1)])
        T = max((tte_days - d) / 365.0, 1e-8)
        g = bs_greeks(S, strike, T, iv, option_type, r)
        rows.append({
            "day": d,
            "spot": S,
            "dte_left": tte_days - d,
            "delta": g["delta"],
            "gamma": g["gamma"],
            "theta": g["theta"],
            "vega": g["vega"],
            "theoretical_price": g["price"],
        })
    return pd.DataFrame(rows)


def theta_acceleration_series(df: pd.DataFrame) -> pd.Series:
    """Second difference of theta (crude 'acceleration')."""
    theta = df["theta"].values
    if len(theta) < 3:
        return pd.Series(np.zeros(len(theta)), index=df.index)
    acc = np.zeros_like(theta)
    acc[2:] = np.diff(theta, n=2)
    return pd.Series(acc, index=df.index, name="theta_accel")
