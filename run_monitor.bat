@echo off
REM Quick start script for Aventa Trading Monitor
REM Usage: run_monitor.bat

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════╗
echo ║   AVENTA TRADING MONITOR - Quick Start ║
echo ╚════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Run: python -m venv venv
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

echo [1/3] Starting real-time monitor in background...
start "Aventa Monitor" cmd /k python real_time_monitor.py --source csv --iterations 999999

timeout /t 3 /nobreak

echo [2/3] Launching Streamlit dashboard...
timeout /t 2 /nobreak
start "" http://localhost:8501

echo [3/3] Starting Streamlit server...
streamlit run streamlit_dashboard.py

pause
