"""Market condition classification engine."""

import pandas as pd
import numpy as np
from indicators.technical import compute_rsi, compute_sma, classify_market
from config.settings import INDICATOR_PARAMS


class MarketConditionClassifier:
    def __init__(self, price_df: pd.DataFrame):
        self.df = price_df.copy()
        self._compute_indicators()

    def _compute_indicators(self):
        self.df["rsi"] = compute_rsi(self.df["close"])
        self.df["sma_20"] = compute_sma(self.df["close"], INDICATOR_PARAMS["sma_fast"])
        self.df["sma_50"] = compute_sma(self.df["close"], INDICATOR_PARAMS["sma_slow"])

    def current_condition(self, iv_current: float = 0.14, iv_avg: float = 0.13) -> dict:
        latest = self.df.iloc[-1]
        condition = classify_market(
            spot=latest["close"],
            rsi=latest["rsi"],
            sma20=latest["sma_20"],
            sma50=latest["sma_50"],
            iv_current=iv_current,
            iv_avg=iv_avg,
        )
        return {
            "condition": condition,
            "spot": latest["close"],
            "rsi": round(latest["rsi"], 2),
            "sma_20": round(latest["sma_20"], 2),
            "sma_50": round(latest["sma_50"], 2),
            "iv_current": iv_current,
            "iv_avg": iv_avg,
            "trend_strength": self._trend_strength(latest),
        }

    def _trend_strength(self, row) -> str:
        sma_gap = abs(row["sma_20"] - row["sma_50"]) / row["close"] * 100
        if sma_gap > 2:
            return "strong"
        elif sma_gap > 0.8:
            return "moderate"
        return "weak"

    def condition_history(self, iv_series: pd.Series = None) -> pd.Series:
        if iv_series is None:
            iv_series = pd.Series(0.14, index=self.df.index)
        iv_avg = iv_series.rolling(20).mean().fillna(iv_series.mean())

        conditions = []
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            if pd.isna(row["rsi"]) or pd.isna(row["sma_20"]) or pd.isna(row["sma_50"]):
                conditions.append("unknown")
            else:
                conditions.append(classify_market(
                    row["close"], row["rsi"], row["sma_20"], row["sma_50"],
                    iv_series.iloc[i], iv_avg.iloc[i]
                ))
        return pd.Series(conditions, index=self.df.index)
