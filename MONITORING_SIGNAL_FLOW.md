# 🔄 SIGNAL FLOW: Monitoring Tab Real-time ke Telegram

## Step-by-Step Flow

```
TAHAP 1: USER ACTION
═════════════════════════════════════════════════════════════════
🖱️ User Klik "▶ Start Monitoring" di Real-time Tab
                          ↓
              RealTimeTab.start_monitoring()


TAHAP 2: WORKER INITIALIZATION
═════════════════════════════════════════════════════════════════
MonitoringWorker(config) dibuat dengan config:
  • signal_service_enabled → TRUE ✓
  • signal_bot_token → "95006295:AAH..." ✓
  • signal_chat_ids → "7521820149" ✓
  • signal_symbols → "XAUUSD,EURUSD,GBPUSD" ✓
  • signal_tp_percent → 1.5% ✓
  • signal_sl_percent → 1.0% ✓
  • signal_min_confidence → 0.0001 ✓
  • signal_filter_type → "ALL" ✓
                          ↓
              worker.start() [Background Thread]


TAHAP 3: MONITORING RUN
═════════════════════════════════════════════════════════════════
while self.running:
    
    📊 STEP A: Fetch Market Data
    ├─ Source: CSV atau MT5
    └─ Last N candles loaded
    
                          ↓
    
    🤖 STEP B: Make Prediction
    ├─ ML Model inference
    ├─ Result: prediction score (-1 to +1)
    └─ Convert to Signal: BUY / SELL / HOLD
    
                          ↓
    
    ✅ STEP C: Emit Result to UI
    ├─ self.update.emit(result)
    └─ Real-time Tab metrics update
    
                          ↓
    
    🔍 STEP D: Check Broadcast Condition
    ├─ Is broadcaster initialized?
    ├─ Is signal BUY or SELL? (not HOLD)
    └─ If YES → proceed to broadcast
               If NO → skip broadcast
    
                          ↓
    
    📡 STEP E: _broadcast_signal()
    ├─ Check: Signal Type Filter
    │         └─ Signal Filter: ALL (✓ pass)
    │
    ├─ Check: Symbol Filter
    │         └─ "XAUUSD" in ["XAUUSD","EURUSD","GBPUSD"] ✓
    │
    ├─ Check: Confidence Threshold
    │         └─ |prediction| > 0.0001 ✓
    │
    ├─ Calculate TP/SL
    │ ├─ TP = Entry + (Entry × 1.5%)
    │ ├─ SL = Entry - (Entry × 1.0%)
    │ └─ RR Ratio = 1.5
    │
    └─ For each Chat ID (7521820149):
                          ↓
    
    📲 STEP F: Send to Telegram
    ├─ broadcaster.send_signal(...)
    ├─ Telegram API call
    ├─ Signal message formatted
    └─ ✓ Message sent!
    
                          ↓
    
    💾 STEP G: Log to History
    ├─ CSV file updated
    ├─ Timestamp, Symbol, Type, Price, ML Score
    └─ ✓ Logged!
    
                          ↓
    
    ⏰ STEP H: Wait for Next Iteration
    ├─ msleep(monitoring_interval)
    └─ Loop continues...


TAHAP 4: TELEGRAM NOTIFICATION
═════════════════════════════════════════════════════════════════
📱 User's Telegram receives:

    🚀 BUY XAUUSD @ 2045.50
    📊 ML Score: 0.87 | Confidence: 87%
    Target: 2077.28 (TP 1.5%)
    Risk: 2025.95 (SL 1.0%)
    Risk/Reward: 1.5x
    📈 Updated: 2026-01-11 09:30:00
```

---

## 📊 Component Responsibilities

| Component | Role | Called From |
|-----------|------|-------------|
| **RealTimeTab** | UI Management | User clicks "Start Monitoring" |
| **MonitoringWorker.run()** | Signal Detection Loop | Runs in QThread |
| **SignalBroadcaster** | Telegram Broadcasting | _broadcast_signal() |
| **_broadcast_signal()** | Filtering + Calculation | MonitoringWorker.run() |
| **TradingConfig** | Configuration Storage | Shared to all components |
| **Telegram API** | Message Delivery | broadcaster.send_signal() |

---

## 🎯 Key Decision Points

### 1. Is Signal Service Enabled?
```
if self.config.signal_service_enabled:
    broadcaster = SignalBroadcaster(...)  ✓ Setup
else:
    broadcaster = None                    ✗ Skip all broadcasting
```

### 2. Is Signal Valid for Broadcasting?
```
if broadcaster and result.get('signal') in ['BUY', 'SELL']:
    self._broadcast_signal(...)           ✓ Broadcast
else:
    # HOLD signal or no broadcaster       ✗ Skip
```

### 3. Pass All Filters?
```
Signal Type:   signal_filter_type == signal_type  ✓
Symbol:        symbol in signal_symbols            ✓
Confidence:    |prediction| >= min_confidence     ✓
```

### 4. Broadcast to All Chat IDs
```
for chat_id in signal_chat_ids.split(','):
    broadcaster.send_signal(chat_id=int(chat_id))
```

---

## ✅ Verification Checklist

- [x] User clicks "Start Monitoring"
- [x] MonitoringWorker created with full config
- [x] MonitoringWorker.run() starts in background
- [x] RealTimeMonitor detects signals
- [x] SignalBroadcaster initialized
- [x] Signal detected? → Call _broadcast_signal()
- [x] Filters passed? → Call broadcaster.send_signal()
- [x] Telegram API call made
- [x] Message formatted and sent
- [x] Logged to CSV history
- [x] Loop continues for next signal

---

## 🚀 Result

**Monitoring Tab Real-time → Signal Detected → Telegram Message ✅**

Setiap kali monitoring mendeteksi BUY atau SELL signal, otomatis terkirim ke Telegram dalam hitungan detik!
