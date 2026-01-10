# 🎨 GUI Launcher - Complete Integration Guide

## System Overview

Your Aventa Trading System now has **TWO ways to operate**:

```
┌─────────────────────────────────────────────────────┐
│        Aventa Trading System v1.0                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌───────────────────┐    ┌────────────────────┐   │
│  │                   │    │                    │   │
│  │   GUI Launcher    │    │   Command Line     │   │
│  │   (Professional)  │    │   (Advanced)       │   │
│  │                   │    │                    │   │
│  └─────────┬─────────┘    └────────┬───────────┘   │
│            │                       │               │
│  • Easy to use              • Faster               │
│  • Visual feedback          • Scriptable           │
│  • Configuration mgmt       • Automation           │
│  • Real-time monitoring     • Advanced tuning      │
│  • Risk management          • Batch processing     │
│  • Activity logging         • Custom workflows     │
│            │                       │               │
│            └───────────┬───────────┘               │
│                        │                          │
│              ┌──────────▼──────────┐              │
│              │   Core Modules      │              │
│              ├─────────────────────┤              │
│              │ • train_models.py   │              │
│              │ • inference.py      │              │
│              │ • real_time_monitor │              │
│              │ • mt5_integration   │              │
│              │ • streamlit_board   │              │
│              └─────────────────────┘              │
│                                                   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Step 1: Install Dependencies (1 minute)

**Windows:**
```bash
run_gui.bat
```

**Linux/Mac:**
```bash
chmod +x run_gui.sh
./run_gui.sh
```

This automatically:
1. Installs PyQt6
2. Installs required packages
3. Launches the GUI

### Step 2: First Configuration (2 minutes)

GUI Window Opens → 8 Tabs Visible

```
┌─ Tab 1: ⚙️ Configuration
├─ Tab 2: 📈 Indicators
├─ Tab 3: 🎓 Training
├─ Tab 4: 📊 Backtest
├─ Tab 5: 🔴 Real-time
├─ Tab 6: 💹 Performance
├─ Tab 7: ⚠️ Risk Management
└─ Tab 8: 📋 Logs
```

1. Click **⚙️ Configuration Tab**
2. Fill in MT5 credentials
3. Set trading parameters
4. File → Save Configuration

### Step 3: Train Model (5 minutes)

1. Click **🎓 Training Tab**
2. Click **▶ Start Training**
3. Watch progress bar
4. View results

### Step 4: Test Strategy (3 minutes)

1. Click **📊 Backtest Tab**
2. Click **▶ Run Backtest**
3. Review metrics
4. Export results if needed

### Step 5: Monitor Live (Continuous)

1. Click **🔴 Real-time Tab**
2. Select data source (CSV/MT5/yFinance)
3. Click **▶ Start Monitoring**
4. Watch predictions update in real-time

---

## 🔄 Common Workflows

### Workflow 1: "I want to train a model"

**Using GUI:**
```
1. ⚙️ Tab: Set indicators
2. 🎓 Tab: Click "Start Training"
3. Wait for completion
4. View results
5. File → Save Config
```

**Using CLI:**
```bash
python train_models.py
```

---

### Workflow 2: "I want to test my strategy"

**Using GUI:**
```
1. ⚙️ Tab: Configure strategy
2. 🎓 Tab: Train model (or use existing)
3. 📊 Tab: Click "Run Backtest"
4. Analyze results
5. Export if needed
```

**Using CLI:**
```bash
python inference.py --data-file data/XAUUSD_M1_59days.csv
```

---

### Workflow 3: "I want to monitor live"

**Using GUI:**
```
1. 🔴 Tab: Select data source
2. 🔴 Tab: Click "Start Monitoring"
3. View real-time predictions
4. 📋 Tab: Check logs
5. 💹 Tab: Monitor performance
```

**Using CLI:**
```bash
python real_time_monitor.py --source csv --interval 60
streamlit run streamlit_dashboard.py
```

---

## 📊 Configuration Examples

### Example 1: Gold Trading (XAUUSD)

**File**: `config_gold.json`

```json
{
  "symbol": "XAUUSD",
  "lot_size": 0.1,
  "stop_loss_pips": 100,
  "take_profit_pips": 200,
  "sma_period": 20,
  "rsi_period": 14,
  "atr_period": 14,
  "buy_threshold": 0.0001,
  "sell_threshold": -0.0001
}
```

**How to use:**
1. Click "File → Save Configuration As..."
2. Save as `config_gold.json`
3. Later: "File → Open Configuration..." and select it

---

### Example 2: Conservative Risk Profile

**File**: `config_conservative.json`

```json
{
  "lot_size": 0.01,
  "stop_loss_pips": 150,
  "take_profit_pips": 300,
  "max_daily_loss": 500,
  "max_positions": 1,
  "buy_threshold": 0.0005,
  "sell_threshold": -0.0005
}
```

---

### Example 3: Aggressive Trading

**File**: `config_aggressive.json`

```json
{
  "lot_size": 0.5,
  "stop_loss_pips": 50,
  "take_profit_pips": 100,
  "max_daily_loss": 2000,
  "max_positions": 5,
  "buy_threshold": 0.00001,
  "sell_threshold": -0.00001
}
```

---

## 🔐 Data Files & Locations

### Directory Structure

```
Aventa_Inova_2026/
├── gui_launcher.py          ← Main GUI application
├── setup_gui.py             ← Dependency installer
├── run_gui.bat              ← Windows launcher
├── run_gui.sh               ← Linux/Mac launcher
│
├── config.json              ← Current configuration
├── config_*.json            ← Saved configurations
│
├── models/
│   ├── rf_baseline.pkl      ← Trained RandomForest
│   └── lstm_model.pt        ← Trained LSTM
│
├── data/
│   └── XAUUSD_M1_59days.csv ← Historical data
│
├── logs/
│   └── realtime_predictions.jsonl ← Live predictions
│
└── docs/
    ├── GUI_USER_GUIDE.md
    ├── GUI_QUICK_START.md
    ├── GUI_IMPLEMENTATION_SUMMARY.md
    └── README.md
