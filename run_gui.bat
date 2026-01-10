@echo off
REM Aventa Trading System - GUI Launcher for Windows

echo ============================================================
echo Aventa Trading System - Professional GUI Launcher
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Installing dependencies...
call python setup_gui.py

if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Starting Aventa Trading System GUI...
echo ============================================================
echo.

python gui_launcher.py

if %errorlevel% neq 0 (
    echo Error: Failed to start GUI
    pause
    exit /b 1
)
