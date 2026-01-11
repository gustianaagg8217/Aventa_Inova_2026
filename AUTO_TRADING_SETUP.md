# 🤖 AUTO TRADING SETUP - FULLY INTEGRATED

## Quick Start (3 Steps)

### Step 1: Set Environment Variables (First Time Only)

```powershell
# Open PowerShell in project folder
$env:MT5_ACCOUNT = "11260163"
$env:MT5_PASSWORD = "your_password_here"
$env:MT5_SERVER = "VantageInternational-Demo"
```

**OR** if you want permanent (add to Windows Environment):
1. Press `Win + X` → Environment Variables
2. Add user variables:
   - `MT5_ACCOUNT` = 11260163
   - `MT5_PASSWORD` = your_password
   - `MT5_SERVER` = VantageInternational-Demo

### Step 2: Train Models (First Time Only)

```powershell
# Terminal 1: Train ML models
python train_models.py
# Takes 5-10 minutes, saves models to /models folder
```

### Step 3: Start Trading

```powershell
# Terminal 2: Start the launcher
python start_trading.py

# Select option [1] to start auto trading bot
```

---

## What Happens Automatically

### Auto Trading Bot (`auto_trading.py`)
✅ Connects to MT5
✅ Loads trained ML models
✅ Monitors price in real-time
✅ Calculates indicators (SMA, RSI, ATR)
✅ Gets ML predictions
✅ Combines TA + ML signals
✅ Opens trades automatically
✅ Monitors positions
✅ Closes trades on TP/SL
✅ Sends Telegram notifications
✅ Logs all trades to CSV

**Features:**
- **Hybrid Signals**: Technical Analysis (SMA/RSI/ATR) + ML Model predictions
- **Risk Management**: Max daily trades, max daily loss, margin monitoring
- **Position Tracking**: Distinguishes bot trades vs manual trades vs other bots
- **Session Filtering**: Only trades during London/NY hours (configurable)
- **Telegram Alerts**: Real-time notifications for entries, exits, margin warnings

---

## Full Menu Options

```
[1] 🚀 START AUTO TRADING BOT
    → Full ML+TA hybrid system
    → All features enabled
    → Main trading loop

[2] 📊 MONITOR DASHBOARD  
    → Real-time metrics
    → Live performance tracking
    → 7 display sections
    → Run in parallel window

[3] 📡 CHECK SIGNALS (Real-Time Monitor)
    → Live ML predictions
    → Technical indicators
    → Data source options (MT5/yfinance/CSV)

[4] 🧠 TRAIN NEW MODELS
    → Re-train ML models
    → Update with latest data
    → Improves predictions

[5] 📈 RUN BACKTEST
    → Test strategy on historical data
    → Performance metrics
    → Risk analysis
```

---

## Signal Generation (How It Works)

### Technical Analysis (TA) Signals
```
LONG Signal:
  1. SMA Fast (5) crosses above SMA Slow (50)
  2. RSI < 70 (not overbought)
  
SHORT Signal:
  1. SMA Fast (5) crosses below SMA Slow (50)
  2. RSI > 30 (not oversold)
```

### ML Model Confirmation
```
If ML model available:
  - TA crossover must be confirmed by ML prediction
  - ML > 0.0001 for LONG (bullish)
  - ML < -0.0001 for SHORT (bearish)
  - Reduces false signals

If ML model NOT available:
  - Use TA signals only
  - System still fully functional
```

### Combined Logic
```
IF (TA LONG crossover) AND (ML bullish OR no ML available):
  ✅ OPEN BUY TRADE
  
IF (TA SHORT crossover) AND (ML bearish OR no ML available):
  ✅ OPEN SELL TRADE
  
ELSE:
  ❌ WAIT FOR NEXT SIGNAL
```

### Position Management
```
Stop Loss: Entry Price ± (ATR × 2.5)
Take Profit: Entry Price ± (ATR × 4.0)
Lot Size: 0.01 BTC
Max Positions: 1 (one at a time)
Max Daily Trades: 15
Max Daily Loss: $50
```

---

## Configuration Files

### `config/config.yaml` - Main Settings
```yaml
system:
  paper_trading: false  # Set to true for demo
  
trading:
  symbol: BTCUSD
  magic_number: 12345

risk:
  mode: conservative
  max_daily_loss: 0.05  # 5%
```

### `config/trading_config.yaml` - Strategy
```yaml
strategy:
  sma_fast: 5
  sma_slow: 50
  rsi_period: 20
  atr_stop_loss_multiplier: 2.5
  atr_take_profit_multiplier: 4.0
  
risk:
  lot_size: 0.01
  max_positions: 1
```

---

## Data Files

**Created automatically by bot:**
- `bot_trades.csv` - All trades (entry, exit, P&L)
- `bot_state.json` - Bot state (daily trades, PnL)
- `logs/training_run_*.json` - Model training logs
- `logs/realtime_predictions.jsonl` - ML predictions
- `logs/signal_history.csv` - Telegram broadcasts

**Check trades:**
```powershell
# View recent trades
python -c "import pandas as pd; print(pd.read_csv('bot_trades.csv').tail(20))"

# View analytics
python analytics.py
```

---

## Troubleshooting

### Error: "No module named 'inference'"
```powershell
# inference.py not found, bot will use TA-only mode
# This is OK, trading will still work
```

### Error: "MT5 not connected"
```powershell
# Check credentials
echo $env:MT5_ACCOUNT
echo $env:MT5_SERVER

# Make sure MT5 terminal is running
# Check server name: look in MT5 login dialog
```

### Error: "No trained models found"
```powershell
# Train models first
python train_models.py

# Or run in TA-only mode
# Bot will work without ML models
```

### Trades not executing
```powershell
# Check:
1. Paper trading enabled? (config/config.yaml)
2. Margin available in MT5?
3. Spread not too wide? (current: max 30 pips)
4. Position limit reached? (max 1 open)
5. Daily loss limit hit? (max $50)
```

---

## Advanced Usage

### Run bot in background (Windows)
```powershell
# Terminal 1: Start bot
python start_trading.py
# Select [1]

# Terminal 2 (separate window): Start dashboard
python start_trading.py
# Select [2]
```

### Monitor only mode
```powershell
# Just view signals, don't trade
python real_time_monitor.py --source mt5
```

### Custom strategy parameters
Edit `config/trading_config.yaml`:
```yaml
strategy:
  sma_fast: 3      # Faster = more signals
  sma_slow: 100    # Slower = filter noise
  rsi_period: 14   # Higher = less overbought/oversold
```

### Change lot size
Edit `config/trading_config.yaml`:
```yaml
risk:
  lot_size: 0.05   # Increase from 0.01 to 0.05
```

---

## Support

**Logs location:** `logs/` folder
**Config location:** `config/` folder
**Models location:** `models/` folder
**Trade history:** `bot_trades.csv`

Check logs for detailed error messages if something goes wrong.

---

**Status: ✅ READY TO TRADE**

You can now run `python start_trading.py` and select option [1] to start full-featured auto trading!
