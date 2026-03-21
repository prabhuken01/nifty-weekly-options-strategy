"""Strike selection logic: delta-based, %OTM, and IV-based combos."""

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import numpy as np
from config.settings import LIQUIDITY_FILTERS, NIFTY_LOT_SIZE, STRIKE_SELECTION


@dataclass
class StrikeCombo:
    label: str
    strategy: str
    buy_strike: float
    sell_strike: float
    buy_ltp: float
    sell_ltp: float
    net_premium: float
    max_profit: float
    max_loss: float
    breakeven: float
    buy_delta: float
    sell_delta: float
    buy_iv: float
    sell_iv: float


class StrikeSelector:
    def __init__(self, chain_df: pd.DataFrame, spot: float, lot_size: int = NIFTY_LOT_SIZE):
        self.chain = chain_df
        self.spot = spot
        self.lot_size = lot_size

    def _liquidity_ok(self, row) -> bool:
        if row.get("ask") and row.get("bid") and row.get("ltp"):
            spread_ok = (row["ask"] - row["bid"]) / max(row["ltp"], 0.01) < LIQUIDITY_FILTERS["max_spread_pct"]
        else:
            spread_ok = True
        return (row.get("open_interest", 0) >= LIQUIDITY_FILTERS["min_oi"]
                and row.get("volume", 0) >= LIQUIDITY_FILTERS["min_volume"]
                and spread_ok)

    def _nearest_strike(self, df, target):
        if df.empty:
            return None
        idx = (df["strike_price"] - target).abs().idxmin()
        return df.loc[idx]

    def _by_delta(self, df, target_delta):
        candidates = df[df["delta"].notna()]
        if candidates.empty:
            return None
        idx = (candidates["delta"].abs() - abs(target_delta)).abs().idxmin()
        return candidates.loc[idx]

    def _build_bull_call(self, label, buy_row, sell_row) -> Optional[StrikeCombo]:
        if buy_row is None or sell_row is None:
            return None
        net = buy_row["ltp"] - sell_row["ltp"]
        width = sell_row["strike_price"] - buy_row["strike_price"]
        if width <= 0:
            return None
        return StrikeCombo(
            label=label, strategy="bull_call_spread",
            buy_strike=buy_row["strike_price"], sell_strike=sell_row["strike_price"],
            buy_ltp=buy_row["ltp"], sell_ltp=sell_row["ltp"],
            net_premium=round(net, 2),
            max_profit=round(width - net, 2) * self.lot_size,
            max_loss=round(net, 2) * self.lot_size,
            breakeven=round(buy_row["strike_price"] + net, 2),
            buy_delta=buy_row.get("delta", 0), sell_delta=sell_row.get("delta", 0),
            buy_iv=buy_row.get("iv", 0), sell_iv=sell_row.get("iv", 0),
        )

    def _build_bear_put(self, label, buy_row, sell_row) -> Optional[StrikeCombo]:
        if buy_row is None or sell_row is None:
            return None
        net = buy_row["ltp"] - sell_row["ltp"]
        width = buy_row["strike_price"] - sell_row["strike_price"]
        if width <= 0:
            return None
        return StrikeCombo(
            label=label, strategy="bear_put_spread",
            buy_strike=buy_row["strike_price"], sell_strike=sell_row["strike_price"],
            buy_ltp=buy_row["ltp"], sell_ltp=sell_row["ltp"],
            net_premium=round(net, 2),
            max_profit=round(width - net, 2) * self.lot_size,
            max_loss=round(net, 2) * self.lot_size,
            breakeven=round(buy_row["strike_price"] - net, 2),
            buy_delta=buy_row.get("delta", 0), sell_delta=sell_row.get("delta", 0),
            buy_iv=buy_row.get("iv", 0), sell_iv=sell_row.get("iv", 0),
        )

    def get_bull_call_combos(self) -> List[StrikeCombo]:
        calls = self.chain[self.chain["instrument_type"] == "CE"].copy()
        combos = []

        for pct in STRIKE_SELECTION["pct_otm_levels"]:
            buy = self._nearest_strike(calls, self.spot)
            sell = self._nearest_strike(calls, self.spot * (1 + pct))
            combo = self._build_bull_call(f"OTM_{int(pct*100)}%", buy, sell)
            if combo:
                combos.append(combo)

        for buy_d, sell_d in STRIKE_SELECTION["delta_pairs"]:
            buy = self._by_delta(calls, buy_d)
            sell = self._by_delta(calls, sell_d)
            combo = self._build_bull_call(f"Delta_{buy_d:.1f}_{sell_d:.1f}", buy, sell)
            if combo:
                combos.append(combo)

        return combos

    def get_bear_put_combos(self) -> List[StrikeCombo]:
        puts = self.chain[self.chain["instrument_type"] == "PE"].copy()
        combos = []

        for pct in STRIKE_SELECTION["pct_otm_levels"]:
            buy = self._nearest_strike(puts, self.spot)
            sell = self._nearest_strike(puts, self.spot * (1 - pct))
            combo = self._build_bear_put(f"OTM_{int(pct*100)}%", buy, sell)
            if combo:
                combos.append(combo)

        return combos

    def get_strangle_combos(self, short=True) -> List[StrikeCombo]:
        calls = self.chain[self.chain["instrument_type"] == "CE"]
        puts = self.chain[self.chain["instrument_type"] == "PE"]
        combos = []

        for pct in [0.02, 0.03, 0.04]:
            call_strike = self._nearest_strike(calls, self.spot * (1 + pct))
            put_strike = self._nearest_strike(puts, self.spot * (1 - pct))
            if call_strike is None or put_strike is None:
                continue

            premium = call_strike["ltp"] + put_strike["ltp"]
            label = f"{'Short' if short else 'Long'}_{int(pct*100)}%"

            combos.append(StrikeCombo(
                label=label,
                strategy="short_strangle" if short else "long_strangle",
                buy_strike=put_strike["strike_price"],
                sell_strike=call_strike["strike_price"],
                buy_ltp=put_strike["ltp"], sell_ltp=call_strike["ltp"],
                net_premium=round(premium, 2),
                max_profit=round(premium, 2) * self.lot_size if short else float("inf"),
                max_loss=float("inf") if short else round(premium, 2) * self.lot_size,
                breakeven=round(self.spot, 2),
                buy_delta=put_strike.get("delta", 0),
                sell_delta=call_strike.get("delta", 0),
                buy_iv=put_strike.get("iv", 0),
                sell_iv=call_strike.get("iv", 0),
            ))

        return combos

    def get_long_strangle_combos(self) -> List[StrikeCombo]:
        return self.get_strangle_combos(short=False)

    def get_short_strangle_combos(self) -> List[StrikeCombo]:
        return self.get_strangle_combos(short=True)
