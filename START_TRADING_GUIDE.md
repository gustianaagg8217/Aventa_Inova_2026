# 🤖 START TRADING - User Guide

Complete guide untuk menggunakan **start_trading.py** - Unified Trading Bot Launcher untuk Aventa_Inova_2026.

---

## 📋 Daftar Isi

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Quick Start](#quick-start)
4. [Menu Options](#menu-options)
5. [Workflow Examples](#workflow-examples)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## Overview

**start_trading.py** adalah entry point utama untuk seluruh sistem trading HFT. Ini menyediakan interface menu terpusat untuk:

✅ **Auto Trading** - Jalankan bot trading otomatis  
✅ **Dashboard** - Monitor performa trading real-time  
✅ **Signal Monitor** - Lihat prediksi ML dan indikator TA  
✅ **Train Models** - Latih ulang model ML dengan data terbaru  
✅ **Backtest** - Tes strategi dengan data historis  
✅ **Download Data** - Download data dari MT5 untuk training  

---

## Requirements

Sebelum menjalankan, pastikan:

### 1. **Python & Dependencies**
```bash
# Python 3.10+
python --version

# Install requirements
pip install -r requirements.txt
```

### 2. **MetaTrader 5**
- Instalasi MT5 di sistem Windows
- Path install MT5: `C:\Program Files\MetaTrader 5` (atau custom path)
- MT5 Account dengan login credentials

### 3. **Struktur Folder**
```
Aventa_Inova_2026-main/
├── start_trading.py          ← Main launcher
├── auto_trading.py           ← Auto trading bot
├── train_models.py           ← Model training
├── download_data.py          ← Data download
├── config/
│   ├── config.yaml
│   ├── trading_config.yaml
│   └── strategy_params.yaml
├── data/                     ← CSV data files
├── models/                   ← Trained models
└── logs/                     ← Log files
```

### 4. **Environment Variables (Optional)**
Setup awal untuk menghindari input berulang:

```powershell
# Windows PowerShell
$env:MT5_PATH = "C:\Program Files\MetaTrader 5"
$env:MT5_ACCOUNT = "12345678"
$env:MT5_PASSWORD = "your_password"
$env:MT5_SERVER = "VantageInternational-Live"
```

---

## Quick Start

### Langkah 1: Jalankan Launcher

```bash
cd Aventa_Inova_2026-main
python start_trading.py
```

Output akan terlihat seperti:

```
════════════════════════════════════════════════════════════════════════════════
  🤖 HFT TRADING SYSTEM LAUNCHER
════════════════════════════════════════════════════════════════════════════════

Time: 2026-01-12 19:30:45
Symbol: XAUUSD | Live Trading: Enabled

════════════════════════════════════════════════════════════════════════════════
  🤖 TRADING SYSTEM MENU
════════════════════════════════════════════════════════════════════════════════

Select an option:

  [1] 🚀 START AUTO TRADING BOT
       → Runs full ML+TA trading with all features
       → Monitors positions and sends Telegram alerts

  [2] 📊 MONITOR DASHBOARD
       → Real-time trading metrics & performance
       → Run this in parallel window

  [3] 📡 CHECK SIGNALS (Real-Time Monitor)
       → View live ML predictions
       → Technical analysis indicators

  [4] 🧠 TRAIN NEW MODELS
       → Re-train ML models with latest data
       → Update strategy parameters

  [5] 📈 RUN BACKTEST
       → Test strategy with historical data
       → Analyze performance metrics

  [6] 💾 DOWNLOAD DATA
       → Download historical data from MT5
       → Configure account, server, symbol

  [0] ❌ EXIT

Enter your choice (0-6):
```

### Langkah 2: Pilih Menu

Input angka 0-6 sesuai kebutuhan.

---

## Menu Options

### **Menu [1] 🚀 START AUTO TRADING BOT**

Jalankan bot trading otomatis dengan ML + Technical Analysis.

#### **Flow:**

**Step 1/5: Symbol Selection**
- Pilih symbol mau trade apa
- Opsi: XAUUSD, BTCUSD, EURUSD, custom, dll
- Default: XAUUSD (Gold)

**Step 2/5: Configuration Check**
- Validasi config files ada
- Cek models folder
- Cek credentials MT5

**Step 3/5: Model Selection**
- Pilih model ML untuk prediction
- Auto-select latest model atau manual
- Fallback ke TA-only jika model tidak ada

**Step 4/5: Credentials Validation**
- Validasi MT5 credentials
- Prompt untuk update jika belum set

**Step 5/5: Pre-Flight Status**
- Review semua setting
- Confirm LIVE trading warning
- Start auto_trading.py

#### **Configuration Preview:**
```
════════════════════════════════════════════════════════════════════════════════
  ✅ PRE-FLIGHT STATUS
════════════════════════════════════════════════════════════════════════════════

[CHECKS]

  Config Files:      ✅ READY
  ML Models:         ✅ READY
  Selected Model:    rf_baseline.pkl
  MT5 Credentials:   ✅ READY

[BOT CONFIGURATION]

  Symbol:            XAUUSD
  Mode:              💰 LIVE TRADING
  ML Model:          rf_baseline
  MT5 Path:          C:\Program Files\MetaTrader 5
```

#### **Tips:**
- Jalankan menu [6] dulu untuk download data
- Jalankan menu [4] untuk train models
- Gunakan PAPER TRADING dulu sebelum LIVE
- Buka dashboard (menu [2]) di window terpisah untuk monitoring

---

### **Menu [2] 📊 MONITOR DASHBOARD**

Real-time dashboard untuk monitor trading performance.

#### **Fitur:**
- Live positions & P&L
- Equity curve
- Trade history
- Performance metrics
- Risk indicators

#### **Tips:**
- Buka di terminal terpisah (parallel dengan auto trading)
- Refresh interval default: 2 detik
- Akses via browser jika ada web dashboard

---

### **Menu [3] 📡 CHECK SIGNALS (Real-Time Monitor)**

Monitor real-time ML predictions dan technical indicators.

#### **Fitur:**
- Live signal strength
- ML prediction value
- Technical analysis output
- Market regime detection

#### **Cara Kerja:**
1. Jalankan monitor
2. Input credentials (atau sudah tersimpan)
3. Real-time display signals setiap interval

---

### **Menu [4] 🧠 TRAIN NEW MODELS**

Latih ulang model ML dengan data terbaru.

#### **Flow:**

**Step 1/3: Data Selection**
```
Found 5 data file(s):

  [1] GOLD_ls_M1_59days.csv (3,229.3 KB)
  [2] XAUUSD_M1_59days.csv (3,338.6 KB)
  [3] BTCUSD_M1_59days.csv (5,494.0 KB)
  [4] EURUSD_M1_59days.csv (2,847.2 KB)
  [5] GBPUSD_M1_59days.csv (2,156.8 KB)

  [0] Use latest/largest file (auto-select)

Select data file (press Enter for auto):
```
- Pilih file mau training
- Symbol auto-detect dari filename
- Default: file terbesar (paling lengkap)

**Step 2/3: Model Selection**
```
Available models:

  [1] Random Forest (sklearn) - Faster, baseline
  [2] LSTM (PyTorch) - More advanced, slower
  [3] Both - Train both models
```
- Pilih tipe model
- Default: Random Forest

**Step 3/3: Training Configuration**
```
  Data File: XAUUSD_M1_59days.csv
  Symbol: XAUUSD
  Model Type: Random Forest

Start training? (y/n):
```
- Review setting
- Confirm start training

#### **Training Process:**
- Feature engineering (SMA, RSI, ATR, dll)
- Dataset split (train/val/test)
- Model training
- Metrics calculation
- Model save to `models/` folder
- Logs to `logs/training_run_*.json`

#### **Output Files:**
```
models/
├── rf_baseline.pkl              ← Trained model
├── rf_baseline_scaler.pkl       ← Feature scaler
├── rf_baseline_metadata.json    ← Training metadata
├── lstm_model.pt                ← LSTM weights
├── lstm_model_scaler.pkl        ← LSTM scaler
└── lstm_model_metadata.json     ← LSTM metadata

logs/
└── training_run_*.json          ← Training history
```

#### **Tips:**
- Pastikan ada data file di folder `data/` (gunakan menu [6])
- Training time: 5-30 menit tergantung model & data size
- LSTM lebih akurat tapi lebih lambat
- Random Forest lebih cepat, cocok untuk quick training
- Monitor logs untuk accuracy metrics

---

### **Menu [5] 📈 RUN BACKTEST**

Test strategi dengan data historis.

#### **Fitur:**
- Historical data backtesting
- Trade-by-trade performance
- Metrics: Sharpe, Win Rate, Max Drawdown, dll
- Equity curve visualization

#### **Output:**
```
logs/
└── backtest_results_*.csv       ← Detailed trade results

Metrics:
- Total Trades
- Win Rate (%)
- Profit Factor
- Sharpe Ratio
- Maximum Drawdown
- dll
```

#### **Tips:**
- Run backtest sebelum live trading
- Validate strategy performance
- Check risk metrics (drawdown, loss limit)
- Adjust parameters jika performance tidak memuaskan

---

### **Menu [6] 💾 DOWNLOAD DATA**

Download data historis dari MT5 untuk training & backtesting.

#### **Flow:**

**Step 1/5: MT5 Path**
```
Common MT5 paths:
  1. C:\Program Files\MetaTrader 5 (Default)
  2. C:\Program Files (x86)\MetaTrader 5
  3. Custom path...

Select (1-3): 1

✅ MT5 Path: C:\Program Files\MetaTrader 5
```

**Step 2/5: Account Number**
```
Enter MT5 Account Number: 12345678

✅ Account: 12345678
```

**Step 3/5: Password**
```
Enter MT5 Password: 

✅ Password: ****
```

**Step 4/5: Server**
```
Common servers:
  1. VantageInternational-Demo
  2. VantageInternational-Live
  3. Other...

Select (1-3): 2

✅ Server: VantageInternational-Live
```

**Step 5/5: Symbol**
```
Available symbols:

  [1] Gold (XAUUSD)
  [2] Bitcoin (BTCUSD)
  [3] EUR/USD (EURUSD)
  [4] GBP/USD (GBPUSD)
  [5] USD/JPY (USDJPY)
  [6] Gold Spot (GOLD.ls)
  [0] Enter custom symbol

Select symbol: 1

✅ Symbol: XAUUSD
```

**Configuration Summary & Confirmation**
```
════════════════════════════════════════════════════════════════════════════════
  📊 DOWNLOAD CONFIGURATION
════════════════════════════════════════════════════════════════════════════════

[CONFIGURATION SUMMARY]

  MT5 Path:    C:\Program Files\MetaTrader 5
  Account:     12345678
  Server:      VantageInternational-Live
  Symbol:      XAUUSD
  Output Dir:  data/

Start downloading? (y/n): y
```

#### **Output:**
```
data/
├── XAUUSD_M1_59days.csv
├── BTCUSD_M1_30days.csv
├── EURUSD_M1_90days.csv
└── ...
```

#### **Tips:**
- Download minimal 30 hari data
- Untuk training lebih baik 60-90 hari
- Multiple symbols → multiple downloads
- Keep credentials safe (not in version control)
- First time setup lebih lama (mungkin 5-10 menit)

---

## Workflow Examples

### **Workflow 1: First Time Setup**

```
1. python start_trading.py
2. Menu [6] - Download Data
   - Input MT5 credentials
   - Select symbol (XAUUSD)
   - Download complete ✓
3. Menu [4] - Train Models
   - Auto-select data file
   - Random Forest model
   - Training complete ✓
4. Menu [1] - Start Auto Trading
   - Select symbol (XAUUSD)
   - Paper trading mode
   - Bot running ✓
5. Menu [2] - Monitor Dashboard
   - Open di terminal terpisah
   - Monitor trades ✓
```

### **Workflow 2: Add New Symbol**

```
1. Menu [6] - Download Data
   - Input credentials
   - Select BTCUSD
   - Download complete ✓
2. Menu [4] - Train Models
   - Select BTCUSD data file
   - LSTM model (more advanced)
   - Training complete ✓
3. Menu [1] - Start Auto Trading
   - Select symbol BTCUSD
   - Review config
   - Start trading ✓
```

### **Workflow 3: Optimize Existing Model**

```
1. Menu [4] - Train Models
   - Latest data selected
   - Both models (sklearn + LSTM)
   - Training takes longer ✓
2. Menu [5] - Run Backtest
   - Test new models
   - Check performance ✓
3. Menu [1] - Start Auto Trading
   - Use new optimized model
   - Monitor results ✓
```

### **Workflow 4: Daily Update**

```
Daily at market open:
1. Menu [6] - Download Data (latest 1-7 days)
2. Menu [4] - Train Models (quick: Random Forest only)
3. Menu [1] - Start Auto Trading (use new model)
4. Menu [2] - Monitor Dashboard
```

---

## Troubleshooting

### **Problem: "No data file found in data folder"**

**Solusi:**
1. Menu [6] - Download Data
2. Tunggu download selesai
3. Cek folder `data/` ada CSV file
4. Coba menu [4] Train lagi

---

### **Problem: "MT5 credentials invalid"**

**Solusi:**
1. Validasi account number (benar?)
2. Validasi password (benar?)
3. Validasi server name
4. Coba set environment variable:
   ```powershell
   $env:MT5_ACCOUNT = "your_account"
   $env:MT5_PASSWORD = "your_password"
   $env:MT5_SERVER = "your_server"
   ```

---

### **Problem: "No trained models found"**

**Solusi:**
1. Menu [4] - Train Models
2. Select data file
3. Select model type
4. Tunggu training selesai
5. Models akan disimpan di `models/` folder

---

### **Problem: Training too slow**

**Solusi:**
1. Gunakan Random Forest (faster) bukan LSTM
2. Gunakan data file yang lebih kecil
3. Kurangi data size kalau mungkin
4. Check CPU/RAM availability

---

### **Problem: "Cannot start: MT5 Path not found"**

**Solusi:**
1. Validasi instalasi MT5
2. Gunakan full path yang benar
3. Default: `C:\Program Files\MetaTrader 5`
4. Atau: `C:\Program Files (x86)\MetaTrader 5`

---

### **Problem: Model accuracy rendah**

**Solusi:**
1. Gunakan data lebih banyak (90+ days)
2. Coba LSTM model (lebih sophisticated)
3. Adjust feature engineering di `train_models.py`
4. Run backtest untuk validate
5. Fine-tune strategy parameters

---

## FAQ

### **Q: Apakah perlu GPU untuk training?**
**A:** Default menggunakan CPU. GPU optional untuk LSTM (faster training). Cek `--device cuda` parameter.

---

### **Q: Berapa lama training model?**
**A:** 
- Random Forest: 5-10 menit
- LSTM: 15-30 menit
- Tergantung data size & hardware

---

### **Q: Boleh trade LIVE dari awal?**
**A:** **TIDAK RECOMMENDED!** 
1. Gunakan PAPER TRADING dulu
2. Validate di backtest
3. Monitor hasil beberapa hari
4. Baru enable LIVE trading

---

### **Q: Berapa banyak data yang ideal?**
**A:** 
- Minimum: 30 hari
- Recommended: 60-90 hari
- Lebih banyak = lebih akurat (biasanya)

---

### **Q: Bisa trade multiple symbols sekaligus?**
**A:** Ya! Jalankan multiple instances:
```bash
# Terminal 1: XAUUSD
python start_trading.py
# Menu [1] - XAUUSD

# Terminal 2: BTCUSD
python start_trading.py
# Menu [1] - BTCUSD
```

---

### **Q: Bagaimana backup models?**
**A:** 
```bash
# Backup models folder
xcopy models\ backups\models_2026_01_12 /E /I

# Restore jika perlu
xcopy backups\models_2026_01_12 models\ /E /I /Y
```

---

### **Q: Bisa customize strategy?**
**A:** Ya! Edit file:
- `config/strategy_params.yaml` - Strategy parameters
- `auto_trading.py` - Trading logic
- `train_models.py` - Feature engineering
- `strategy/` folder - Strategy modules

---

### **Q: Apa bedanya Paper vs Live Trading?**
**A:**
| Aspek | Paper | Live |
|-------|-------|------|
| Real Money | ❌ No | ✅ Yes |
| Risk | 0 | High |
| untuk Testing | ✅ Yes | ❌ No |
| Validation | ✅ Yes | ❌ No |

---

### **Q: Gimana kalau bot error saat trading?**
**A:**
1. Emergency stop: Ctrl+C
2. Check logs: `logs/` folder
3. Review error message
4. Fix issue
5. Restart menu [1]

---

### **Q: Bisa automated scheduling?**
**A:** Ya! Setup Windows Task Scheduler:
1. Create task
2. Trigger: Daily at X time
3. Action: `python start_trading.py` + input script
4. Or gunakan cron (Linux)

---

## Tips & Best Practices

### ✅ DO's:
- ✅ Download data sebelum trading
- ✅ Train models dengan data terbaru
- ✅ Validate di backtest dulu
- ✅ Use paper trading untuk testing
- ✅ Monitor dashboard real-time
- ✅ Backup models secara berkala
- ✅ Check logs untuk errors
- ✅ Keep credentials secure

### ❌ DON'Ts:
- ❌ Don't enable live trading langsung
- ❌ Don't use outdated models
- ❌ Don't ignore error messages
- ❌ Don't share credentials
- ❌ Don't trade without sufficient capital
- ❌ Don't modify code tanpa understanding
- ❌ Don't leave bot unattended (first time)

---

## Support & Resources

📚 **Documentation:**
- [README.md](README.md) - Project overview
- [CONFIGURATION.md](CONFIGURATION.md) - Config reference
- [STRATEGY.md](STRATEGY.md) - Strategy details
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide

🐛 **Troubleshooting:**
- Check logs: `logs/` folder
- Review error in console output
- Validate credentials
- Check file permissions
- Verify folder structure

📧 **Issues:**
- GitHub Issues: https://github.com/gustianaagg8217/Aventa_Inova_2026/issues
- Contact: Check CONTRIBUTING.md

---

## Changelog

### v1.0 (2026-01-12)
- ✅ Added Symbol Selection (Menu [1])
- ✅ Added Download Data (Menu [6])
- ✅ Added Train Models with data selection (Menu [4])
- ✅ Improved error handling
- ✅ Created START_TRADING_GUIDE.md

---

**Last Updated:** 2026-01-12  
**Version:** 1.0  
**Status:** Production Ready

---

*Built with ❤️ for professional traders*
