"""Technical indicators: RSI, SMA, VWAP, Bollinger Bands, market classifier."""

import pandas as pd
import numpy as np
from config.settings import INDICATOR_PARAMS, MARKET_CONDITION_THRESHOLDS


def compute_rsi(prices: pd.Series, period: int = None) -> pd.Series:
    period = period or INDICATOR_PARAMS["rsi_period"]
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def compute_sma(prices: pd.Series, period: int) -> pd.Series:
    return prices.rolling(period).mean()


def compute_ema(prices: pd.Series, period: int) -> pd.Series:
    return prices.ewm(span=period, adjust=False).mean()


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_tp_vol = (tp * df["volume"]).cumsum()
    cumulative_vol = df["volume"].cumsum()
    return cumulative_tp_vol / cumulative_vol


def compute_bollinger_bands(prices: pd.Series, period: int = None, std_dev: int = None):
    period = period or INDICATOR_PARAMS["bollinger_period"]
    std_dev = std_dev or INDICATOR_PARAMS["bollinger_std"]
    sma = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    return sma, sma + std_dev * std, sma - std_dev * std


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to a NIFTY price dataframe."""
    df = df.copy()
    df["rsi_14"] = compute_rsi(df["close"])
    df["sma_20"] = compute_sma(df["close"], INDICATOR_PARAMS["sma_fast"])
    df["sma_50"] = compute_sma(df["close"], INDICATOR_PARAMS["sma_slow"])
    df["ema_9"] = compute_ema(df["close"], 9)
    df["vwap"] = compute_vwap(df)
    df["bb_mid"], df["bb_upper"], df["bb_lower"] = compute_bollinger_bands(df["close"])
    df["atr_14"] = compute_atr(df)
    df["daily_return"] = df["close"].pct_change()
    df["cumulative_return"] = (1 + df["daily_return"]).cumprod() - 1
    return df


def classify_market(spot: float, rsi: float, sma20: float, sma50: float,
                    iv_current: float, iv_avg: float) -> str:
    thresholds = MARKET_CONDITION_THRESHOLDS
    if rsi > thresholds["bullish_rsi"] and spot > sma20 > sma50:
        return "bullish"
    elif rsi < thresholds["bearish_rsi"] and spot < sma20 < sma50:
        return "bearish"
    elif iv_current > iv_avg * thresholds["high_vol_multiplier"]:
        return "high_volatility"
    return "sideways"
