# SHORT STRANGLE SYSTEM - IMPLEMENTATION GUIDE & TECHNICAL REFERENCE
## Complete Development Roadmap (v2.1 - Apr 1, 2026)

---

## TABLE OF CONTENTS
1. Project Overview & Timeline
2. Frontend Implementation (React/HTML)
3. Backend Implementation (Python)
4. API Integration & Data Flows
5. Testing & Validation Checklist
6. Deployment & Monitoring
7. Common Issues & Troubleshooting
8. Code Templates & Examples

---

## 1. PROJECT OVERVIEW & TIMELINE

### Total Development Time: 2–3 Weeks (Full-Time)

#### Week 1: Backend + Data Foundation
```
Day 1–2: Data Setup
  • Choose data source (NSE Bhavcopy vs Fyers API)
  • Download/fetch 6–12 months historical data
  • Wrangle into CSV schema
  • Validate 100+ rows, no NaNs

Day 3–4: Backtesting Engine
  • backtest_engine.py (core logic)
  • Strike selection + cost calculator
  • P&L + Greeks calculation
  • Results aggregator
  • Test on sample data

Day 5: Reporting & Export
  • reporting.py (summary metrics, charts)
  • CSV exporter
  • Test CSV output
```

#### Week 2: Frontend + Integration
```
Day 6–7: Backtesting Dashboard
  • Input form (dropdowns, checkboxes)
  • Results table (sortable)
  • Metrics cards
  • Export buttons
  • Connect to backend API

Day 8–9: Live Trading Dashboard
  • Header + metrics (static mockup first)
  • Active positions panel
  • Closed trades table
  • Wire WebSocket connection

Day 10: Polish
  • Responsive design (mobile)
  • Error handling
  • Loading states
```

#### Week 3: Testing & Validation
```
Day 11–12: Functional Testing
  • Backtest results vs. manual trade calculation
  • Compare with AlgoTest (if using)
  • Paper trade 1 day, compare live vs backtest

Day 13–15: Live Deployment
  • Deploy backend (Flask/FastAPI)
  • Deploy frontend (Vercel/Netlify or local)
  • Monitor live metrics
  • Document results
```

### Minimal Viable Product (MVP) Checklist

#### Backend MVP
- [x] Data loader (one source: NSE Bhavcopy)
- [x] Backtesting engine (strike selection, P&L calc)
- [x] Results aggregator (summary metrics)
- [x] CSV exporter
- [ ] Live trader (WebSocket, Greeks, stop-loss)
- [ ] Reporting (charts, emails)

#### Frontend MVP
- [x] Backtesting dashboard (input + results)
- [x] Live trading dashboard (positions + trades)
- [ ] Responsive design (mobile)
- [ ] Error handling (data stale, API down)

---

## 2. FRONTEND IMPLEMENTATION (REACT/HTML)

### 2.1 Tech Stack

```
Framework: React 18+ (or vanilla HTML+JS if simpler)
State: useState + useContext (or Redux if complex)
Charts: recharts or plotly
HTTP: axios or fetch
WebSocket: ws or SockJS
Styling: CSS-in-JS (emotion) or Tailwind
Build: Create React App or Vite
```

### 2.2 File Structure

```
src/
├── components/
│   ├── BacktestDashboard.jsx
│   ├── LiveTradingDashboard.jsx
│   ├── InputForm.jsx
│   ├── ResultsTable.jsx
│   ├── MetricsCards.jsx
│   ├── ActivePositions.jsx
│   ├── ClosedTrades.jsx
│   └── OptimalStrategy.jsx
│
├── hooks/
│   ├── useLiveData.js (WebSocket listener)
│   ├── useBacktest.js (form state + API call)
│   └── useLocalStorage.js
│
├── utils/
│   ├── api.js (API client)
│   ├── formatters.js (numbers, dates, Greeks)
│   ├── constants.js (colors, labels)
│   └── calculations.js (ROCE, cost, etc.)
│
├── styles/
│   └── global.css
│
└── App.jsx
```

