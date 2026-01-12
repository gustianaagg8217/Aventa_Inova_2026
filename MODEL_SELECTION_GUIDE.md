# 🤖 Model Selection Guide

## Overview

When you run `start_trading.py` and select option **[1] START AUTO TRADING BOT**, the system now lets you **choose which trained model to use** or **automatically use the latest one**.

---

## Workflow

### 1️⃣ Start the Launcher
```bash
python start_trading.py
```

### 2️⃣ Select Option [1]
```
[1] 🚀 START AUTO TRADING BOT
```

### 3️⃣ Pre-Flight Checks
The system will:
- ✅ Validate config files (config.yaml, trading_config.yaml)
- ✅ Scan for trained models in `/models` folder
- ✅ Verify MT5 credentials

### 4️⃣ Model Selection Menu
```
[MODEL SELECTION]

  [A] Use LATEST model (default)
  [1-N] Select specific model

Select model (press Enter for latest):
```

**Options:**
- **Press Enter or type `A`** → Auto-select latest model by modification time
- **Type `1`, `2`, etc.** → Select a specific trained model
- **Invalid input** → Defaults to latest model

### 5️⃣ Confirm Trading Mode
```
[BOT CONFIG]
  Symbol: BTCUSD
  Mode: 💰 LIVE TRADING
  Model: rf_baseline.pkl

⚠️  WARNING: LIVE TRADING MODE IS ENABLED
Type 'LIVE' to confirm:
```

Type `LIVE` to confirm and start trading.

---

## Available Models

The system will display all trained models with information:

```
[CHECK] Scanning for trained models...
✅ Found 2 trained model(s):

   [1] rf_baseline.pkl (Random Forest, 1.45 MB, 2024-12-20 15:30)
   [2] lstm_model.pt (LSTM, 2.34 MB, 2024-12-21 09:15)
```

### Model Types

| Model | File | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| **Random Forest** | `*.pkl` | Fast (5-10s training) | ⭐⭐⭐⭐ | Default, stable |
| **LSTM** | `*.pt` | Slower (1-2m training) | ⭐⭐⭐⭐⭐ | Better accuracy, more patterns |

---

## Examples

### Example 1: Auto-Select Latest
```
[MODEL SELECTION]

  [A] Use LATEST model (default)
  [1-2] Select specific model

Select model (press Enter for latest): [ENTER]

✅ Using latest model: lstm_model
```

### Example 2: Select Specific Model
```
[MODEL SELECTION]

  [A] Use LATEST model (default)
  [1-2] Select specific model

Select model (press Enter for latest): 1

✅ Using selected model: rf_baseline
```

### Example 3: TA-Only Mode (No Models)
```
[CHECK] Scanning for trained models...
⚠️  No trained models found in models
   Run: python train_models.py

⚠️  No models found. Continuing with TA-only mode (no ML)
```

---

## Training New Models

To add more trained models to the selection menu:

### Random Forest (Default)
```bash
python train_models.py --model sklearn
```
**Output:** `models/rf_baseline.pkl`

### LSTM (Neural Network)
```bash
python train_models.py --model lstm --epochs 20
```
**Output:** `models/lstm_model.pt`

### Both Models
```bash
# First train Random Forest
python train_models.py --model sklearn

# Then train LSTM
python train_models.py --model lstm --epochs 20
```

Now `start_trading.py` will show both and let you choose! ✨

---

## Signal Generation

Once the model is selected:

1. **Load Market Data** → OHLCV candlesticks (BTCUSD M1)
2. **Technical Indicators** → SMA 5/50, RSI, ATR
3. **ML Prediction** → Get signal from selected model
4. **Signal Confirmation** → TA + ML validation
5. **Execute Trade** → Place order on MT5

```
Market Data → [Indicators] → [ML Model] → [Signal] → [Trade]
                                    ↑
                        (Depends on user selection)
```

---

## Environment Variables

The following are required in environment before trading starts:

```powershell
# PowerShell (Windows)
$env:MT5_ACCOUNT = "your_account_number"
$env:MT5_PASSWORD = "your_password"
$env:MT5_SERVER = "VantageInternational-Demo"
```

```bash
# Linux/Mac
export MT5_ACCOUNT="your_account_number"
export MT5_PASSWORD="your_password"
export MT5_SERVER="VantageInternational-Demo"
```

---

## Troubleshooting

### ❓ "No trained models found"
**Solution:** Train models first
```bash
python train_models.py --model sklearn
```

### ❓ Model selection doesn't appear
**Solution:** Make sure `/models` folder exists
```bash
mkdir models
```

### ❓ Can't confirm with 'LIVE'
**Solution:** 
- Make sure paper_trading is `false` in config.yaml
- Type exactly: `LIVE` (all caps)

### ❓ "Invalid selection, using latest model"
**Solution:** 
- Press Enter or type `A` for auto-select
- Or type `1`, `2`, etc. for specific model number

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start launcher | `python start_trading.py` |
| Select option | Type `1` for AUTO TRADING BOT |
| Auto-select model | Press Enter |
| Select model #1 | Type `1` |
| Train new model | `python train_models.py` |
| View config | Edit `config/config.yaml` |
| Check credentials | Look in environment variables |

---

## Summary

✅ **Current Behavior:**
- `start_trading.py` now shows list of trained models
- You can choose which model to use
- Or press Enter to auto-select latest
- Bot will use your selection + Technical Analysis

✅ **Benefits:**
- Compare model performance by training multiple
- Switch between models without retraining
- TA-only fallback if no models available
- Full control over trading system
