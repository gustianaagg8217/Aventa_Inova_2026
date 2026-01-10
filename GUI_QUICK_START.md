# 🚀 GUI Launcher - Installation & Launch Guide

## Quick Installation (1 minute)

### Windows
```batch
# Method 1: Automatic (Recommended)
run_gui.bat

# Method 2: Manual
python setup_gui.py
python gui_launcher.py
```

### Linux / macOS
```bash
# Method 1: Automatic (Recommended)
chmod +x run_gui.sh
./run_gui.sh

# Method 2: Manual
python3 setup_gui.py
python3 gui_launcher.py
```

---

## What Gets Installed?

Running `setup_gui.py` installs:

```
✓ PyQt6 >= 6.0.0       - Professional GUI framework
✓ PyQt6-sip            - Qt bindings
✓ numpy                - Numerical computing
✓ pandas               - Data manipulation
```

---

## GUI Launcher Features

### 8 Professional Tabs

1. **⚙️ Configuration** - MT5, trading, signal settings
2. **📈 Indicators** - SMA, RSI, ATR parameters
3. **🎓 Training** - Model training with progress
4. **📊 Backtest** - Strategy backtesting
5. **🔴 Real-time** - Live monitoring dashboard
6. **💹 Performance** - Trading metrics & P&L
7. **⚠️ Risk Management** - Position sizing, limits
8. **📋 Logs** - Activity tracking & export

### Key Features

✓ **Configuration Management**
  - Save/load configs as JSON
  - Validate settings before use
  - Reset to defaults anytime

✓ **Real-time Monitoring**
  - Live prediction generation
  - Signal generation (BUY/SELL/HOLD)
  - Prediction history tracking
  - Multiple data sources (CSV, MT5, yfinance)

✓ **Model Training**
  - Train RandomForest & LSTM models
  - Progress monitoring
  - Results display and export

✓ **Backtesting**
  - Test strategies on historical data
  - Performance metrics calculation
  - Results export (CSV/JSON)

✓ **Risk Management**
  - Automatic position sizing
  - Daily loss limits
  - Exposure tracking
  - P&L monitoring

✓ **Professional Logging**
  - Real-time log display
  - Multiple log levels
  - Export to file
  - System activity tracking

---

## First Time Usage

### Step 1: Install (1 minute)
```bash
python setup_gui.py
```

### Step 2: Configure (2 minutes)
```bash
python gui_launcher.py
# Opens GUI window
```

1. Go to **⚙️ Configuration** tab
2. Enter MT5 credentials:
   - MT5 Path
   - Login
   - Password
   - Server
3. Set trading parameters:
   - Symbol (XAUUSD)
   - Lot Size (0.1)
   - Stop Loss (100 pips)
   - Take Profit (200 pips)

### Step 3: Save (30 seconds)
```
File → Save Configuration
```

### Step 4: Run Training (5 minutes)
```
🎓 Training Tab → Start Training
```

### Step 5: Test Backtest (2 minutes)
```
📊 Backtest Tab → Run Backtest
```

### Step 6: Start Monitoring (Continuous)
```
🔴 Real-time Tab → Start Monitoring
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.10+ |
| RAM | 2 GB | 8 GB |
| Disk | 500 MB | 2 GB |
| Display | 1024x768 | 1400x900 |
| OS | Windows 7+ | Windows 10+ |

---

## Keyboard Shortcuts

- **Ctrl+S** - Save configuration
- **Ctrl+O** - Open configuration
- **Ctrl+N** - New configuration
- **Ctrl+Q** - Quit application

---

## Troubleshooting

### "Python not found"
```bash
# Add Python to PATH or use full path
C:\Python310\python.exe setup_gui.py
```

### "PyQt6 not installing"
```bash
pip install --upgrade pip
pip install PyQt6 --force-reinstall
```

### GUI looks different/ugly
```bash
# Try different style
# Edit gui_launcher.py line 20:
app.setStyle('Fusion')  # Try: 'Windows', 'Plasique', 'Motif'
```

### Configuration won't save
```bash
# Run as Administrator (Windows)
# Or check folder permissions
```

---

## Command Line Arguments

```bash
# (Future versions may support)
python gui_launcher.py --config myconfig.json
python gui_launcher.py --start-monitoring
python gui_launcher.py --autorun training
```

---

## Tips & Tricks

1. **Multiple Profiles**
   - Save different configs for different symbols
   - Quickly switch between profiles

2. **Auto-Save**
   - Save after each configuration change
   - Prevents losing settings

3. **Monitoring 24/7**
   - Leave real-time tab running in background
   - Check logs regularly for errors

4. **Backtest Before Trading**
   - Always run backtest first
   - Test different parameters

5. **Daily Backup**
   - Backup config.json daily
   - Backup logs regularly

---

## Next Steps

1. Read **GUI_USER_GUIDE.md** for detailed instructions
2. Read **QUICK_START.md** for trading setup
3. Review **DASHBOARD_GUIDE.md** for dashboard features
4. Check **README.md** for project overview

---

## Support

**Issues?** Check:
- Logs tab for error messages
- Troubleshooting section above
- Documentation files
- GitHub issues

**Questions?** See:
- GUI_USER_GUIDE.md (detailed)
- QUICK_START.md (trading)
- README.md (overview)

---

## Version Information

- **GUI Launcher:** v1.0.0
- **Python:** 3.8+
- **PyQt6:** 6.0+
- **Status:** Production Ready ✅

---

**Ready to trade?** Launch the GUI:

### Windows
```bash
run_gui.bat
```

### Linux/Mac
```bash
./run_gui.sh
```

Enjoy professional trading! 🚀📈
