"""Strategy payoff calculators for all spread types."""

import numpy as np
import pandas as pd


def bull_call_payoff(spot_range, buy_strike, sell_strike, net_premium, lot_size=50):
    payoff = np.minimum(np.maximum(spot_range - buy_strike, 0), sell_strike - buy_strike) - net_premium
    return payoff * lot_size


def bear_put_payoff(spot_range, buy_strike, sell_strike, net_premium, lot_size=50):
    payoff = np.minimum(np.maximum(buy_strike - spot_range, 0), buy_strike - sell_strike) - net_premium
    return payoff * lot_size


def long_strangle_payoff(spot_range, put_strike, call_strike, net_premium, lot_size=50):
    call_payoff = np.maximum(spot_range - call_strike, 0)
    put_payoff = np.maximum(put_strike - spot_range, 0)
    return (call_payoff + put_payoff - net_premium) * lot_size


def short_strangle_payoff(spot_range, put_strike, call_strike, net_premium, lot_size=50):
    return -long_strangle_payoff(spot_range, put_strike, call_strike, net_premium, lot_size) + 2 * net_premium * lot_size


def long_straddle_payoff(spot_range, strike, net_premium, lot_size=50):
    return (np.abs(spot_range - strike) - net_premium) * lot_size


def short_straddle_payoff(spot_range, strike, net_premium, lot_size=50):
    return (net_premium - np.abs(spot_range - strike)) * lot_size


def iron_condor_payoff(spot_range, put_buy, put_sell, call_sell, call_buy, net_credit, lot_size=50):
    put_spread = np.maximum(put_sell - spot_range, 0) - np.maximum(put_buy - spot_range, 0)
    call_spread = np.maximum(spot_range - call_sell, 0) - np.maximum(spot_range - call_buy, 0)
    return (net_credit - put_spread - call_spread) * lot_size


def payoff_summary(payoff_array):
    return {
        "max_profit": float(np.max(payoff_array)),
        "max_loss": float(np.min(payoff_array)),
        "breakeven_count": int(np.sum(np.diff(np.sign(payoff_array)) != 0)),
    }
