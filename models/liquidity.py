"""Notional liquidity in ₹ Crore (NIFTY lot = 50)."""

import pandas as pd

from config.settings import NIFTY_LOT_SIZE


def oi_rupees_crore(open_interest: float, ltp: float, lot: int = NIFTY_LOT_SIZE) -> float:
    """Open interest notional in ₹ Crore."""
    return (float(open_interest) * lot * float(ltp)) / 1e7


def volume_rupees_crore(volume: float, price_proxy: float, lot: int = NIFTY_LOT_SIZE) -> float:
    """Volume notional in ₹ Crore using a single price proxy (e.g. LTP or mid)."""
    return (float(volume) * lot * float(price_proxy)) / 1e7


def enrich_chain_liquidity(df, ltp_col="ltp"):
    """Add OI_₹Cr and Vol_₹Cr columns."""
    out = df.copy()
    out["OI_₹Cr"] = out.apply(
        lambda r: round(oi_rupees_crore(r["open_interest"], r[ltp_col]), 2),
        axis=1,
    )
    out["Vol_₹Cr"] = out.apply(
        lambda r: round(volume_rupees_crore(r["volume"], r[ltp_col]), 2),
        axis=1,
    )
    return out


def combo_min_leg_oi_cr(combo, chain_df) -> float:
    """Minimum ₹Cr OI across the two actual legs (correct CE/PE per strategy)."""
    strat = getattr(combo, "strategy", "")
    if strat == "bull_call_spread":
        sub = chain_df[
            (chain_df["instrument_type"] == "CE")
            & (chain_df["strike_price"].isin([combo.buy_strike, combo.sell_strike]))
        ]
    elif strat == "bear_put_spread":
        sub = chain_df[
            (chain_df["instrument_type"] == "PE")
            & (chain_df["strike_price"].isin([combo.buy_strike, combo.sell_strike]))
        ]
    elif strat in ("short_strangle", "long_strangle"):
        pe = chain_df[
            (chain_df["instrument_type"] == "PE") & (chain_df["strike_price"] == combo.buy_strike)
        ]
        ce = chain_df[
            (chain_df["instrument_type"] == "CE") & (chain_df["strike_price"] == combo.sell_strike)
        ]
        sub = pd.concat([pe, ce], ignore_index=True) if not pe.empty and not ce.empty else pd.DataFrame()
    else:
        strikes = {combo.buy_strike, combo.sell_strike}
        sub = chain_df[chain_df["strike_price"].isin(strikes)]

    if sub is None or sub.empty:
        return 0.0
    crs = [oi_rupees_crore(row["open_interest"], row["ltp"]) for _, row in sub.iterrows()]
    return min(crs) if crs else 0.0