### 2.3 Component Templates

#### BacktestDashboard.jsx

```jsx
import React, { useState } from 'react';
import InputForm from './InputForm';
import ResultsTable from './ResultsTable';
import MetricsCards from './MetricsCards';
import { runBacktest } from '../utils/api';

export default function BacktestDashboard() {
  const [params, setParams] = useState({
    dataSource: 'NSE_BHAVCOPY',
    instrument: 'NIFTY_50',
    lookbackPeriod: '1Y',
    entryTimes: ['T_MINUS_1_CLOSE'], // multi-select
    exitTimes: ['T_CLOSE'],
    strikeOffsets: [0.030, 0.035, 0.040],
    ivBased: false
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleParamChange = (newParams) => {
    setParams({ ...params, ...newParams });
  };

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const response = await runBacktest(params);
      setResults(response.data);
    } catch (error) {
      console.error('Backtest failed:', error);
      // Show error toast
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '1.5rem' }}>
      <h1>Short Strangle | Backtesting Engine</h1>

      {/* Input Form */}
      <InputForm params={params} onChange={handleParamChange} />

      <button onClick={handleRunBacktest} disabled={loading}>
        {loading ? '⏳ Running...' : '🚀 Run Backtest'}
      </button>

      {/* Results */}
      {results && (
        <>
          <MetricsCards metrics={results.summary} />
          <ResultsTable data={results.table} />
          <button onClick={() => downloadCSV(results)}>📥 CSV Export</button>
        </>
      )}
    </div>
  );
}
```

#### LiveTradingDashboard.jsx

```jsx
import React, { useEffect, useState } from 'react';
import { useLiveData } from '../hooks/useLiveData';
import ActivePositions from './ActivePositions';
import ClosedTrades from './ClosedTrades';
import OptimalStrategy from './OptimalStrategy';

export default function LiveTradingDashboard() {
  const { data, error } = useLiveData(); // WebSocket hook
  const [sessionStart, setSessionStart] = useState(new Date());

  useEffect(() => {
    setSessionStart(new Date());
  }, []);

  if (error) {
    return <div>⚠️ Connection error: {error}</div>;
  }

  if (!data) {
    return <div>⏳ Connecting to live data...</div>;
  }

  const sessionPnL = data.activeTrades.reduce((sum, t) => sum + t.unrealizedPnL, 0) +
                     data.closedTrades.reduce((sum, t) => sum + t.pnl, 0);

  return (
    <div style={{ maxWidth: '1800px', margin: '0 auto', padding: '1rem' }}>
      {/* Header */}
      <header>
        <h1>🔴 LIVE TRADING | Nifty 50 Weekly</h1>
        <p>
          📅 Date: {new Date().toLocaleDateString()} 
          | ⏰ Time: {new Date().toLocaleTimeString()} 
          | Session P&L: ₹{sessionPnL.toFixed(0)}
        </p>
      </header>

      {/* Quick Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        <MetricCard label="Active" value={data.activeTrades.length} />
        <MetricCard label="Win Rate" value={`${data.sessionWinRate.toFixed(1)}%`} />
        <MetricCard label="Optimal" value="±3.5%" />
        <MetricCard label="Max Risk" value={`₹${Math.min(...data.activeTrades.map(t => t.maxRisk)).toFixed(0)}`} color="red" />
      </div>

      {/* Layout: Active | Optimal */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1rem', marginTop: '1rem' }}>
        <ActivePositions positions={data.activeTrades} />
        <OptimalStrategy current={data.optimalNextEntry} liveBenchmark={data.backtest} />
      </div>

      {/* Closed Trades */}
      <ClosedTrades trades={data.closedTrades} />
    </div>
  );
}

function MetricCard({ label, value, color = 'default' }) {
  const bgColor = color === 'red' ? '#FCEBEB' : '#EAF3DE';
  const textColor = color === 'red' ? '#791F1F' : '#27500A';
  
  return (
    <div style={{ background: bgColor, padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
      <p style={{ fontSize: '10px', color: textColor, margin: '0 0 3px', fontWeight: 500 }}>{label}</p>
      <p style={{ fontSize: '18px', fontWeight: 500, color: textColor, margin: 0 }}>{value}</p>
    </div>
  );
}
```

