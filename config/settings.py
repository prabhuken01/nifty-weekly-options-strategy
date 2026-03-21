"""Central configuration for the NIFTY Weekly Options Trading Model."""

NIFTY_LOT_SIZE = 50
RISK_FREE_RATE = 0.065  # ~6.5% India 10Y yield
MAX_LOSS_PCT = 0.02     # 2% of capital per trade
DEFAULT_CAPITAL = 500_000

INDICATOR_PARAMS = {
    "rsi_period": 14,
    "sma_fast": 20,
    "sma_slow": 50,
    "bollinger_period": 20,
    "bollinger_std": 2,
}

MARKET_CONDITION_THRESHOLDS = {
    "bullish_rsi": 60,
    "bearish_rsi": 40,
    "high_vol_multiplier": 1.25,
}

LIQUIDITY_FILTERS = {
    "min_oi": 50_000,
    "min_volume": 500,
    "max_spread_pct": 0.05,
}

STRATEGY_PARAMS = {
    "min_risk_reward": 1.5,
    "min_pop": 0.45,
    "stop_loss_multiplier": 1.5,
    "target_pct_of_max": 0.75,
}

MONTE_CARLO_SIMS = 50_000

STRIKE_SELECTION = {
    "pct_otm_levels": [0.01, 0.02, 0.03],
    "delta_pairs": [(0.5, 0.3), (0.4, 0.2)],
    "strangle_delta_range": (0.15, 0.25),
}
