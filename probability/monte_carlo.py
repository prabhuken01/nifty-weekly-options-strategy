"""Monte Carlo simulation for probability and payoff estimation."""

import numpy as np
from config.settings import RISK_FREE_RATE, MONTE_CARLO_SIMS


def simulate_terminal_prices(spot, iv, tte_years, n_sims=MONTE_CARLO_SIMS,
                              r=RISK_FREE_RATE, seed=42):
    """Simulate terminal NIFTY prices using GBM."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n_sims)
    return spot * np.exp((r - 0.5 * iv**2) * tte_years + iv * np.sqrt(tte_years) * z)


def mc_pop_above(spot, target, iv, tte_years, n_sims=MONTE_CARLO_SIMS):
    terminals = simulate_terminal_prices(spot, iv, tte_years, n_sims)
    return float((terminals >= target).mean())


def mc_pop_between(spot, lower, upper, iv, tte_years, n_sims=MONTE_CARLO_SIMS):
    terminals = simulate_terminal_prices(spot, iv, tte_years, n_sims)
    return float(((terminals >= lower) & (terminals <= upper)).mean())


def spread_expected_payoff(spot, buy_strike, sell_strike, iv, tte_years,
                            net_premium, spread_type="bull_call",
                            n_sims=MONTE_CARLO_SIMS):
    """Full payoff analysis for a vertical spread."""
    terminals = simulate_terminal_prices(spot, iv, tte_years, n_sims)
    width = abs(sell_strike - buy_strike)

    if spread_type == "bull_call":
        payoffs = np.clip(terminals - buy_strike, 0, width) - net_premium
    elif spread_type == "bear_put":
        payoffs = np.clip(buy_strike - terminals, 0, width) - net_premium
    elif spread_type == "long_strangle":
        call_payoff = np.maximum(terminals - sell_strike, 0)
        put_payoff = np.maximum(buy_strike - terminals, 0)
        payoffs = call_payoff + put_payoff - net_premium
    elif spread_type == "short_strangle":
        call_payoff = np.maximum(terminals - sell_strike, 0)
        put_payoff = np.maximum(buy_strike - terminals, 0)
        payoffs = net_premium - call_payoff - put_payoff
    else:
        payoffs = np.zeros(n_sims)

    winners = payoffs[payoffs > 0]
    losers = payoffs[payoffs < 0]

    return {
        "pop": float((payoffs > 0).mean()),
        "expected_payoff": float(payoffs.mean()),
        "max_profit": float(payoffs.max()),
        "max_loss": float(payoffs.min()),
        "avg_win": float(winners.mean()) if len(winners) > 0 else 0,
        "avg_loss": float(losers.mean()) if len(losers) > 0 else 0,
        "risk_reward": abs(winners.mean() / losers.mean()) if len(losers) > 0 and losers.mean() != 0 else float("inf"),
        "payoff_distribution": payoffs,
    }


def historical_pop(spot, target_price, mu_daily, sigma_daily, tte_days,
                   n_sims=MONTE_CARLO_SIMS):
    """Historical distribution-based POP using actual return stats."""
    rng = np.random.default_rng(42)
    log_returns = rng.normal(mu_daily, sigma_daily, (n_sims, tte_days))
    terminal = spot * np.exp(log_returns.sum(axis=1))
    return float((terminal >= target_price).mean())
