"""Backtest performance metrics and analytics."""

import pandas as pd
import numpy as np


def compute_metrics(trades_df: pd.DataFrame) -> dict:
    """Compute comprehensive backtest metrics from a trades DataFrame."""
    if trades_df.empty:
        return {}

    pnl = trades_df["pnl"]
    wins = pnl[pnl > 0]
    losses = pnl[pnl <= 0]

    cumulative = pnl.cumsum()
    peak = cumulative.cummax()
    drawdown = cumulative - peak

    return {
        "total_pnl": round(pnl.sum(), 2),
        "total_trades": len(pnl),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": round(len(wins) / max(len(pnl), 1), 4),
        "avg_win": round(wins.mean(), 2) if len(wins) > 0 else 0,
        "avg_loss": round(losses.mean(), 2) if len(losses) > 0 else 0,
        "largest_win": round(wins.max(), 2) if len(wins) > 0 else 0,
        "largest_loss": round(losses.min(), 2) if len(losses) > 0 else 0,
        "profit_factor": round(wins.sum() / max(abs(losses.sum()), 1), 2),
        "avg_rr": round(wins.mean() / max(abs(losses.mean()), 1), 2) if len(losses) > 0 else float("inf"),
        "sharpe_ratio": round((pnl.mean() / max(pnl.std(), 0.001)) * np.sqrt(52), 2),
        "max_drawdown": round(drawdown.min(), 2),
        "max_drawdown_pct": round(drawdown.min() / max(peak.max(), 1) * 100, 2),
        "recovery_factor": round(pnl.sum() / max(abs(drawdown.min()), 1), 2),
        "expectancy": round(pnl.mean(), 2),
        "consecutive_wins": _max_streak(pnl > 0),
        "consecutive_losses": _max_streak(pnl <= 0),
    }


def _max_streak(bool_series):
    groups = bool_series.ne(bool_series.shift()).cumsum()
    return int(bool_series.groupby(groups).sum().max()) if len(bool_series) > 0 else 0


def equity_curve(trades_df: pd.DataFrame, initial_capital: float = 500_000) -> pd.DataFrame:
    """Generate equity curve from trades."""
    df = trades_df.copy()
    df["cumulative_pnl"] = df["pnl"].cumsum()
    df["equity"] = initial_capital + df["cumulative_pnl"]
    df["peak_equity"] = df["equity"].cummax()
    df["drawdown"] = df["equity"] - df["peak_equity"]
    df["drawdown_pct"] = df["drawdown"] / df["peak_equity"] * 100
    return df