```

---

## 📈 Tab-by-Tab Guide

### ⚙️ Configuration Tab
**Purpose**: Set all parameters
**Key Actions**:
- Fill in MT5 credentials
- Set trading parameters
- Adjust signal thresholds
- Save/load profiles

**Example**:
```
MT5 Path: C:\Program Files\MetaTrader 5
Login: 123456
Symbol: XAUUSD
Lot Size: 0.1
Stop Loss: 100 pips
Take Profit: 200 pips
```

---

### 📈 Indicators Tab
**Purpose**: Tune technical indicators
**Key Actions**:
- Adjust SMA period (e.g., 15-30)
- Adjust RSI period (e.g., 10-20)
- Adjust overbought/oversold levels
- Fine-tune ATR period

**Testing Strategy**:
1. Change indicator values
2. Train model
3. Backtest
4. Compare results
5. Keep best settings

---

### 🎓 Training Tab
**Purpose**: Train ML models
**Process**:
```
1. Click "Start Training"
   ↓
2. Loads historical data
   ↓
3. Extracts features
   ↓
4. Trains RandomForest
   ↓
5. Trains LSTM (optional)
   ↓
6. Saves models
   ↓
7. Shows results
```

**Results Include**:
- Training accuracy metrics
- Model parameters
- Feature importance
- Elapsed time
- File locations

---

### 📊 Backtest Tab
**Purpose**: Test on historical data
**Metrics Provided**:
- Total trades executed
- Winning/losing trades count
- Win rate percentage
- Total profit/loss
- Average win/loss sizes
- Signal distribution

**Export Options**:
- CSV for Excel
- JSON for programming
- Both formats available

---

### 🔴 Real-time Tab
**Purpose**: Live prediction monitoring
**Data Sources**:
1. **CSV**: Historical rolling window (testing)
2. **MT5**: Live market data (requires terminal)
3. **yFinance**: Yahoo Finance (limited real-time)

**Live Metrics**:
- Current iteration number
- Latest closing price
- Latest prediction value
- Current signal (BUY/SELL/HOLD)
- Cumulative signal counts

**History Display**:
- Last 50 predictions
- Timestamp for each
- Price at prediction time
- Actual signal generated

---

### 💹 Performance Tab
**Purpose**: Track trading performance
**Metrics Displayed**:
- Total number of trades
- Winning trade count
- Losing trade count
- Win rate percentage
- Total profit/loss ($)
- Average win size ($)
- Average loss size ($)
- Profit factor ratio
- Maximum drawdown %

**Trade History**:
- Entry timestamp
- Entry price
- Exit price
- P&L in dollars
- Return percentage
- Bars held

---

### ⚠️ Risk Management Tab
**Purpose**: Position sizing & risk limits

**Position Calculator**:
```
Account Size: $10,000
Risk Per Trade: 2%
Stop Loss: 100 pips

