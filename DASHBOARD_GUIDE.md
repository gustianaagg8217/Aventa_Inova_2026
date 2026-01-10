# 📊 Monitoring Dashboard Setup Guide

## Streamlit Dashboard

A real-time web-based dashboard for monitoring ML predictions and trading signals.

### Installation

Streamlit is already listed in `requirements.txt`. Install dependencies:

```bash
pip install -r requirements.txt
```

Or install Streamlit directly:

```bash
pip install streamlit>=1.28.0 plotly pandas
```

### Quick Start

1. **Start real-time monitoring** (in one terminal):

```bash
python real_time_monitor.py --source csv --iterations 100
```

This will:
- Load historical XAUUSD data
- Generate predictions every 1 second
- Save results to `logs/realtime_predictions.jsonl`

2. **Launch dashboard** (in another terminal):

```bash
streamlit run streamlit_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Dashboard Features

#### 📈 **Live Predictions Tab**
- **Real-time chart** showing price and predictions
- **Trading signals** marked with triangles (🟢 BUY, 🔴 SELL)
- **Signal history** table with recent predictions
- Interactive hover for details

#### 📊 **Statistics Tab**
- **Prediction distribution** histogram
- **Signal pie chart** (BUY/SELL/HOLD ratios)
- **Summary statistics** (mean, std, min, max, median)

#### 🔧 **Model Info Tab**
- **Model metadata** (type, estimators, parameters)
- **Test metrics** (R², MAE, MSE)
- **Feature importances** bar chart
- **Training data** information

#### 📋 **Raw Data Tab**
- Full prediction dataset
- Download as CSV

### Live Trading Data Sources

#### Using MetaTrader 5 (Live)

```bash
python real_time_monitor.py \
    --source mt5 \
    --login 123456 \
    --password your_password \
    --server your_server \
    --symbol XAUUSD \
    --interval 60
```

Requirements:
- MetaTrader 5 terminal running
- Valid account credentials
- `pip install MetaTrader5`

#### Using Yahoo Finance (Demo)

```bash
python real_time_monitor.py \
    --source yfinance \
    --symbol GC=F \
    --interval 300 \
    --iterations 50
```

Note: yfinance has limited real-time data (5-15 minute delay)

#### Using CSV Historical Data (Backtest)

```bash
python real_time_monitor.py \
    --source csv \
    --data-file data/XAUUSD_M1_59days.csv \
    --interval 0.5 \
    --iterations 500
```

### Dashboard Configuration

Edit the sidebar in the dashboard to:
- Change **Model Directory** (default: `models`)
- Change **Log File** (default: `logs/realtime_predictions.jsonl`)
- **Refresh data** manually
- **Open logs directory**

### Advanced Usage

#### Running in Background

Windows:
```batch
start "" streamlit run streamlit_dashboard.py
```

Linux/Mac:
```bash
streamlit run streamlit_dashboard.py &
```

#### Custom Port

```bash
streamlit run streamlit_dashboard.py --server.port 8080
```

#### Headless Mode (for servers)

```bash
streamlit run streamlit_dashboard.py --logger.level=error --server.headless true
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_dashboard.py", "--server.port=8501"]
```

Build and run:

```bash
docker build -t aventa-dashboard .
docker run -p 8501:8501 -v $(pwd)/logs:/app/logs -v $(pwd)/models:/app/models aventa-dashboard
```

### Cloud Deployment

#### Streamlit Cloud

1. Push code to GitHub
2. Deploy at [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Select repository and file
4. App runs automatically

#### AWS EC2

```bash
# SSH into instance
ssh -i key.pem ubuntu@your-instance

# Clone repo and setup
git clone https://github.com/gustianaagg8217/Aventa_Inova_2026.git
cd Aventa_Inova_2026
pip install -r requirements.txt

# Run in screen
screen -S monitor
python real_time_monitor.py --source csv --iterations 999999

screen -S dashboard
streamlit run streamlit_dashboard.py --server.port 80 --server.address 0.0.0.0
```

Access at: `http://your-instance-public-ip`

#### DigitalOcean App Platform

1. Create new app from GitHub
2. Set environment: Python 3.10
3. Build command: `pip install -r requirements.txt`
4. Run command: `streamlit run streamlit_dashboard.py --server.port 8080`

### Monitoring Tips

#### 1. Window Layout

Use two windows side-by-side:
- **Left**: Terminal with real_time_monitor.py
- **Right**: Browser with Streamlit dashboard

#### 2. Signal Filtering

The dashboard automatically shows:
- 🟢 **GREEN triangles**: BUY signals
- 🔴 **RED triangles**: SELL signals
- 🟡 **YELLOW dots**: HOLD signals

#### 3. Feature Analysis

Top 3 features for XAUUSD:
1. **ATR** (16.4%) - Volatility
2. **Log Returns** (15.7%) - Momentum
3. **RSI** (15.4%) - Overbought/Oversold

#### 4. Performance Baseline

Baseline (mean predictor) metrics:
- MSE: 9.62e-08
- MAE: 0.000224
- R²: -0.0000258

Our model metrics:
- Test MSE: 1.01e-07
- Test MAE: 0.000230
- Test R²: -0.048

### Troubleshooting

#### Dashboard won't start

```bash
# Clear Streamlit cache
streamlit cache clear

# Reinstall dependencies
pip install --upgrade streamlit plotly pandas
```

#### No data showing

1. Check log file exists: `logs/realtime_predictions.jsonl`
2. Run monitor first: `python real_time_monitor.py`
3. Wait 10 seconds for data to accumulate
4. Click "Refresh Now" in sidebar

#### High CPU usage

- Reduce monitoring frequency: `--interval 5` (5 seconds)
- Limit iterations: `--iterations 1000`
- Use screen command for background execution

#### Memory issues

- Limit lookback bars: `--lookback 50` (in inference)
- Clear logs periodically: `rm logs/realtime_predictions.jsonl`

### Integration Examples

#### Telegram Notifications

```python
from telegram import Bot

async def send_signal(signal, prediction, close_price):
    bot = Bot(token="YOUR_BOT_TOKEN")
    message = f"Signal: {signal}\nPred: {prediction:.2e}\nPrice: ${close_price:.2f}"
    await bot.send_message(chat_id="YOUR_CHAT_ID", text=message)
```

#### Discord Webhook

```python
import requests

def send_signal(signal, prediction):
    webhook_url = "YOUR_WEBHOOK_URL"
    data = {
        "content": f"Signal: {signal} | Prediction: {prediction:.2e}"
    }
    requests.post(webhook_url, json=data)
```

#### Email Alerts

```python
import smtplib

def send_email_alert(signal, prediction):
    # Setup SMTP
    # Send signal notification
    pass
```

### Next Steps

1. ✅ Dashboard running locally
2. ⏭️ Deploy to cloud
3. ⏭️ Add Telegram/Discord alerts
4. ⏭️ Connect to MT5 for auto-execution
5. ⏭️ Setup 24/7 monitoring

## Support

For issues or questions:
- Check logs: `tail -f logs/realtime_predictions.jsonl`
- Monitor output: `python real_time_monitor.py`
- Dashboard errors: Check browser console (F12)
