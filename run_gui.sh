#!/bin/bash
# Aventa Trading System - GUI Launcher for Linux/Mac

echo "============================================================"
echo "Aventa Trading System - Professional GUI Launcher"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Installing dependencies..."
python3 setup_gui.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "============================================================"
echo "Starting Aventa Trading System GUI..."
echo "============================================================"
echo ""

python3 gui_launcher.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to start GUI"
    exit 1
fi