→ Recommended Lot: 0.05 lots
```

**Daily Limits**:
- Loss limit stops trading if exceeded
- Profit target tracks daily goal
- Position limit prevents overexposure

**Risk Metrics**:
- Current $ exposure
- Current risk percentage
- Available margin

---

### 📋 Logs Tab
**Purpose**: Monitor system activity

**Log Levels**:
```
DEBUG    - Detailed diagnostic info
INFO     - General information (default)
WARNING  - Warning messages
ERROR    - Error messages
CRITICAL - Critical failures
```

**Actions**:
- Filter by log level
- Clear old logs
- Export to file (.txt or .log)
- Real-time updates

**Example Log Entry**:
```
2026-01-11 14:35:22 - gui - INFO - Training started
2026-01-11 14:35:45 - train - INFO - Epoch 1/30 complete
2026-01-11 14:35:67 - train - INFO - Epoch 2/30 complete
2026-01-11 14:36:12 - gui - INFO - Training completed!
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save Configuration |
| Ctrl+O | Open Configuration |
| Ctrl+N | New Configuration |
| Ctrl+Q | Quit Application |

---

## 💾 Configuration Management

### Save Configuration

```
File Menu → Save Configuration
        ↓
Updates config from all tabs
        ↓
Saves to config.json
        ↓
Success message
```

### Load Configuration

```
File Menu → Open Configuration...
        ↓
File dialog opens
        ↓
Select .json file
        ↓
All tabs update
        ↓
Ready to use
```

### Reset to Defaults

```
Tools Menu → Reset to Defaults
        ↓
Confirmation dialog
        ↓
Config reset
        ↓
All tabs update
```

---

## 🔧 Troubleshooting

### "GUI won't start"
```bash
# Solution: Install dependencies
python setup_gui.py
python gui_launcher.py
```

### "Training fails"
```
Logs Tab → Check error messages
          ↓
Common causes:
• Data file missing
• Invalid path
• Memory issues
```

### "Real-time monitor stops"
```
Logs Tab → Check logs
          ↓
Check data source:
• CSV: File exists?
• MT5: Terminal running?
• yFinance: Internet connected?
```

### "Backtest shows no trades"
```
⚙️ Configuration Tab
    ↓
Adjust thresholds:
    ├─ Buy: increase sensitivity
    └─ Sell: increase sensitivity
    ↓
📊 Backtest Tab → Run again
```

---

## 📞 Support Resources

### Documentation
- **GUI_USER_GUIDE.md** - Detailed (350+ lines)
- **GUI_QUICK_START.md** - Quick reference (200+ lines)
- **GUI_IMPLEMENTATION_SUMMARY.md** - Technical (400+ lines)

### Files
- **README.md** - Project overview
- **QUICK_START.md** - Trading setup
- **DASHBOARD_GUIDE.md** - Dashboard details

### In-Application
- **Logs Tab** - Real-time debugging
- **Tools Menu** - Validation & reset
- **Help Menu** - About & docs

---

## ✅ Checklist: Getting Started

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] Ran `run_gui.bat` or `./run_gui.sh`
- [ ] GUI window opened
- [ ] Filled in ⚙️ Configuration tab
- [ ] Saved configuration
- [ ] Ran training once
- [ ] Ran backtest once
- [ ] Started monitoring once
- [ ] Checked logs
- [ ] Read GUI_USER_GUIDE.md

---

## 🎯 Next Steps

### Day 1
1. ✅ Install and launch GUI
2. ✅ Configure MT5 settings
3. ✅ Save configuration
4. ✅ Run training

### Day 2
1. ✅ Run backtesting
2. ✅ Analyze results
3. ✅ Adjust indicators
4. ✅ Retrain model

### Day 3
1. ✅ Test with CSV data
2. ✅ Start real-time monitoring
3. ✅ Watch predictions
4. ✅ Check performance tab

### Week 1
1. ✅ Connect MT5 (paper trading)
2. ✅ Run live monitoring
3. ✅ Test auto-trading
4. ✅ Optimize parameters

---

## 🎉 You're Ready!

Your Aventa Trading System GUI Launcher is now:

✅ **Fully installed**
✅ **Professionally designed**
✅ **Completely documented**
✅ **Production ready**
✅ **Easy to use**

### Launch Now:

**Windows:**
```bash
run_gui.bat
```

**Linux/Mac:**
```bash
./run_gui.sh
```

Happy trading! 🚀📈💰

---

**Questions?** Check the documentation files or review the Logs tab in the GUI!
