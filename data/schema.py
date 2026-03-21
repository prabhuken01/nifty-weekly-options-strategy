"""Data models for option chain snapshots."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OptionChainSnapshot:
    timestamp: datetime
    expiry_date: str
    spot_price: float
    strike_price: float
    instrument_type: str  # "CE" or "PE"

    ltp: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_ask_spread: Optional[float] = None

    iv: float = 0.0
    time_to_expiry: float = 0.0
    tte_trading_days: float = 0.0

    volume: int = 0
    open_interest: int = 0
    oi_change: int = 0

    delta: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    gamma: Optional[float] = None

    moneyness: str = "OTM"
    distance_from_atm_pct: float = 0.0
    rsi_14: float = 50.0
    sma_20: float = 0.0
    sma_50: float = 0.0
    market_condition: str = "sideways"
    vwap: Optional[float] = None
