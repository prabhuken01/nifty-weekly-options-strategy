"""Option chain parsing, enrichment, and analysis."""

import pandas as pd
import numpy as np
from options.greeks import all_greeks, bs_price
from config.settings import RISK_FREE_RATE


def enrich_chain(chain_df: pd.DataFrame, spot: float, tte_days: float) -> pd.DataFrame:
    """Add computed Greeks and derived fields to a raw option chain."""
    df = chain_df.copy()
    T = tte_days / 365.0

    greeks_data = []
    for _, row in df.iterrows():
        g = all_greeks(spot, row["strike_price"], T, row.get("iv", 0.15),
                       row["instrument_type"])
        greeks_data.append(g)

    greeks_df = pd.DataFrame(greeks_data)
    for col in greeks_df.columns:
        df[col] = greeks_df[col].values

    df["moneyness"] = df.apply(
        lambda r: _classify_moneyness(r["strike_price"], spot, r["instrument_type"]),
        axis=1
    )
    df["distance_from_atm_pct"] = round((df["strike_price"] - spot) / spot * 100, 2)
    df["theoretical_price"] = df.apply(
        lambda r: round(bs_price(spot, r["strike_price"], T, r.get("iv", 0.15),
                                 r["instrument_type"]), 2),
        axis=1
    )
    df["mispricing"] = round(df["ltp"] - df["theoretical_price"], 2)

    return df


def _classify_moneyness(strike, spot, opt_type):
    pct = (strike - spot) / spot
    if opt_type == "CE":
        if pct < -0.005:
            return "ITM"
        elif pct > 0.005:
            return "OTM"
    else:
        if pct > 0.005:
            return "ITM"
        elif pct < -0.005:
            return "OTM"
    return "ATM"


def compute_pcr(chain_df: pd.DataFrame) -> dict:
    """Compute Put-Call Ratio from chain data."""
    puts = chain_df[chain_df["instrument_type"] == "PE"]
    calls = chain_df[chain_df["instrument_type"] == "CE"]

    oi_pcr = puts["open_interest"].sum() / max(calls["open_interest"].sum(), 1)
    vol_pcr = puts["volume"].sum() / max(calls["volume"].sum(), 1)

    return {
        "oi_pcr": round(oi_pcr, 3),
        "volume_pcr": round(vol_pcr, 3),
        "interpretation": "bullish" if oi_pcr > 1.2 else "bearish" if oi_pcr < 0.8 else "neutral",
    }


def max_pain(chain_df: pd.DataFrame) -> float:
    """Calculate the max pain strike price."""
    strikes = chain_df["strike_price"].unique()
    pain = {}

    for strike in strikes:
        total_pain = 0
        for _, row in chain_df.iterrows():
            if row["instrument_type"] == "CE":
                total_pain += max(0, row["strike_price"] - strike) * row["open_interest"]
            else:
                total_pain += max(0, strike - row["strike_price"]) * row["open_interest"]
        pain[strike] = total_pain

    return min(pain, key=pain.get)