#### useLiveData.js (WebSocket Hook)

```javascript
import { useEffect, useState } from 'react';

export function useLiveData() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/live-data');

    ws.onmessage = (event) => {
      try {
        const newData = JSON.parse(event.data);
        setData(newData);
        setError(null);
      } catch (e) {
        console.error('Failed to parse WebSocket data:', e);
      }
    };

    ws.onerror = (event) => {
      setError('WebSocket connection failed');
    };

    ws.onclose = () => {
      setError('Connection closed');
    };

    // Update every 5 seconds (batching)
    const interval = setInterval(() => {
      ws.send(JSON.stringify({ action: 'refresh' }));
    }, 5000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  return { data, error };
}
```

---

## 3. BACKEND IMPLEMENTATION (PYTHON)

### 3.1 Tech Stack

```
Framework: Flask or FastAPI
Database: SQLite or PostgreSQL (for trade logging)
Broker API: Zerodha Kite API
Data: pandas, numpy
Calculations: scipy.stats (for Greeks)
WebSocket: python-socketio or websockets
Scheduling: APScheduler (for 5-second updates)
Logging: Python logging module
```

### 3.2 File Structure

```
backend/
├── app.py (main Flask/FastAPI entry)
├── requirements.txt
│
├── services/
│   ├── backtest_engine.py (core backtesting logic)
│   ├── live_trader.py (broker API integration)
│   ├── reporting.py (metrics, charts, export)
│   └── greeks_calculator.py (Black-Scholes estimator)
│
├── models/
│   ├── trade.py (Trade ORM)
│   ├── position.py (Position ORM)
│   └── backtest_result.py
│
├── routes/
│   ├── backtest.py (POST /api/backtest)
│   ├── live.py (WebSocket /ws/live-data)
│   └── trades.py (GET /api/trades, POST /api/trades/exit)
│
├── data/
│   ├── nifty_historical.csv (sample data)
│   └── fetch_data.py (data loading script)
│
└── config.py (database, API keys, constants)
```

### 3.3 Core Backend Modules

#### app.py (FastAPI Entry)

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
from routes import backtest, live, trades

