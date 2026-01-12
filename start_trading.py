#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 UNIFIED TRADING BOT LAUNCHER
================================
Single entry point for the complete HFT trading system.
Handles model training, setup, and bot execution.

Usage:
    python start_trading.py
    
    Then choose:
    1 = Auto Trading Bot (full ML + TA)
    2 = Monitor Dashboard
    3 = Check Signals
    4 = Train Models
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
import yaml
import json

def print_header(title):
    """Print styled header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def check_credentials():
    """Check and validate MT5 credentials"""
    print("[CHECK] Validating MT5 credentials...")
    
    # Check environment variables
    required_env = ['MT5_ACCOUNT', 'MT5_PASSWORD', 'MT5_SERVER', 'MT5_PATH']
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("\n📋 Please set these before running:")
        print("  $env:MT5_ACCOUNT = 'your_account'")
        print("  $env:MT5_PASSWORD = 'your_password'")
        print("  $env:MT5_SERVER = 'your_server'")
        print("  $env:MT5_PATH = 'C:\\Program Files\\MetaTrader 5'")
        
        # Try to get from config files
        config_path = Path('config/config.yaml')
        if config_path.exists():
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
                account = cfg.get('trading', {}).get('account')
                server = cfg.get('trading', {}).get('server')
                if account and server:
                    print(f"\n✅ Found in config: Account={account}, Server={server}")
                    print("⏳ Password and Path still needed in environment variable")
                    return False
        
        return False
    
    print("✅ Credentials validated\n")
    return True

def check_models():
    """Check if trained models exist and return list"""
    print("[CHECK] Scanning for trained models...")
    
    model_dir = Path('models')
    if not model_dir.exists():
        print(f"❌ Models directory not found: {model_dir}")
        return []
    
    # Find all model files (.pkl for sklearn, .pt for LSTM)
    pkl_files = list(model_dir.glob('*.pkl'))
    pt_files = list(model_dir.glob('*.pt'))
    model_files = pkl_files + pt_files
    
    if not model_files:
        print(f"⚠️  No trained models found in {model_dir}")
        print("   Run: python train_models.py")
        return []
    
    print(f"✅ Found {len(model_files)} trained model(s):\n")
    
    models_info = []
    for i, f in enumerate(sorted(model_files), 1):
        model_type = "LSTM" if f.suffix == '.pt' else "Random Forest"
        size_mb = f.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"   [{i}] {f.name} ({model_type}, {size_mb:.2f} MB, {mtime})")
        models_info.append({
            'path': f,
            'name': f.stem,
            'type': model_type,
            'size': f.stat().st_size,
            'mtime': f.stat().st_mtime
        })
    
    print()
    return models_info

def select_model(models_info: list) -> Optional[str]:
    """Let user select a model or auto-select latest"""
    if not models_info:
        return None
    
    print("\n[MODEL SELECTION]\n")
    print(f"  [A] Use LATEST model (default)")
    print(f"  [1-{len(models_info)}] Select specific model")
    print()
    
    choice = input("Select model (press Enter for latest): ").strip().upper()
    
    if choice == '' or choice == 'A':
        # Auto-select latest by modification time
        latest = max(models_info, key=lambda x: x['mtime'])
        print(f"\n✅ Using latest model: {latest['name']}")
        return str(latest['path'])
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(models_info):
            selected = models_info[idx]
            print(f"\n✅ Using selected model: {selected['name']}")
            return str(selected['path'])
    
    print("❌ Invalid selection, using latest model")
    latest = max(models_info, key=lambda x: x['mtime'])
    return str(latest['path'])

def check_config():
    """Verify configuration files exist and are valid"""
    print("[CHECK] Validating configuration files...")
    
    config_files = [
        Path('config/config.yaml'),
        Path('config/trading_config.yaml'),
        Path('config/strategy_params.yaml')
    ]
    
    missing = []
    for cf in config_files:
        if not cf.exists():
            missing.append(cf)
        else:
            try:
                with open(cf) as f:
                    yaml.safe_load(f)
                    print(f"✅ {cf}")
            except Exception as e:
                print(f"❌ {cf}: {e}")
                return False
    
    if missing:
        print(f"⚠️  Missing: {', '.join(str(f) for f in missing)}")
        print("   These will be created with defaults if needed")
    
    print()
    return True

def show_menu():
    """Show main menu"""
    print_header("🤖 TRADING SYSTEM MENU")
    
    print("Select an option:\n")
    print("  [1] 🚀 START AUTO TRADING BOT")
    print("       → Runs full ML+TA trading with all features")
    print("       → Monitors positions and sends Telegram alerts")
    print()
    print("  [2] 📊 MONITOR DASHBOARD")
    print("       → Real-time trading metrics & performance")
    print("       → Run this in parallel window")
    print()
    print("  [3] 📡 CHECK SIGNALS (Real-Time Monitor)")
    print("       → View live ML predictions")
    print("       → Technical analysis indicators")
    print()
    print("  [4] 🧠 TRAIN NEW MODELS")
    print("       → Re-train ML models with latest data")
    print("       → Update strategy parameters")
    print()
    print("  [5] 📈 RUN BACKTEST")
    print("       → Test strategy with historical data")
    print("       → Analyze performance metrics")
    print()
    print("  [0] ❌ EXIT")
    print()

def ask_credentials():
    """Ask user for MT5 credentials interactively"""
    print_header("📝 MT5 CREDENTIALS INPUT")
    
    print("Enter your MT5 account information:\n")
    
    # Check if already set
    account = os.getenv('MT5_ACCOUNT')
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    path = os.getenv('MT5_PATH')
    
    # Account
    if account:
        print(f"Current Account: {account}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            account = input("Enter MT5 Account Number: ").strip()
        print()
    else:
        account = input("Enter MT5 Account Number: ").strip()
        print()
    
    # Password
    if password:
        print(f"Current Password: {'*' * len(password)}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            password = input("Enter MT5 Password: ").strip()
        print()
    else:
        password = input("Enter MT5 Password: ").strip()
        print()
    
    # Server
    if server:
        print(f"Current Server: {server}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            print("\nCommon servers:")
            print("  1. VantageInternational-Demo (Demo)")
            print("  2. VantageInternational-Live (Live)")
            print("  3. Other...")
            choice = input("Select (1-3) or enter custom: ").strip()
            if choice == '1':
                server = "VantageInternational-Demo"
            elif choice == '2':
                server = "VantageInternational-Live"
            elif choice == '3':
                server = input("Enter server name: ").strip()
            else:
                server = choice if choice else server
        print()
    else:
        print("\nCommon servers:")
        print("  1. VantageInternational-Demo (Demo)")
        print("  2. VantageInternational-Live (Live)")
        print("  3. Other...")
        choice = input("Select (1-3) or enter custom: ").strip()
        if choice == '1':
            server = "VantageInternational-Demo"
        elif choice == '2':
            server = "VantageInternational-Live"
        elif choice == '3':
            server = input("Enter server name: ").strip()
        else:
            server = choice if choice else "VantageInternational-Demo"
        print()
    
    # MT5 Path
    if path:
        print(f"Current MT5 Path: {path}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            print("\nCommon MT5 paths:")
            print("  1. C:\\Program Files\\MetaTrader 5 (Default)")
            print("  2. C:\\Program Files (x86)\\MetaTrader 5")
            print("  3. Other (Custom path)...")
            choice = input("Select (1-3) or enter custom path: ").strip()
            if choice == '1':
                path = "C:\\Program Files\\MetaTrader 5"
            elif choice == '2':
                path = "C:\\Program Files (x86)\\MetaTrader 5"
            elif choice == '3':
                path = input("Enter MT5 installation path: ").strip()
            else:
                path = choice if choice else path
        print()
    else:
        print("\nCommon MT5 paths:")
        print("  1. C:\\Program Files\\MetaTrader 5 (Default)")
        print("  2. C:\\Program Files (x86)\\MetaTrader 5")
        print("  3. Other (Custom path)...")
        choice = input("Select (1-3) or enter custom path: ").strip()
        if choice == '1':
            path = "C:\\Program Files\\MetaTrader 5"
        elif choice == '2':
            path = "C:\\Program Files (x86)\\MetaTrader 5"
        elif choice == '3':
            path = input("Enter MT5 installation path: ").strip()
        else:
            path = choice if choice else "C:\\Program Files\\MetaTrader 5"
        print()
    
    # Validate inputs
    if not account or not password or not server or not path:
        print("❌ Missing required credentials!")
        return False
    
    # Set environment variables
    os.environ['MT5_ACCOUNT'] = account
    os.environ['MT5_PASSWORD'] = password
    os.environ['MT5_SERVER'] = server
    os.environ['MT5_PATH'] = path
    
    print("✅ Credentials set successfully!")
    print(f"   Account: {account}")
    print(f"   Server: {server}")
    print(f"   Path: {path}\n")
    return True

def start_trading_bot():
    """Start the auto trading bot"""
    print_header("🚀 STARTING AUTO TRADING BOT")
    
    # Ask for credentials if not already set
    if not all([os.getenv('MT5_ACCOUNT'), os.getenv('MT5_PASSWORD'), os.getenv('MT5_SERVER'), os.getenv('MT5_PATH')]):
        if not ask_credentials():
            print("❌ Cannot proceed without credentials")
            input("Press Enter to return to menu...")
            return False
    
    # Status tracking
    status = {
        'config': False,
        'models': None,
        'credentials': False,
        'symbol': 'BTCUSD',
        'paper_trading': False,
        'selected_model': None
    }
    
    # Check 1: Configuration
    print("[VALIDATION] Running pre-flight checks...\n")
    config_path = Path('config/config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
            status['symbol'] = cfg.get('trading', {}).get('symbol', 'BTCUSD')
            status['paper_trading'] = cfg.get('system', {}).get('paper_trading', False)
    
    if check_config():
        status['config'] = True
    
    # Check 2: Models and Selection
    models_info = check_models()
    if models_info:
        status['models'] = True
        status['selected_model'] = select_model(models_info)
    else:
        status['models'] = False
        print("⚠️  No models found. Continuing with TA-only mode (no ML)")
    
    # Check 3: Credentials
    creds_valid = check_credentials()
    status['credentials'] = creds_valid
    
    # Display Status Summary
    print_header("✅ PRE-FLIGHT STATUS")
    print("[CHECKS]\n")
    print(f"  Config Files:      {'✅ READY' if status['config'] else '❌ FAILED'}")
    print(f"  ML Models:         {'✅ READY' if status['models'] else '⚠️  NOT FOUND (TA-Only)'}")
    if status['selected_model']:
        print(f"  Selected Model:    {Path(status['selected_model']).name}")
    print(f"  MT5 Credentials:   {'✅ READY' if status['credentials'] else '❌ FAILED'}")
    print()
    
    # Show Bot Configuration
    print("[BOT CONFIGURATION]\n")
    print(f"  Symbol:            {status['symbol']}")
    print(f"  Mode:              {'📃 PAPER TRADING' if status['paper_trading'] else '💰 LIVE TRADING'}")
    if status['selected_model']:
        print(f"  ML Model:          {Path(status['selected_model']).name}")
    else:
        print(f"  ML Model:          None (TA Only)")
    print(f"  MT5 Path:          {os.getenv('MT5_PATH', 'Not set')}")
    print()
    
    # Check if ready to proceed
    if not status['config']:
        print("⚠️  CANNOT START: Configuration check failed")
        print("\nFix the issues above and try again.\n")
        input("Press Enter to return to menu...")
        return False
    
    if not status['credentials']:
        print("⚠️  CANNOT START: MT5 Credentials missing")
        print("\nPlease set environment variables:")
        print("  $env:MT5_ACCOUNT = 'your_account'")
        print("  $env:MT5_PASSWORD = 'your_password'")
        print("  $env:MT5_SERVER = 'your_server'\n")
        input("Press Enter to return to menu...")
        return False
    
    # Confirm if LIVE trading
    if not status['paper_trading']:
        print("⚠️  WARNING: LIVE TRADING MODE IS ENABLED")
        print("\n💰 You are about to trade with REAL MONEY!")
        confirm = input("\nType 'LIVE' to confirm (or press Enter to cancel): ")
        if confirm != 'LIVE':
            print("\n❌ Trading cancelled. Returning to menu...\n")
            input("Press Enter to continue...")
            return False
    
    # All checks passed - Start trading
    print("\n" + "="*80)
    print("[LAUNCH] Starting auto_trading.py...")
    print("="*80 + "\n")
    
    try:
        subprocess.run(
            [sys.executable, 'auto_trading.py'],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*80)
    input("Press Enter to return to menu...")
    return False

def start_dashboard():
    """Start the dashboard"""
    print_header("📊 STARTING DASHBOARD")
    
    print("[LAUNCH] Starting dashboard.py...")
    print("=" * 80)
    
    try:
        subprocess.run(
            [sys.executable, 'dashboard.py', '--interval', '2'],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

def start_monitor():
    """Start real-time monitor"""
    print_header("📡 STARTING REAL-TIME MONITOR")
    
    print("[LAUNCH] Starting real_time_monitor.py...")
    print("=" * 80)
    
    try:
        # Use yfinance if MT5 not configured, else use MT5
        source = 'yfinance'
        if os.getenv('MT5_ACCOUNT') and os.getenv('MT5_PASSWORD'):
            source = 'mt5'
            args = [
                sys.executable, 'real_time_monitor.py',
                '--source', source,
                '--login', os.getenv('MT5_ACCOUNT'),
                '--password', os.getenv('MT5_PASSWORD'),
                '--server', os.getenv('MT5_SERVER', 'VantageInternational-Demo'),
                '--interval', '5'
            ]
        else:
            args = [
                sys.executable, 'real_time_monitor.py',
                '--source', source,
                '--interval', '5'
            ]
        
        subprocess.run(args, check=False)
    except KeyboardInterrupt:
        print("\n\n[STOP] Monitor stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

def train_models():
    """Train ML models"""
    print_header("🧠 TRAINING ML MODELS")
    
    print("[LAUNCH] Starting train_models.py...")
    print("⏳ This may take several minutes...\n")
    print("=" * 80)
    
    try:
        subprocess.run(
            [sys.executable, 'train_models.py'],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] Training stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n✅ Training completed")
    return True

def run_backtest():
    """Run backtest"""
    print_header("📈 RUNNING BACKTEST")
    
    print("[LAUNCH] Starting optimized_backtest.py...")
    print("=" * 80)
    
    try:
        subprocess.run(
            [sys.executable, 'optimized_backtest.py'],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] Backtest stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

def main():
    """Main launcher loop"""
    # Fix encoding for Windows console with emojis
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print_header("🤖 HFT TRADING SYSTEM LAUNCHER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Symbol: XAUUSD | Live Trading: Enabled" if not Path('config/config.yaml').exists() 
          else "Symbol: Check config | Mode: Check config")
    
    while True:
        show_menu()
        
        choice = input("Enter your choice (0-5): ").strip()
        
        if choice == '1':
            start_trading_bot()
        elif choice == '2':
            start_dashboard()
        elif choice == '3':
            start_monitor()
        elif choice == '4':
            train_models()
        elif choice == '5':
            run_backtest()
        elif choice == '0':
            print("\n✅ Exiting... Goodbye!")
            break
        else:
            print("❌ Invalid option. Please try again.")
        
        # Ask to continue
        if choice != '0':
            input("\nPress Enter to return to menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✅ Launcher closed")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
