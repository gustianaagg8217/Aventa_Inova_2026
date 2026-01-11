# 🚀 AUTO TRADING QUICK REFERENCE

## ONE-TIME SETUP (5 minutes)

### Step 1: Setup Credentials
```powershell
python setup_trading.py
# Follow prompts to enter MT5 account details
```

### Step 2: Train Models (if not done)
```powershell
python train_models.py
# Wait 5-10 minutes for models to train
```

---

## EVERY DAY - START TRADING

```powershell
python start_trading.py
```

Then select:
- **[1]** - Start Auto Trading Bot ← Main trading loop
- **[2]** - Monitor Dashboard ← Real-time stats (optional)
- **[3]** - Check Signals ← View predictions (optional)
- **[4]** - Train Models ← Update ML (optional)

---

## AUTO TRADING BOT - What It Does

| Feature | Status | Details |
|---------|--------|---------|
| **ML Predictions** | ✅ Enabled | Uses trained models if available |
| **Technical Analysis** | ✅ Enabled | SMA (5/50) + RSI (20) + ATR |
| **Hybrid Signals** | ✅ Enabled | TA + ML combined confirmation |
| **Position Management** | ✅ Auto | SL & TP set by ATR |
| **Risk Management** | ✅ Enabled | Max daily trades, max loss |
| **Telegram Alerts** | ✅ Enabled | Entry/exit/warning notifications |
| **Trade Logging** | ✅ Auto | Saved to bot_trades.csv |
| **Session Filtering** | ✅ Enabled | London/NY hours trading |

---

## FILE LOCATIONS

```
Trading Bot:        auto_trading.py
Launcher:           start_trading.py
Setup:              setup_trading.py
Dashboard:          dashboard.py
Real-Time Monitor:  real_time_monitor.py
Model Training:     train_models.py

Configuration:      config/config.yaml
                    config/trading_config.yaml

Trained Models:     models/

Trade Logs:         bot_trades.csv
                    bot_state.json

Logs:               logs/realtime_predictions.jsonl
                    logs/signal_history.csv
```

---

## SIGNAL LOGIC (Simple Explanation)

```
EVERY SECOND:
  ├─ Get latest price data
  ├─ Calculate SMA (fast & slow)
  ├─ Calculate RSI
  ├─ Calculate ATR
  ├─ Check ML model (if available)
  │
  ├─ IF SMA Fast > SMA Slow AND RSI < 70:
  │    AND (ML predicts bullish OR no ML):
  │     └─ OPEN BUY TRADE
  │
  ├─ ELIF SMA Fast < SMA Slow AND RSI > 30:
  │    AND (ML predicts bearish OR no ML):
  │     └─ OPEN SELL TRADE
  │
  └─ ELSE: WAIT for next signal

EVERY POSITION:
  ├─ Monitor price vs Stop Loss (ATR × 2.5)
  └─ Monitor price vs Take Profit (ATR × 4.0)
  
EVERY COMPLETED TRADE:
  └─ Send Telegram notification
```

---

## COMMON CONFIGURATIONS

### Conservative (Default)
```yaml
lot_size: 0.01
max_positions: 1
max_daily_trades: 15
atr_sl_mult: 2.5
atr_tp_mult: 4.0
```

### Moderate Risk
```yaml
lot_size: 0.05
max_positions: 2
max_daily_trades: 20
atr_sl_mult: 2.0
atr_tp_mult: 3.0
```

### Aggressive
```yaml
lot_size: 0.1
max_positions: 3
max_daily_trades: 30
atr_sl_mult: 1.5
atr_tp_mult: 2.5
```

Change in `config/trading_config.yaml`

---

## TROUBLESHOOTING QUICK FIX

| Problem | Fix |
|---------|-----|
| "No module named 'inference'" | Bot uses TA-only mode - this is OK |
| "MT5 not connected" | Check credentials and MT5 is running |
| "No trained models" | Run: `python train_models.py` |
| "Trading halted" | Check daily loss limit or position limit |
| "Too wide spread" | Wait for better market conditions |
| No trades executing | Check paper/live mode, margin available |
| Telegram not working | Check bot token and chat IDs in config |

---

## MONITORING

### View Recent Trades
```powershell
python -c "import pandas as pd; df = pd.read_csv('bot_trades.csv'); print(df.tail(20))"
```

### Show Statistics
```powershell
python analytics.py
```

### Check Bot State
```powershell
python -c "import json; print(json.load(open('bot_state.json')))"
```

---

## IMPORTANT NOTES

✅ **Fully Automated** - No manual interaction needed once started
✅ **ML + TA Combined** - Uses both for better accuracy  
✅ **Risk Management** - Built-in position & loss limits
✅ **Real-Time Alerts** - Telegram notifications for all events
✅ **Trade Logging** - All trades recorded to CSV

⚠️ **Paper Trading Recommended** - Test on demo first
⚠️ **Check Credentials** - MT5 account must be valid
⚠️ **Monitor Daily** - Check margin and P&L
⚠️ **Live Trading Enabled** - Make sure this is intentional

---

## SUPPORT

**Documentation:** `AUTO_TRADING_SETUP.md`
**Logs:** `logs/` folder
**Config:** `config/` folder  
**Trade History:** `bot_trades.csv`

**Ready? Start with:**
```powershell
python start_trading.py
```
