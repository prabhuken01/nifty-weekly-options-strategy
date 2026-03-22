"""Date-wise GBM paths and percentile cones (to expiry)."""

from typing import Tuple

import numpy as np
import pandas as pd

from config.settings import RISK_FREE_RATE


def simulate_daily_paths(
    spot: float,
    iv: float,
    tte_days: int,
    n_sims: int,
    r: float = RISK_FREE_RATE,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (days_axis, paths) where paths shape is (n_sims, tte_days + 1).
    One trading-day step per calendar day in the model.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / 365.0
    n_days = int(tte_days) + 1
    days = np.arange(0, n_days)
    paths = np.zeros((n_sims, n_days))
    paths[:, 0] = spot
    for d in range(1, n_days):
        z = rng.standard_normal(n_sims)
        paths[:, d] = paths[:, d - 1] * np.exp((r - 0.5 * iv**2) * dt + iv * np.sqrt(dt) * z)
    return days, paths


def cone_percentiles(paths: np.ndarray, percentiles=(5, 25, 50, 75, 95)) -> pd.DataFrame:
    """Per-day percentiles across simulated paths."""
    rows = []
    days = np.arange(paths.shape[1])
    for p in percentiles:
        rows.append(np.percentile(paths, p, axis=0))
    data = {"day": days}
    for p, row in zip(percentiles, rows):
        data[f"p{p}"] = row
    return pd.DataFrame(data)


def mc_probability_table(paths: np.ndarray, spot: float) -> pd.DataFrame:
    """
    Per day: P(S > spot) — useful for directional bias vs start (synthetic).
    """
    days = np.arange(paths.shape[1])
    p_above = [(paths[:, d] > spot).mean() for d in days]
    return pd.DataFrame({"day": days, "P(S > S0)": p_above})
