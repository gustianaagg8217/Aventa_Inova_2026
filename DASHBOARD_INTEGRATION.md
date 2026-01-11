# Dashboard Integration Guide

## Overview

Dashboard.py adalah komponen pusat yang mengintegrasikan semua subsistem Aventa Inova 2026. Menampilkan data real-time dari:

- **auto_trading.py** → Trading bot activity & open positions
- **real_time_monitor.py** → ML predictions & model signals
- **signal_service.py** → Telegram signal broadcasts
- **analytics.py** → Performance metrics & statistics
- **live_analytics.py** → Real-time performance tracking

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARD.PY                              │
│                   (Central Display)                          │
└─────────────────────────────────────────────────────────────┘
                            ▲
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   AUTO_TRADING   │ │ REAL_TIME_       │ │  SIGNAL_         │
│      (BOT)       │ │  MONITOR (ML)    │ │  SERVICE         │
│                  │ │                  │ │  (Telegram)      │
└──────────────────┘ └──────────────────┘ └──────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
  bot_trades.csv  realtime_predictions  signal_history.csv
  bot_state.json      .jsonl             (CSV)
  bot_closed_
  trades.csv
```

## File Dependencies

### Input Files (Read by Dashboard)

| File | Source | Purpose | Update Frequency |
|------|--------|---------|------------------|
| `bot_trades.csv` | auto_trading.py | Active/open trades | Real-time (each trade) |
| `bot_state.json` | auto_trading.py | Bot state info | Every check cycle (1s) |
| `bot_closed_trades.csv` | auto_trading.py | Closed trades with P&L | When trade closes |
| `logs/realtime_predictions.jsonl` | real_time_monitor.py | ML predictions | Every prediction cycle |
| `logs/signal_history.csv` | signal_service.py | Telegram broadcasts | When signal sent |

### Data Fields Required

#### bot_trades.csv (Open Trades)
```csv
timestamp, type, entry, session, rsi, atr, sma_fast, sma_slow, vpin, spread
2026-01-11T10:30:45, BUY, 2024.50, London, 65.2, 3.45, 2023.10, 2020.50, 0.55, 0.25
```

#### bot_state.json
```json
{
    "bot_active": true,
    "daily_trades": 5,
    "total_trades": 150,
    "daily_pnl": 125.50,
    "last_trade_time": "2026-01-11T10:30:45"
}
```

#### bot_closed_trades.csv (Closed Trades with P&L)
```csv
timestamp, close_time, type, entry_price, exit_price, pnl, duration_seconds
2026-01-11T10:00:00, 2026-01-11T10:15:30, BUY, 2024.50, 2025.00, 50.00, 930
```

#### logs/realtime_predictions.jsonl
```json
{"timestamp": "2026-01-11T10:35:00", "signal": "BUY", "confidence": 0.85, "price": 2024.75, "direction": "UPTREND"}
{"timestamp": "2026-01-11T10:36:00", "signal": "SELL", "confidence": 0.72, "price": 2024.50, "direction": "DOWNTREND"}
```

#### logs/signal_history.csv
```csv
timestamp, symbol, signal_type, price, ml_score, tp_price, sl_price, status
2026-01-11T10:32:00, XAUUSD, BUY, 2024.50, 0.85, 2050.00, 2020.00, sent
```

## Usage Examples

### 1. Start Full Dashboard
```bash
python dashboard.py
```
Shows complete dashboard with all sections. Refreshes every 30 seconds.

### 2. Compact Mode (Quick Overview)
```bash
python dashboard.py --compact
```
Shows only essential sections: bot status, recent trades, session breakdown.

### 3. Custom Refresh Interval
```bash
python dashboard.py --interval 10
```
Refresh every 10 seconds instead of 30.

### 4. View Analytics Summary
```bash
python dashboard.py --analytics
```
Shows trading analytics & performance metrics.

### 5. View Performance Tracking
```bash
python dashboard.py --performance
```
Shows live performance tracking (requires MT5 connection).

## Dashboard Sections Explained

### 1. Bot Status & Performance
```
🤖 BOT STATUS & PERFORMANCE
📊 Displays:
   - Bot active/idle status
   - Daily trades & limits
   - Total P&L, Win rate
   - Best/worst trades, Profit factor
   - Average trade duration
```

### 2. Recent Open Trades
```
📋 RECENT OPEN TRADES (Last 10)
   Shows active positions with:
   - Entry time, trade type (BUY/SELL)
   - Entry price, session (London/NY/Asian)
   - RSI & ATR indicators
```

### 3. Recently Closed Trades
```
✅ RECENTLY CLOSED TRADES (Last 5)
   Shows closed positions with:
   - Close time, entry/exit price
   - Realized P&L
   - Trade duration
