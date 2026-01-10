# 🚀 Aventa GUI Launcher - Complete User Guide

**Version:** 1.0  
**Status:** ✅ Production Ready  
**Platform:** Windows, Linux, macOS  

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Tab Descriptions](#tab-descriptions)
4. [Configuration Management](#configuration-management)
5. [Features & Workflows](#features--workflows)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- Windows, Linux, or macOS
- 2GB RAM minimum

### Step 1: Install Dependencies

**Windows:**
```bash
python setup_gui.py
```

**Linux/Mac:**
```bash
python3 setup_gui.py
```

Or install manually:
```bash
pip install PyQt6 numpy pandas scikit-learn torch PyMetaTrader5 yfinance
```

### Step 2: Launch GUI

**Windows:**
```bash
run_gui.bat
```

**Linux/Mac:**
```bash
chmod +x run_gui.sh
./run_gui.sh
```

**Direct Python:**
```bash
python gui_launcher.py
```

---

## 🎯 Quick Start

### First Time Setup

1. **Launch the application**
   - GUI window opens with 8 tabs
   - Default configuration loaded

2. **Configure MT5 Connection** (⚙️ Configuration Tab)
   - Enter MT5 installation path
   - Enter login credentials
   - Enter server name

3. **Set Trading Parameters**
   - Symbol: XAUUSD (gold)
   - Lot Size: 0.1 lots
   - Stop Loss: 100 pips
   - Take Profit: 200 pips

4. **Configure Indicators** (📈 Indicators Tab)
   - SMA Period: 20
   - RSI Period: 14
   - RSI Overbought: 70
   - RSI Oversold: 30
   - ATR Period: 14

5. **Save Configuration** (File → Save Configuration)
   - Saves as `config.json`
   - Load anytime with File → Open Configuration

---

## 📑 Tab Descriptions

### 1️⃣ **⚙️ Configuration Tab**

**Purpose:** Manage all trading parameters and system settings.

**Settings:**

#### MT5 Settings
- **MT5 Path:** Installation directory (e.g., `C:\Program Files\MetaTrader 5`)
- **Login:** Trading account number
- **Password:** Account password
- **Server:** Broker server name

#### Trading Settings
- **Symbol:** Trading instrument (e.g., XAUUSD, EURUSD)
- **Lot Size:** Position size (0.01 to 100)
- **Stop Loss:** Pips from entry (1-1000)
- **Take Profit:** Pips from entry (1-1000)
- **Max Daily Loss:** Maximum loss before stopping ($)
- **Max Positions:** Maximum concurrent trades

#### Signal Thresholds
- **Buy Threshold:** Prediction value to trigger BUY (e.g., 0.0001)
- **Sell Threshold:** Prediction value to trigger SELL (e.g., -0.0001)

**Actions:**
- All fields update in real-time
- Save via File → Save Configuration
- Validate via Tools → Validate Configuration

---

### 2️⃣ **📈 Indicators Tab**

**Purpose:** Configure technical indicator parameters.

**Indicators:**

#### Moving Averages (SMA)
- **Period:** Number of bars (2-500)
- Default: 20

#### RSI (Relative Strength Index)
- **Period:** Lookback period (2-100)
- **Overbought Level:** Upper threshold (0-100)
- **Oversold Level:** Lower threshold (0-100)
- Defaults: Period=14, Overbought=70, Oversold=30

#### ATR (Average True Range)
- **Period:** Volatility period (2-100)
- Default: 14

**Usage:**
- Modify values to optimize indicator sensitivity
- Restart training/monitoring after changes
- Save configuration to preserve changes

---

### 3️⃣ **🎓 Training Tab**

**Purpose:** Train machine learning models on historical data.

**Features:**

#### Training Settings
- **Test Size:** Fraction of data for testing (0.01-0.5)
  - Default: 0.1 (10%)
- **Validation Size:** Fraction for validation (0.01-0.5)
  - Default: 0.1 (10%)
- **Epochs:** Training iterations for LSTM (1-500)
  - Default: 30
- **Batch Size:** Samples per training batch (1-256)
  - Default: 32
- **Model Type:** Select RandomForest, LSTM, or Both

#### Training Controls
- **▶ Start Training:** Begin model training
- **⏹ Stop Training:** Halt training process

#### Progress & Status
- **Progress Bar:** Visual training progress (0-100%)
- **Status:** Current operation (e.g., "Training models...", "Completed!")
- **Results:** Training output and metrics

**Workflow:**
1. Adjust training parameters
2. Click "Start Training"
3. Monitor progress bar
4. View results in Results section
5. Trained models saved to `models/` directory

**Output Files:**
- `models/rf_baseline.pkl` - RandomForest model
- `models/rf_baseline_scaler.pkl` - Feature scaler
- `models/lstm_model.pt` - LSTM model
- `models/lstm_model_history.json` - Training history

---

### 4️⃣ **📊 Backtest Tab**

**Purpose:** Test strategies on historical data without live trading.

**Features:**

#### Backtest Controls
- **▶ Run Backtest:** Execute backtest on historical data
- **💾 Export Results:** Save results to CSV or JSON

#### Metrics
- **Total Trades:** Number of completed trades
- **Winning Trades:** Profitable trades count
- **Losing Trades:** Loss-making trades count
- **Win Rate:** % of winning trades
- **Total P&L:** Total profit/loss ($)
- **Average Win:** Average winning trade size
- **Buy Signals:** Count of BUY signals
- **Sell Signals:** Count of SELL signals
- **Hold Signals:** Count of HOLD signals

**Workflow:**
1. Load training data (automatic)
2. Click "Run Backtest"
3. Monitor progress
4. View results table
5. Optionally export to CSV/JSON

**Export Options:**
- **CSV:** Spreadsheet format
- **JSON:** Structured data format

---

### 5️⃣ **🔴 Real-time Tab**

**Purpose:** Monitor live market predictions in real-time.

**Features:**

#### Monitoring Settings
- **Data Source:** Select csv, mt5, or yfinance
- **Update Interval:** Seconds between predictions (0.1-3600)

#### Live Metrics
- **Iteration:** Current update number
- **Latest Price:** Most recent closing price ($)
- **Prediction:** Last predicted value
- **Signal:** BUY/SELL/HOLD
- **Buy Signals:** Cumulative count
- **Sell Signals:** Cumulative count
- **Hold Signals:** Cumulative count

#### Prediction History
- **Table:** Last 50 predictions with timestamp, price, prediction, signal

#### Controls
- **▶ Start Monitoring:** Begin real-time predictions
- **⏹ Stop Monitoring:** Stop real-time stream

**Data Sources:**

##### CSV Mode
- Uses historical data with rolling window
- Good for testing and backtesting
- No live data needed

##### MT5 Mode (Live Trading)
- Requires MetaTrader 5 terminal running
- Real-time XAUUSD price data
- Direct market connectivity

##### yFinance Mode
- Yahoo Finance data (limited real-time)
- Demo/testing purposes
- Global symbols available

**Workflow:**
1. Select data source
2. Set update interval
3. Click "Start Monitoring"
4. Watch real-time metrics update
5. Review prediction history table
6. Click "Stop" to halt monitoring

---

### 6️⃣ **💹 Performance Tab**

**Purpose:** Track trading performance metrics.

**Metrics:**

#### Key Performance Indicators
- **Total Trades:** All executed trades
- **Winning Trades:** Profitable count
- **Losing Trades:** Loss count
- **Win Rate:** Success percentage
- **Total P&L:** Cumulative profit/loss ($)
- **Average Win:** Mean winning trade size
- **Average Loss:** Mean losing trade size
- **Profit Factor:** Win amount / Loss amount
- **Max Drawdown:** Largest peak-to-trough decline

#### Trade History
- Detailed table of all completed trades
- Entry/exit prices and times
- P&L and return percentage
- Bars held for each trade

**Features:**
- **🔄 Refresh Metrics:** Update from latest data
- Historical data display
- Performance charts (when connected to monitoring)

---

### 7️⃣ **⚠️ Risk Management Tab**

**Purpose:** Manage position sizing and risk limits.

**Components:**

#### Position Sizing
- **Account Size:** Total trading capital ($)
- **Risk Per Trade:** % of account to risk (0.1-100%)
- **Stop Loss (pips):** Risk distance in pips
- **📊 Calculate Position Size:** Auto-calculate lot size

**Formula:**
```
Lot Size = (Account * Risk%) / (Stop Loss * Pip Value)
```

#### Daily Limits
- **Daily Loss Limit:** Max loss before stopping ($)
- **Daily Profit Target:** Goal for day ($)
- **Max Concurrent Positions:** Maximum open trades

#### Risk Metrics
- **Current Exposure:** Total $ in open positions
- **Current Risk %:** Exposure as % of account
- **Available Margin:** Remaining margin ($)

**Workflow:**
1. Enter account size
2. Set risk percentage (2-5% recommended)
3. Click "Calculate Position Size"
4. Set daily loss limit
5. Monitor current exposure during trading

**Best Practices:**
- Risk 1-2% per trade
- Risk 5% max per day
- Maximum 3-5 concurrent positions
- Daily profit target = 1-2% of account

---

### 8️⃣ **📋 Logs Tab**

**Purpose:** Monitor system activity and debug issues.

**Features:**

#### Log Controls
- **Log Level:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **🗑️ Clear Logs:** Delete all logged messages
- **💾 Export Logs:** Save logs to .txt or .log file

#### Activity Log
- Real-time log display
- 10,000 line buffer (auto-scrolling)
- Timestamp for each event
- Color-coded severity

#### Log Levels
- **DEBUG:** Detailed diagnostic info
- **INFO:** General information (default)
- **WARNING:** Warning messages
- **ERROR:** Error messages
- **CRITICAL:** Critical failures

**Workflow:**
1. Monitor logs during operations
2. Filter by log level if needed
3. Clear logs between sessions
4. Export for debugging/archiving

**Export Options:**
- **TXT:** Plain text format
- **LOG:** Standard log file format

---

## 💾 Configuration Management

### Save Configuration

**Method 1: Quick Save**
```
File → Save Configuration
```
Saves to `config.json` in project directory.

**Method 2: Save As**
```
File → Save Configuration As...
```
Choose custom filename and location.

### Load Configuration

**Method 1: Open File**
```
File → Open Configuration...
```
Select any saved `.json` config file.

**Method 2: Recent Files**
Last used config automatically loads on startup.

### Configuration File Format

```json
{
  "mt5_path": "C:\\Program Files\\MetaTrader 5",
  "mt5_login": 123456,
  "mt5_password": "password",
  "mt5_server": "broker.server",
  "symbol": "XAUUSD",
  "lot_size": 0.1,
  "stop_loss_pips": 100,
  "take_profit_pips": 200,
  "max_daily_loss": 1000.0,
  "max_positions": 3,
  "sma_period": 20,
  "rsi_period": 14,
  "atr_period": 14,
  "rsi_overbought": 70,
  "rsi_oversold": 30,
  "buy_threshold": 0.0001,
  "sell_threshold": -0.0001,
  "model_type": "RandomForest",
  "model_dir": "models",
  "test_size": 0.1,
  "validation_size": 0.1,
  "epochs": 30,
  "batch_size": 32,
  "monitoring_interval": 1.0,
  "data_source": "csv"
}
```

### Validate Configuration

```
Tools → Validate Configuration
```

Checks:
- ✓ Symbol not empty
- ✓ Lot size > 0
- ✓ Stop loss > 0
- ✓ All paths exist

---

## 🔄 Features & Workflows

### Workflow 1: Train & Backtest

**Time:** ~5-10 minutes

```
1. Configuration Tab
   └─ Set trading parameters

2. Indicators Tab
   └─ Adjust indicator settings

3. Training Tab
   ├─ Set epochs: 30-100
   ├─ Set batch size: 16-64
   ├─ Click "Start Training"
   └─ Wait for completion

4. Backtest Tab
   ├─ Click "Run Backtest"
   ├─ Analyze results
   └─ Export results
```

### Workflow 2: Live Monitoring

**Time:** Continuous

```
1. Real-time Tab
   ├─ Select data source: csv/mt5/yfinance
   ├─ Set interval: 1-60 seconds
   ├─ Click "Start Monitoring"
   └─ Watch predictions in real-time

2. Logs Tab
   └─ Monitor system activity

3. Performance Tab (Optional)
   └─ Check live P&L
```

### Workflow 3: Risk Management Setup

**Time:** ~5 minutes

```
1. Risk Management Tab
   ├─ Enter account size
   ├─ Set risk per trade: 2%
   ├─ Click "Calculate Position Size"
   └─ Recommended lot size displays

2. Configuration Tab
   ├─ Update lot size
   └─ Set daily loss limit

3. Save Configuration
```

### Workflow 4: Optimize Indicators

**Time:** ~15 minutes per cycle

```
1. Indicators Tab
   └─ Adjust parameters
      ├─ SMA: 15-30
      ├─ RSI: 10-20
      ├─ ATR: 10-20

2. Training Tab
   └─ Retrain model

3. Backtest Tab
   └─ Compare results

4. Repeat until satisfied
```

---

## 🆘 Troubleshooting

### GUI Won't Start

**Error:** `ModuleNotFoundError: No module named 'PyQt6'`

**Solution:**
```bash
pip install PyQt6
python gui_launcher.py
```

---

### Training Fails

**Error:** `FileNotFoundError: data/XAUUSD_M1_59days.csv`

**Solution:**
1. Ensure data file exists in `data/` folder
2. Check data path in Configuration Tab
3. Data file must have columns: time, open, high, low, close

---

### Real-time Monitor Stops

**Error:** Connection lost

**Solution:**
- **CSV mode:** Verify data file path
- **MT5 mode:** Start MetaTrader 5 terminal
- **yfinance mode:** Check internet connection

---

### Backtest Shows No Trades

**Cause:** Thresholds too tight

**Solution:**
1. Go to Configuration Tab
2. Increase threshold values:
   - Buy: 0.0001 → 0.00005
   - Sell: -0.0001 → -0.00005
3. Rerun backtest

---

### Performance Metrics Empty

**Cause:** No monitoring data collected

**Solution:**
1. Run Real-time Tab for several minutes
2. Refresh Performance Tab
3. Or import backtest results

---

### Configuration Won't Save

**Error:** Permission denied

**Solution:**
1. Run as Administrator
2. Check folder write permissions
3. Save to different location

---

## 📞 Support Resources

- **Documentation:** QUICK_START.md, DASHBOARD_GUIDE.md
- **Config Files:** config.json
- **Logs:** Check Logs Tab for errors
- **GitHub:** See README.md

---

## 🎓 Best Practices

### Trading
1. ✓ Always test on historical data first
2. ✓ Risk 1-2% per trade max
3. ✓ Set daily loss limits
4. ✓ Monitor live predictions
5. ✓ Keep position count low

### Configuration
1. ✓ Save configs frequently
2. ✓ Use meaningful config names
3. ✓ Document custom settings
4. ✓ Backup configs regularly

### Monitoring
1. ✓ Start with CSV data source
2. ✓ Test MT5 with paper trading first
3. ✓ Monitor logs regularly
4. ✓ Track performance metrics

---

**Last Updated:** January 11, 2026  
**Version:** 1.0.0  
✅ **Production Ready**
