"""Liquidity filtering for option chain strikes."""

import pandas as pd
from config.settings import LIQUIDITY_FILTERS


def filter_liquid_strikes(chain_df: pd.DataFrame,
                          min_oi: int = None,
                          min_volume: int = None,
                          max_spread_pct: float = None) -> pd.DataFrame:
    """Filter option chain to only liquid strikes."""
    min_oi = min_oi or LIQUIDITY_FILTERS["min_oi"]
    min_volume = min_volume or LIQUIDITY_FILTERS["min_volume"]
    max_spread_pct = max_spread_pct or LIQUIDITY_FILTERS["max_spread_pct"]

    df = chain_df.copy()

    df = df[df["open_interest"] >= min_oi]
    df = df[df["volume"] >= min_volume]

    if "bid" in df.columns and "ask" in df.columns and "ltp" in df.columns:
        spread_pct = (df["ask"] - df["bid"]) / df["ltp"].clip(lower=0.01)
        df = df[spread_pct <= max_spread_pct]

    return df.reset_index(drop=True)


def liquidity_score(row: pd.Series) -> float:
    """Score a strike's liquidity from 0-100."""
    oi_score = min(row["open_interest"] / 500_000, 1.0) * 40
    vol_score = min(row["volume"] / 10_000, 1.0) * 30

    if row.get("bid") and row.get("ask") and row.get("ltp"):
        spread = (row["ask"] - row["bid"]) / max(row["ltp"], 0.01)
        spread_score = max(0, (1 - spread / 0.05)) * 30
    else:
        spread_score = 15

    return round(oi_score + vol_score + spread_score, 1)
