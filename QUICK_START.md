# 🚀 Quick Start - Dashboard Running Locally

## Prerequisites ✅

- Python 3.8+ (use existing venv)
- Required packages: streamlit, plotly, pandas

## Step 1: Install Dependencies

```bash
pip install streamlit plotly pandas
```

## Step 2: Generate Sample Data (Terminal 1)

Run the real-time monitor to generate prediction data:

```bash
python real_time_monitor.py --source csv --iterations 50
```

This will:
- Load XAUUSD data
- Generate 50 predictions
- Save to `logs/realtime_predictions.jsonl`

## Step 3: Launch Dashboard (Terminal 2)

```bash
streamlit run streamlit_dashboard.py
```

Or with specific port:

```bash
python -m streamlit run streamlit_dashboard.py --server.port 8501
```

## Step 4: Open in Browser

Dashboard will automatically open at:
```
http://localhost:8501
```

Or manually visit that URL.

## Dashboard Features 📊

### Main Metrics
- Total predictions count
- Buy/Sell/Hold signal ratios
- Latest closing price
- Model performance metrics

### Charts & Visualizations
- **Live Predictions**: Real-time price + prediction overlay
- **Signal Markers**: Green triangles (BUY), Red triangles (SELL)
- **Prediction Distribution**: Histogram of all predictions
- **Signal Pie Chart**: Proportion of BUY/SELL/HOLD

### Tabs
1. **📈 Live Predictions** - Charts and signal history
2. **📊 Statistics** - Distribution analysis
3. **🔧 Model Info** - Feature importance, test metrics
4. **📋 Raw Data** - Full dataset, CSV download

## Monitoring in Real-Time

**Keep both windows open:**

| Window | Purpose |
|--------|---------|
| Terminal 1 | Real-time monitor generating new predictions |
| Terminal 2 | Streamlit dashboard displaying live data |

The dashboard auto-refreshes every 30 seconds.

## Continuous Monitoring

For 24/7 monitoring, use:

```bash
# Terminal 1 - Run indefinitely
python real_time_monitor.py --source csv --iterations 999999 --interval 60

# Terminal 2 - Dashboard
streamlit run streamlit_dashboard.py
```

## Live MT5 Data

When ready to trade with live data:

```bash
python real_time_monitor.py \
    --source mt5 \
    --login YOUR_LOGIN \
    --password YOUR_PASSWORD \
    --server YOUR_SERVER \
    --symbol XAUUSD \
    --interval 60
```

## Troubleshooting

### Dashboard won't load

1. Check if Streamlit is installed:
```bash
pip install streamlit
```

2. Verify port is free:
```bash
# Windows
netstat -ano | find ":8501"

# Linux/Mac
lsof -i :8501
```

3. Try different port:
```bash
streamlit run streamlit_dashboard.py --server.port 8502
```

### No data showing

1. Check log file exists:
```bash
ls -la logs/realtime_predictions.jsonl
```

2. Run monitor first, wait 10 seconds
3. Click "Refresh Now" in sidebar
4. Check browser console (F12) for errors

### High CPU/Memory

- Limit monitor iterations: `--iterations 1000`
- Increase interval: `--interval 5`
- Reduce lookback bars in code

## Next Steps

After dashboard is running:

1. ✅ **Monitor signals** in real-time
2. ⏭️ **Fine-tune thresholds** based on signal distribution
3. ⏭️ **Add alerts** (Telegram/Discord)
4. ⏭️ **Connect to MT5** for auto-execution
5. ⏭️ **Deploy to cloud** (AWS/DigitalOcean)

## File Locations

```
Project Root/
├── streamlit_dashboard.py     ← Main dashboard script
├── real_time_monitor.py       ← Real-time prediction generator
├── inference.py               ← ML inference engine
├── logs/
│   └── realtime_predictions.jsonl  ← Live prediction data
└── models/
    ├── rf_baseline.pkl        ← Trained model
    └── rf_baseline_scaler.pkl ← Feature scaler
```

## Support

For issues, check:
- Streamlit docs: https://docs.streamlit.io
- Project repo: https://github.com/gustianaagg8217/Aventa_Inova_2026

---

**Happy monitoring! 🎯**