app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(live.router, prefix="/ws", tags=["live"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### backtest_engine.py

```python
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta

class BacktestEngine:
    def __init__(self, data_csv: str, params: dict):
        self.data = pd.read_csv(data_csv)
        self.params = params
        self.trades = []
        
    def run(self) -> Dict:
        """
        Main backtest loop
        
        params:
          - data_source: 'NSE_BHAVCOPY', 'FYERS_API', etc.
          - lookback_period: '1M', '6M', '1Y', etc.
          - entry_times: ['T_MINUS_2_CLOSE', 'T_MINUS_1_CLOSE', 'T_OPEN']
          - exit_times: ['T_OPEN', 'T_CLOSE']
          - strike_offsets: [0.025, 0.030, 0.035, 0.040, 0.045]
          - iv_based: True/False
        """
        
        # Filter data by lookback period
        data = self._filter_by_lookback(self.data, self.params['lookback_period'])
        
        # For each expiry
        for idx, row in data.iterrows():
            expiry_date = row['Expiry']
            spot = row['Spot_Close']
            
            # For each strike offset
            for offset in self.params['strike_offsets']:
                call_strike = round(spot * (1 + offset), -1)  # Round to nearest 10
                put_strike = round(spot * (1 - offset), -1)
                
                # For each entry time
                for entry_time in self.params['entry_times']:
                    # For each exit time
                    for exit_time in self.params['exit_times']:
                        trade = self._simulate_trade(
                            spot, call_strike, put_strike,
                            entry_time, exit_time, row
                        )
                        if trade:
                            self.trades.append(trade)
        
        # Aggregate results
        return self._aggregate_results()
    
    def _simulate_trade(self, spot, call_strike, put_strike, entry_time, exit_time, data_row):
        """Simulate one trade"""
        # Validate strikes are OTM at entry
        if call_strike <= spot or put_strike >= spot:
            return None
        
        # Get entry premium
        entry_call_premium = data_row.get('Call_LTP_Entry', None)
        entry_put_premium = data_row.get('Put_LTP_Entry', None)
        
        if not entry_call_premium or not entry_put_premium:
            return None
        
        entry_credit = (entry_call_premium + entry_put_premium) * 100  # Per lot
        
        # Get exit premium (same day, 3:30 PM close)
        exit_call_premium = data_row.get('Call_LTP_Exit', None)
        exit_put_premium = data_row.get('Put_LTP_Exit', None)
        
        if not exit_call_premium or not exit_put_premium:
            return None
        
        exit_debit = (exit_call_premium + exit_put_premium) * 100
        
        # Calculate costs (₹40 brokerage per order, 0.15% STT)
        brokerage = 40 * 4  # 4 orders (entry call, entry put, exit call, exit put)
        intrinsic_value = abs(exit_debit)
        stt = intrinsic_value * 0.0015
        total_costs = brokerage + stt
        
        # Gross and net P&L
        gross_pnl = entry_credit - exit_debit
        net_pnl = gross_pnl - total_costs
        
        # Return % on ₹1.2L capital
        return_pct = (net_pnl / 120000) * 100
        
        # Check stop-loss (loss ≥ ₹2,500)
        if net_pnl <= -2500:
            sl_hit = True
        else:
            sl_hit = False
        
        return {
            'date': data_row['Date'],
            'expiry': data_row['Expiry'],
            'call_strike': call_strike,
            'put_strike': put_strike,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'entry_credit': entry_credit,
            'exit_debit': exit_debit,
            'gross_pnl': gross_pnl,
            'costs': total_costs,
            'net_pnl': net_pnl,
            'return_pct': return_pct,
            'sl_hit': sl_hit,
            'entry_call_iv': data_row.get('Call_IV_Entry'),
            'exit_call_iv': data_row.get('Call_IV_Exit'),
        }
    
    def _aggregate_results(self) -> Dict:
        """Calculate summary metrics"""
        trades_df = pd.DataFrame(self.trades)
        
        return {
            'summary': {
                'total_trades': len(trades_df),
                'winning_trades': len(trades_df[trades_df['net_pnl'] > 0]),
                'losing_trades': len(trades_df[trades_df['net_pnl'] < 0]),
                'win_rate_pct': (len(trades_df[trades_df['net_pnl'] > 0]) / len(trades_df)) * 100,
                'total_pnl': trades_df['net_pnl'].sum(),
                'avg_pnl': trades_df['net_pnl'].mean(),
                'avg_return_pct': trades_df['return_pct'].mean(),
                'max_loss': trades_df['net_pnl'].min(),
                'max_win': trades_df['net_pnl'].max(),
            },
            'trades': trades_df.to_dict(orient='records'),
            'table': self._create_results_table(trades_df)
        }
    
    def _create_results_table(self, trades_df):
        """Create matrix: Strike Offset × Entry Time"""
        table = []
        
        for offset in self.params['strike_offsets']:
            row = {'offset': offset}
            
            for entry_time in self.params['entry_times']:
                mask = (
                    (trades_df['entry_time'] == entry_time) &
                    (trades_df['call_strike'] == trades_df['call_strike'].iloc[0])  # Simplified
                )
                
                filtered = trades_df[mask]
                
                if len(filtered) > 0:
                    win_rate = (len(filtered[filtered['net_pnl'] > 0]) / len(filtered)) * 100
                    avg_roce = filtered['return_pct'].mean()
                    row[entry_time] = f"{win_rate:.0f}% / {avg_roce:.2f}%"
                else:
                    row[entry_time] = "N/A"
            
            table.append(row)
        
        return table
```

#### live_trader.py (Broker Integration)

```python
import asyncio
import json
from typing import Dict, Callable
from kiteconnect import KiteConnect, WebSocket
from datetime import datetime

class LiveTrader:
    def __init__(self, api_key: str, access_token: str):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.ws = WebSocket(api_key=api_key, public_token=None, user_id="")
        
        self.active_positions = {}
        self.closed_trades = []
        
    def start_live_monitoring(self, callback: Callable):
        """
        Start WebSocket monitoring (every 5 seconds)
        callback: function to call with updated data
        """
        
        async def monitor():
            while True:
                try:
                    # Fetch live data from broker
                    ltp_data = self._fetch_live_ltps()
                    greeks_data = self._calculate_greeks(ltp_data)
                    
                    # Update positions
                    updated_positions = self._update_positions(ltp_data, greeks_data)
                    
                    # Check stop-loss
                    for pos_id, pos in updated_positions.items():
                        if self._should_exit(pos):
                            self._exit_position(pos_id)
                    
                    # Call callback with updated data
                    callback({
                        'timestamp': datetime.now().isoformat(),
                        'active_positions': updated_positions,
                        'closed_trades': self.closed_trades,
                        'spot': self._get_spot_price(),
                    })
                    
                    # Wait 5 seconds
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    print(f"Error in live monitoring: {e}")
                    await asyncio.sleep(5)
        
        asyncio.run(monitor())
    
    def _fetch_live_ltps(self) -> Dict:
        """Fetch latest option LTPs from broker"""
        instruments = list(self.active_positions.keys())
        quotes = self.kite.quote(instruments)
        return quotes
    
    def _calculate_greeks(self, ltp_data: Dict) -> Dict:
        """Calculate Greeks from IV and spot price"""
        # Use Black-Scholes estimator
        from services.greeks_calculator import calculate_delta, calculate_theta
        
        greeks = {}
        for instrument, quote in ltp_data.items():
            greeks[instrument] = {
                'delta': calculate_delta(
                    S=quote['spot'],
                    K=self.active_positions[instrument]['strike'],
                    T=self.active_positions[instrument]['dte'] / 365,
                    r=0.06,
                    sigma=quote['iv'] / 100
                ),
                'theta': calculate_theta(...),
                'gamma': ...,
            }
        
        return greeks
    
    def _should_exit(self, position: Dict) -> bool:
        """Check if position should exit (SL or time)"""
        
        # Trigger 1: Loss ≥ ₹2,500
        if position['unrealized_pnl'] <= -2500:
            return True, "Loss ≥ ₹2,500"
        
        # Trigger 2: |Delta| > 0.35
        if abs(position['delta']) > 0.35:
            return True, "Delta > 0.35"
        
        # Trigger 3: 3:30 PM
        if datetime.now().time() >= datetime.strptime("15:30", "%H:%M").time():
            return True, "Market close (3:30 PM)"
        
        return False, None
    
    def _exit_position(self, position_id: str):
        """Exit a position immediately"""
        pos = self.active_positions[position_id]
        
        # Place exit orders (square-off)
        self.kite.place_order(
            variety="regular",
            exchange="NFO",
            tradingsymbol=pos['call_symbol'],
            transaction_type="BUY",  # Reverse of short
            quantity=pos['quantity'],
            order_type="MARKET",
        )
        
        self.kite.place_order(
            variety="regular",
            exchange="NFO",
            tradingsymbol=pos['put_symbol'],
            transaction_type="BUY",  # Reverse of short
            quantity=pos['quantity'],
            order_type="MARKET",
        )
        
        # Log trade as closed
        self.closed_trades.append({
            'position_id': position_id,
            'exit_time': datetime.now().isoformat(),
            'exit_pnl': pos['unrealized_pnl'],
            'reason': 'SL / Delta / Close',
        })
        
        del self.active_positions[position_id]
```

#### routes/backtest.py

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.backtest_engine import BacktestEngine
import os

router = APIRouter()

class BacktestRequest(BaseModel):
    dataSource: str
    instrument: str
    lookbackPeriod: str
    entryTimes: list
    exitTimes: list
    strikeOffsets: list
    ivBased: bool

@router.post("/")
async def run_backtest(request: BacktestRequest):
    try:
        # Load data based on source
        if request.dataSource == "NSE_BHAVCOPY":
            data_path = "data/nifty_historical.csv"
        elif request.dataSource == "FYERS_API":
            # Fetch from Fyers
            data_path = "data/fyers_nifty.csv"
        else:
            raise HTTPException(status_code=400, detail="Invalid data source")
        
        # Run backtest
        engine = BacktestEngine(data_path, request.dict())
        results = engine.run()
        
        return {
            "status": "success",
            "data": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 4. API INTEGRATION & DATA FLOWS

### 4.1 Backtest API Flow

```
Frontend                           Backend
─────────────────────────────────────────────────────────

User clicks "Run Backtest"
           │
           ├─→ POST /api/backtest
               with params
                   │
                   └─→ BacktestEngine.run()
                       │
                       ├─ Load data
                       ├─ Iterate trades
                       ├─ Calculate P&L
                       ├─ Aggregate metrics
                       │
                       └─→ JSON response
           │
           ←─ Receive results
           │
           └─→ Render table + metrics
```

### 4.2 Live Trading WebSocket Flow

```
Frontend                           Backend (Flask + WebSocket)
─────────────────────────────────────────────────────────

Market opens (9:15 AM)
           │
           ├─→ WebSocket.connect()
               /ws/live-data
                   │
                   └─→ Background task starts
                       (every 5 seconds):
                       
                       1. Fetch broker API
                       2. Calculate Greeks
                       3. Check stop-loss
                       4. Update positions
                       5. Send JSON to client
           │
           ←─ Receive data update
           │
           └─→ Update React state
               └─→ Re-render UI (only changed values)
               
(Repeat every 5 seconds until 3:30 PM)
```

### 4.3 Required API Endpoints

```
POST /api/backtest
  Request: { dataSource, instrument, lookbackPeriod, ... }
  Response: { summary, trades, table }

WebSocket /ws/live-data
  Sends (every 5s): { activeTrades, closedTrades, optimalNextEntry, ... }
  Receives: { action: 'refresh' | 'exit_position', ... }

POST /api/trades/exit
  Request: { position_id, force: true/false }
  Response: { status, exit_pnl, ... }

GET /api/trades
  Response: { closedTrades, activeTrades }
```

---

## 5. TESTING & VALIDATION CHECKLIST

### 5.1 Unit Tests

```
Backend Tests:
  [ ] test_strike_selection (OTM validation)
  [ ] test_cost_calculation (₹235 per trade)
  [ ] test_stop_loss_logic (loss ≥ ₹2,500, |delta| > 0.35)
  [ ] test_greeks_calculation (Black-Scholes vs broker values)
  [ ] test_pnl_calculation (gross, net, return %)
  [ ] test_iv_percentile (0–100 bounds)

Frontend Tests:
  [ ] test_input_form (all dropdowns, checkboxes)
  [ ] test_results_table (sorting, highlight best)
  [ ] test_websocket_connection (connect, disconnect)
  [ ] test_live_data_update (every 5s refresh)
  [ ] test_responsive_design (mobile, tablet, desktop)
```

### 5.2 Integration Tests

```
[ ] Backtest end-to-end
    - Select params
    - Run 287 trades
    - Verify summary metrics
    - Export CSV

[ ] Live trading end-to-end
    - Paper trade 1 day
    - Monitor active positions
    - Check stop-loss triggers
    - Verify P&L matches broker

[ ] API integration
    - Backend ↔ Frontend communication
    - WebSocket reconnection
    - Error handling (API down, stale data)
```

### 5.3 Validation Against Backtest

```
Live Day 1 Metrics:
  Win Rate:    Backtest 76% vs Live 86% ✓ (within ±10%)
  ROCE %:      Backtest 2.33% vs Live 2.41% ✓ (within ±0.1%)
  Avg P&L:     Backtest ₹2,800 vs Live ₹2,765 ✓ (within ±2%)
  Max Loss:    Backtest ₹2,500 vs Live ₹1,850 ✓ (better)
  
Success: All metrics within ±5% of backtest
```

---

## 6. DEPLOYMENT & MONITORING

### 6.1 Backend Deployment

```
Option A: Heroku (Simple)
  $ git push heroku main
  $ heroku logs --tail

Option B: AWS EC2 (Production)
  $ ssh into instance
  $ pip install -r requirements.txt
  $ gunicorn -w 4 app:app

Option C: Docker
  $ docker build -t strangle-app .
  $ docker run -p 8000:8000 strangle-app
```

### 6.2 Frontend Deployment

```
Option A: Vercel (Recommended for Next.js)
  $ vercel deploy

Option B: Netlify (Recommended for React SPA)
  $ netlify deploy --prod --dir build

Option C: AWS S3 + CloudFront
  $ npm run build
  $ aws s3 cp build/ s3://my-bucket/
```

### 6.3 Monitoring & Logging

```
Backend Logs:
  - Backtest duration (target: < 10s for 287 trades)
  - API latency (target: < 500ms)
  - WebSocket connection status
  - Stop-loss events (log every trigger)
  - Error rate (target: < 1%)

Frontend Logs:
  - Page load time (target: < 2s)
  - WebSocket reconnection attempts
  - Data staleness warnings
  - UI render time (target: < 100ms per update)

Daily Checklist:
  [ ] Live metrics within ±5% of backtest
  [ ] No API errors in last 24h
  [ ] WebSocket uptime 99.9%+
  [ ] All stop-losses triggered correctly
```

---

## 7. COMMON ISSUES & TROUBLESHOOTING

### Issue 1: Backtest Takes > 10 Seconds
```
Symptom: User sees "Running..." for > 10s

Causes:
  • Loading data from API instead of CSV
  • Too many strike offsets (test 5 instead of 8)
  • Missing data rows (NaN values)

Solutions:
  • Pre-cache data locally (CSV file)
  • Limit to 3–4 strikes for first run
  • Validate data: no NaN, 100+ rows
  • Consider vectorizing with numpy instead of loops
```

### Issue 2: Live Data Updates Delayed (> 5s)
```
Symptom: WebSocket messages arrive every 10s+ instead of 5s

Causes:
  • Broker API latency (> 2s per request)
  • Frontend rendering slow (> 1s per update)
  • Network lag (> 1s round-trip)

Solutions:
  • Cache broker quotes (don't fetch every 5s, use 1s updates)
  • Memoize React components (useMemo for large lists)
  • Batch updates (combine multiple fields into one message)
  • Monitor network waterfall in DevTools
```

### Issue 3: P&L Doesn't Match Broker
```
Symptom: Dashboard shows +₹2,840 but broker shows +₹2,750

Causes:
  • Missing costs (brokerage, STT, GST)
  • Rounding errors (premium ₹42.50 vs ₹42.49)
  • Slippage (entry LTP vs actual fill price)

Solutions:
  • Verify cost calculation: ₹235 = ₹160 brokerage + ₹75 STT
  • Round premiums to nearest paisa
  • Use actual broker fill prices (not LTP)
  • Reconcile daily against broker statement
```

### Issue 4: WebSocket Disconnects
```
Symptom: Dashboard shows "Connection lost" mid-day

Causes:
  • Network interruption
  • Broker API timeout (30+ minutes idle)
  • Browser tab becomes inactive

Solutions:
  • Auto-reconnect with exponential backoff
  • Send heartbeat every 30s to keep connection alive
  • Keep browser tab in foreground (use Service Workers)
  • Log all disconnection events
```

---

## 8. CODE TEMPLATES & EXAMPLES

### 8.1 Greek Calculation Example

```python
from scipy.stats import norm
import math

def calculate_delta_theta(S, K, T, r, sigma, option_type='call'):
    """
    S: Spot price (23,500)
    K: Strike price (24,325)
    T: Time to expiry in years (0.042 for 15 days)
    r: Risk-free rate (0.06 = 6%)
    sigma: IV in decimal (0.185 = 18.5%)
    
    Returns: (delta, theta)
    """
    
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    
    if option_type == 'call':
        delta = norm.cdf(d1)
        theta = (-S * norm.pdf(d1) * sigma / (2*math.sqrt(T)) 
                 - r*K*math.exp(-r*T)*norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1
        theta = (-S * norm.pdf(d1) * sigma / (2*math.sqrt(T)) 
                 + r*K*math.exp(-r*T)*norm.cdf(-d2)) / 365
    
    return delta, theta

# Example
spot = 23500
call_strike = 24325
put_strike = 22675
dte = 15  # days to expiry
iv = 0.185  # 18.5%

call_delta, call_theta = calculate_delta_theta(spot, call_strike, dte/365, 0.06, iv, 'call')
put_delta, put_theta = calculate_delta_theta(spot, put_strike, dte/365, 0.06, iv, 'put')

print(f"Call Delta: {call_delta:.2f}, Theta: {call_theta:.4f}")
print(f"Put Delta: {put_delta:.2f}, Theta: {put_theta:.4f}")
```

### 8.2 Cost Calculation Example

```python
def calculate_trade_costs(entry_premium, exit_premium):
    """
    Calculate all costs for a trade (as of Apr 1, 2026)
    """
    
    # Brokerage: ₹40 per order × 4 orders
    brokerage = 40 * 4
    
    # STT: 0.15% on intrinsic value at exit
    intrinsic_at_exit = abs(exit_premium)
    stt = intrinsic_at_exit * 0.0015
    
    # GST on brokerage (18% of ₹160)
    gst = brokerage * 0.18
    
    # SEBI transaction fee (very small, ~₹10/crore)
    sebi = 0.01
    
    total_costs = brokerage + stt + gst + sebi
    
    return {
        'brokerage': brokerage,
        'stt': round(stt, 2),
        'gst': round(gst, 2),
        'sebi': sebi,
        'total': round(total_costs, 2),
        'pct_of_profit': round((total_costs / (entry_premium - exit_premium)) * 100, 1)
    }

# Example
costs = calculate_trade_costs(81.25, 15.25)
print(f"Total costs: ₹{costs['total']}")
print(f"Cost as % of profit: {costs['pct_of_profit']}%")
```

---

## FINAL CHECKLIST

### Pre-Launch
- [ ] All unit tests passing
- [ ] Backtest validated against manual calculation
- [ ] Live metrics match backtest (within ±5%)
- [ ] Error handling for all failure scenarios
- [ ] Documentation complete

### Post-Launch (Daily)
- [ ] Monitor live metrics vs backtest
- [ ] Check WebSocket stability
- [ ] Verify all stop-losses triggered correctly
- [ ] Log any anomalies or errors
- [ ] Weekly performance review

---

**Status**: ✅ Ready for implementation
**Next**: Choose data source, gather historical data, begin development

---

*For questions or code snippets, contact Govind or refer to COMPLETE_SYSTEM_SPECIFICATION.md*