```

### 4. Session Breakdown
```
⏰ SESSION & DIRECTION BREAKDOWN
   Statistics by:
   - Trading session (London, NY, Asian)
   - Trade direction (BUY, SELL)
   - Trade counts & percentages
```

### 5. Indicator Statistics
```
📈 INDICATOR STATISTICS
   Average/Min/Max of:
   - RSI (Relative Strength Index)
   - ATR (Average True Range)
   - SMA Fast/Slow
   - VPIN (Volume-Synchronized Probability)
   - Spread
```

### 6. ML Model Signals
```
🧠 ML MODEL SIGNALS
   Recent ML predictions:
   - Signal (BUY/SELL/HOLD)
   - Confidence level (0-100%)
   - Current price
   - Detected trend direction
```

### 7. Telegram Broadcasts
```
📢 TELEGRAM SIGNAL BROADCASTS
   Signals sent via Telegram:
   - Entry price & level
   - Take Profit & Stop Loss
   - Broadcast status (sent/failed)
```

## Integration with Other Modules

### With auto_trading.py
**Dashboard reads:**
- `bot_trades.csv` - for open position display
- `bot_state.json` - for bot status
- `bot_closed_trades.csv` - for closed trade stats

**How it updates:** Real-time as auto_trading.py writes files

### With real_time_monitor.py
**Dashboard reads:**
- `logs/realtime_predictions.jsonl` - for ML signals section

**How it updates:** Every prediction cycle (configurable)

### With signal_service.py
**Dashboard reads:**
- `logs/signal_history.csv` - for broadcast history

**How it updates:** When signals are broadcast to Telegram

### With analytics.py
**Dashboard calls:**
- `TradingAnalytics.get_summary_stats()` with `--analytics` flag
- `TradingAnalytics.calculate_pnl()`

**How it updates:** On demand with analytics flag

### With live_analytics.py
**Dashboard calls:**
- `LivePerformanceTracker.get_session_stats()` with `--performance` flag

**How it updates:** On demand with performance flag

## Performance Metrics Calculated

| Metric | Formula | Source |
|--------|---------|--------|
| Win Rate | (wins / total_closed) × 100 | bot_closed_trades.csv |
| Profit Factor | gross_profit / gross_loss | bot_closed_trades.csv |
| Best Trade | MAX(P&L) | bot_closed_trades.csv |
| Worst Trade | MIN(P&L) | bot_closed_trades.csv |
| Avg Win | AVG(P&L where P&L > 0) | bot_closed_trades.csv |
| Avg Loss | AVG(P&L where P&L < 0) | bot_closed_trades.csv |
| Total P&L | SUM(P&L) | bot_closed_trades.csv |

## Error Handling

Dashboard gracefully handles:
- Missing data files (shows "No data available")
- Corrupted CSV/JSON (skips bad records, logs error)
- Incomplete fields (fills with defaults)
- Timestamp parsing errors (shows raw timestamp)
- Import errors for optional modules (continues without them)

## System Requirements

```
Python 3.8+
pandas
numpy (implicit via pandas)
```

## Performance Notes

- Dashboard loop: Non-blocking, 30s default refresh
- File I/O: ~50-200ms per refresh (depends on file size)
- Memory: ~50-100MB typical (varies with trade history size)
- CPU: Minimal (<1% idle, <5% during refresh)

## Troubleshooting

### Dashboard shows "No data available"
- Check if bot is running: `python auto_trading.py`
- Verify bot_trades.csv exists
- Check bot_state.json has content

### ML signals not showing
- Check real_time_monitor.py is running
- Verify logs/realtime_predictions.jsonl exists
- Check prediction log has recent entries

### Telegram broadcasts not showing
- Check signal_service.py is running
- Verify logs/signal_history.csv exists
- Check CSV has recent rows

### Performance is slow
- Use `--compact` mode for faster rendering
- Increase `--interval` to 60+ seconds
- Clear old log files (truncate JSONL if >100MB)

## Future Enhancements

- [ ] WebSocket real-time updates (no file polling)
- [ ] Alert system (sound/notification on events)
- [ ] Multi-timeframe analysis display
- [ ] Risk heatmap visualization
- [ ] Trade execution history with detailed logs
- [ ] Web-based dashboard (HTML/CSS)
- [ ] Database backend instead of CSV files
- [ ] Custom metrics & KPI tracking

## Quick Reference - Command Summary

```bash
# Full dashboard (default)
python dashboard.py

# Compact mode
python dashboard.py --compact

# 10-second refresh
python dashboard.py --interval 10

# Analytics view
python dashboard.py --analytics

# Performance tracker
python dashboard.py --performance

# Combined (compact + 15s interval)
python dashboard.py --compact --interval 15
```
