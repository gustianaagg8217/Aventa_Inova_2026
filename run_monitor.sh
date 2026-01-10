#!/bin/bash
# Quick start script for Aventa Trading Monitor
# Usage: ./run_monitor.sh

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   AVENTA TRADING MONITOR - Quick Start ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo "[1/3] Starting real-time monitor in background..."
python real_time_monitor.py --source csv --iterations 999999 &
MONITOR_PID=$!

sleep 3

echo "[2/3] Opening browser..."
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
else
    echo "Open your browser to: http://localhost:8501"
fi

echo "[3/3] Starting Streamlit server..."
sleep 2
streamlit run streamlit_dashboard.py

# Cleanup on exit
trap "kill $MONITOR_PID" EXIT
