# 📡 Signal Service - Quick Start Guide

## 🟢 Status: READY TO USE

Your Signal Service is now fully integrated and ready to broadcast trading signals via Telegram!

---

## 🚀 Launch in 3 Steps

```bash
# Step 1: Navigate to project directory
cd D:\AVENTA\Aventa_AI_2027\02_Aventa_Inovation_trading_v3\Aventa_Inova_2026

# Step 2: Launch the application
python gui_launcher.py

# Step 3: Click on "📡 Signal Service" tab
# (Located in the main window after "🚀 Live Trading")
```

---

## 📡 Your Pre-configured Telegram Bot

**Bot Token:** 
```
95006295:AAH4Bc1J8pv_x_2wDLstK-PeKvJiWZ7heXo
```

**Default Subscriber Chat ID:**
```
7521820149
```

✅ These are already pre-filled in the Signal Service tab!

---

## 🎮 Using the Signal Service Tab

### ⚙️ Configuration Sub-Tab
- View/edit bot settings
- Change symbols to broadcast (comma-separated)
- Adjust TP/SL percentages
- Click "Test Connection" to verify bot works
- Click "Save Configuration" to persist settings

### 👥 Subscribers Sub-Tab
- View your current subscribers (starting with 7521820149)
- Add new subscribers by entering their chat ID
- Remove subscribers with the delete button
- **"Send Test Signal"** - Try this first! It will send a sample signal to your subscriber

### 📊 History Sub-Tab
- View all signals that have been sent
- See timestamp, symbol, type, prices, and ML confidence scores
- **"Export to CSV"** - Downloads history to your Desktop

### 📈 Statistics Sub-Tab
- Dashboard with signal metrics
- See how many BUY vs SELL signals
- View success rate percentage
- Track total signals sent

---

## 🧪 First Time Setup (5 minutes)

1. **Launch GUI**
   ```bash
   python gui_launcher.py
   ```

2. **Navigate to Signal Service**
   - Click the "📡 Signal Service" tab

3. **Test Connection**
   - Go to "⚙️ Configuration" sub-tab
   - Click "🧪 Test Connection" button
   - Should show ✅ Connected

4. **Send Test Signal**
   - Go to "👥 Subscribers" sub-tab
   - Click "Send Test Signal" button
   - **Check your Telegram!** You should receive a message like:
     ```
     🚀 BUY XAUUSD @ 2045.50
     📊 ML Score: 0.87 | Confidence: 87%
     Target: 2077.28 (TP 1.5%) | Risk: 2025.95 (SL 1.0%)
     Risk/Reward: 1.5x
     ```

5. **Add More Subscribers (Optional)**
   - Enter additional chat IDs in "👥 Subscribers" tab
   - Click "Add Subscriber"
   - All subscribers will receive signals when broadcasting is enabled

---

## 🔄 How It Works

```
Your Trading System → Signal Detection → SignalBroadcaster → Telegram API
                        (ML + TA)         (Format + Send)       ↓
                                                              Chat ID(s)
                                                                 ↓
                                                          Signal Message
```

---

## 📊 Signal Format Example

**Detailed Format (Default):**
```
🚀 BUY XAUUSD @ 2045.50
📊 ML Score: 0.87 | Confidence: 87%
Target: 2077.28 (TP 1.5%) | Risk: 2025.95 (SL 1.0%)
Risk/Reward: 1.5x
📈 SMA(20): 2040.00 | RSI: 65
```

---

## ⚙️ Configuration Options

| Option | Default | Purpose |
|--------|---------|---------|
| Enable Service | OFF | Turn broadcasting on/off |
| Symbols | XAUUSD, EURUSD, GBPUSD | Which pairs to broadcast |
| Signal Type | ALL | BUY only, SELL only, or ALL |
| TP % | 1.5% | Take Profit percentage |
| SL % | 1.0% | Stop Loss percentage |

---

## 🎯 Next Steps

1. ✅ Launch GUI: `python gui_launcher.py`
2. ✅ Go to 📡 Signal Service tab
3. ✅ Test Telegram connection
4. ✅ Send test signal
5. ✅ Enable broadcasting when ready

---

**Status:** 🟢 PRODUCTION READY
