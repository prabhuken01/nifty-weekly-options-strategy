"""Backtesting engine for weekly options strategies."""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List


@dataclass
class BacktestTrade:
    expiry: str
    strategy: str
    combo_label: str
    entry_premium: float
    exit_premium: float
    pnl: float
    pnl_pct: float
    won: bool


@dataclass
class BacktestResult:
    strategy: str
    trades: List[BacktestTrade] = field(default_factory=list)

    @property
    def total_pnl(self):
        return sum(t.pnl for t in self.trades)

    @property
    def win_rate(self):
        return sum(t.won for t in self.trades) / max(len(self.trades), 1)

    @property
    def avg_rr(self):
        wins = [t.pnl for t in self.trades if t.won]
        losses = [abs(t.pnl) for t in self.trades if not t.won]
        if not losses:
            return float("inf")
        return (sum(wins) / max(len(wins), 1)) / (sum(losses) / len(losses))

    @property
    def sharpe(self):
        pnls = pd.Series([t.pnl_pct for t in self.trades])
        if pnls.std() == 0:
            return 0.0
        return float((pnls.mean() / pnls.std()) * (52**0.5))

    @property
    def max_drawdown(self):
        cumulative = pd.Series([t.pnl for t in self.trades]).cumsum()
        peak = cumulative.cummax()
        return float((cumulative - peak).min())

    @property
    def profit_factor(self):
        gross_profit = sum(t.pnl for t in self.trades if t.won)
        gross_loss = abs(sum(t.pnl for t in self.trades if not t.won))
        return gross_profit / max(gross_loss, 1)

    def to_dict(self):
        return {
            "strategy": self.strategy,
            "total_pnl": round(self.total_pnl, 2),
            "win_rate": round(self.win_rate, 4),
            "avg_rr": round(self.avg_rr, 2),
            "sharpe": round(self.sharpe, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "profit_factor": round(self.profit_factor, 2),
            "n_trades": len(self.trades),
        }
