# ⚡ NIFTY Weekly Options — Quantitative Trading Dashboard

A comprehensive, production-grade Streamlit dashboard for analyzing NIFTY weekly options strategies with real-time Greeks, Monte Carlo simulations, backtesting, and automated trade signal generation.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

### 📈 Market Overview
- Interactive candlestick charts with SMA, EMA, Bollinger Bands
- RSI, VWAP, ATR technical indicators
- Market regime classification (Bullish / Bearish / Sideways / High Volatility)

### 🔗 Option Chain Analysis
- Full option chain with Greeks (Delta, Gamma, Theta, Vega)
- Open Interest distribution & IV smile/skew visualization
- Put-Call Ratio & Max Pain calculation
- Liquidity filtering (OI, Volume, Bid-Ask spread)

### 🎯 Strategy Builder
- Interactive payoff diagrams for 7 strategies:
  - Bull Call Spread, Bear Put Spread
  - Long/Short Strangle, Long/Short Straddle
  - Iron Condor
- Real-time breakeven, max profit/loss, risk:reward calculation

### 🎲 Monte Carlo Lab
- GBM-based terminal price simulation (up to 100K paths)
- Probability cones with ±1σ bands
- Black-Scholes vs Monte Carlo POP comparison
- Distribution statistics (mean, median, skew, percentiles)

### 📊 Backtest Engine
- 52-week backtest with equity curve & drawdown analysis
- Sharpe ratio, profit factor, win rate, max drawdown
- Strategy-level performance breakdown
- Detailed trade log

### 🚀 Trade Signals
- Automated signal generation based on market condition
- Delta-based and %OTM strike selection
- Confidence scoring (High / Medium / Low)
- POP and Risk:Reward filtering

## Project Structure

```
nifty_options_model/
├── config/settings.py           # Parameters & thresholds
├── data/
│   ├── schema.py                # OptionChainSnapshot dataclass
│   └── sample_data.py           # Synthetic data generator
├── indicators/technical.py      # RSI, SMA, VWAP, Bollinger, ATR
├── market_condition/classifier.py
├── options/
│   ├── chain_processor.py       # Chain enrichment, PCR, Max Pain
│   ├── greeks.py                # Black-Scholes Greeks
│   └── liquidity_filter.py      # OI/Volume/Spread filters
├── strike_selection/selector.py # Delta & %OTM combo builder
├── probability/
│   ├── black_scholes.py         # Analytical POP
│   ├── monte_carlo.py           # GBM simulation engine
│   └── pop_estimator.py         # Blended POP estimator
├── strategy/spreads.py          # Payoff calculators
├── backtest/
│   ├── engine.py                # Backtest framework
│   └── metrics.py               # Performance analytics
├── decision/engine.py           # Signal generator
├── app.py                       # Streamlit dashboard
└── requirements.txt
```

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud

- **Main file:** `app.py` (repo root)
- **Python:** 3.10–3.12 supported via `requirements.txt`
- If you see a redacted `ImportError`, open **Manage app → Logs**. Common fix: ensure `requirements.txt` installs fully (this repo includes `jinja2` for pandas compatibility).

## Configuration

All parameters are centralized in `config/settings.py`:
- Lot size, risk-free rate, capital
- Indicator periods (RSI, SMA, Bollinger)
- Market condition thresholds
- Liquidity filters
- Strategy parameters (min R:R, min POP)
- Monte Carlo simulation count

## Roadmap

| Phase | Milestone |
|-------|-----------|
| 1 | ✅ Core indicators & market classifier |
| 2 | ✅ Option chain processor & Greeks |
| 3 | ✅ Strike selection engine |
| 4 | ✅ Probability models (BS + MC) |
| 5 | ✅ Strategy payoff calculators |
| 6 | ✅ Backtest engine & metrics |
| 7 | ✅ Decision engine & signals |
| 8 | ✅ Streamlit dashboard |
| 9 | 🔲 Broker API integration (Zerodha/Upstox) |
| 10 | 🔲 Paper trading → Live |

## Tech Stack

- **Python 3.11+** — Core language
- **Streamlit** — Dashboard framework
- **Plotly** — Interactive visualizations
- **NumPy / Pandas** — Data processing
- **SciPy** — Statistical distributions

---

*Data shown in the dashboard is simulated for demonstration. Connect a broker API for live data.*
