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
    print("  [6] 💾 DOWNLOAD DATA")
    print("       → Download historical data from MT5")
    print("       → Configure account, server, symbol")
    print()
    print("  [0] ❌ EXIT")
    print()

def select_symbol() -> str:
    """Let user select trading symbol"""
    print_header("📊 SELECT TRADING SYMBOL")
    
    # Common trading symbols
    symbols = [
        ('XAUUSD', 'Gold (XAUUSD)'),
        ('BTCUSD', 'Bitcoin (BTCUSD)'),
        ('EURUSD', 'EUR/USD (EURUSD)'),
        ('GBPUSD', 'GBP/USD (GBPUSD)'),
        ('USDJPY', 'USD/JPY (USDJPY)'),
        ('AUDUSD', 'AUD/USD (AUDUSD)'),
        ('NZDUSD', 'NZD/USD (NZDUSD)'),
        ('USDCAD', 'USD/CAD (USDCAD)'),
        ('USDCHF', 'USD/CHF (USDCHF)'),
        ('EUROGOLD', 'Euro Gold (EUROGOLD)'),
    ]
    
    # Try to load symbol from config
    config_path = Path('config/config.yaml')
    default_symbol = 'XAUUSD'
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
                default_symbol = cfg.get('trading', {}).get('symbol', 'XAUUSD')
        except:
            pass
    
    print("Available symbols:\n")
    for i, (code, name) in enumerate(symbols, 1):
        marker = "→" if code == default_symbol else " "
        print(f"  [{i}] {marker} {name}")
    print(f"\n  [0] Enter custom symbol")
    print(f"\n  [A] Use default ({default_symbol})")
    print()
    
    choice = input("Select symbol (press Enter for default): ").strip().upper()
    
    if choice == '' or choice == 'A':
        print(f"\n✅ Using symbol: {default_symbol}")
        return default_symbol
    
    if choice == '0':
        custom = input("\nEnter symbol (e.g., XAUUSD): ").strip().upper()
        if custom:
            print(f"\n✅ Using custom symbol: {custom}")
            return custom
        else:
            print(f"\n✅ Using default symbol: {default_symbol}")
            return default_symbol
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(symbols):
            symbol = symbols[idx][0]
            print(f"\n✅ Using symbol: {symbol}")
            return symbol
    
    print(f"\n⚠️  Invalid choice. Using default: {default_symbol}")
    return default_symbol

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
        'symbol': 'XAUUSD',
        'paper_trading': False,
        'selected_model': None
    }
    
    # Step 1: Symbol Selection
    print("[STEP 1/5] Symbol Selection\n")
    selected_symbol = select_symbol()
    status['symbol'] = selected_symbol
    print()
    
    # Check 1: Configuration
    print("[STEP 2/5] Running pre-flight checks...\n")
    config_path = Path('config/config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
            # Use selected symbol instead of config's symbol
            status['paper_trading'] = cfg.get('system', {}).get('paper_trading', False)
    
    if check_config():
        status['config'] = True
    
    # Check 2: Models and Selection
    print("[STEP 3/5] Checking ML Models...\n")
    models_info = check_models()
    if models_info:
        status['models'] = True
        status['selected_model'] = select_model(models_info)
    else:
        status['models'] = False
        print("⚠️  No models found. Continuing with TA-only mode (no ML)")
    
    # Check 3: Credentials
    print("[STEP 4/5] Validating Credentials...\n")
    creds_valid = check_credentials()
    status['credentials'] = creds_valid
    
    # Display Status Summary
    print("[STEP 5/5] Pre-Flight Status\n")
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

def select_training_data():
    """Let user select symbol and data file for training"""
    print_header("📂 SELECT TRAINING DATA")
    
    data_dir = Path('data')
    if not data_dir.exists():
        print("⚠️  Data directory not found. Creating...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print("   Empty data directory created.")
        print("   Please download data files using menu [2] or download_data.py")
        return None, None
    
    # Find all CSV files
    csv_files = sorted(data_dir.glob('*.csv'))
    
    if not csv_files:
        print(f"⚠️  No CSV files found in {data_dir}")
        print("   Please download data files first using download_data.py")
        return None, None
    
    print(f"\nFound {len(csv_files)} data file(s):\n")
    for i, file in enumerate(csv_files, 1):
        size_kb = file.stat().st_size / 1024
        print(f"  [{i}] {file.name} ({size_kb:.1f} KB)")
    
    print(f"\n  [0] Use latest/largest file (auto-select)")
    print()
    
    choice = input("Select data file (press Enter for auto): ").strip()
    
    # Auto-select largest file
    if choice == '' or choice == '0':
        selected_file = max(csv_files, key=lambda p: p.stat().st_size)
        print(f"\n✅ Using: {selected_file.name}")
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(csv_files):
            selected_file = csv_files[idx]
            print(f"\n✅ Using: {selected_file.name}")
        else:
            print("❌ Invalid selection. Using largest file...")
            selected_file = max(csv_files, key=lambda p: p.stat().st_size)
            print(f"✅ Using: {selected_file.name}")
    else:
        print("❌ Invalid input. Using largest file...")
        selected_file = max(csv_files, key=lambda p: p.stat().st_size)
        print(f"✅ Using: {selected_file.name}")
    
    # Extract symbol from filename (e.g., GOLD_ls_M1_59days.csv -> GOLD_ls)
    symbol = selected_file.stem.split('_M1')[0].upper()
    
    print(f"   Symbol: {symbol}")
    print(f"   Path: {selected_file}\n")
    
    return str(selected_file), symbol

def train_models():
    """Train ML models with symbol and data selection"""
    print_header("🧠 TRAINING ML MODELS")
    
    # Step 1: Select training data and symbol
    print("[STEP 1/3] Data Selection\n")
    data_file, symbol = select_training_data()
    
    if data_file is None:
        print("❌ No data file selected. Training cancelled.")
        input("Press Enter to return to menu...")
        return False
    
    print()
    
    # Step 2: Select model type
    print("[STEP 2/3] Model Selection\n")
    print("Available models:\n")
    print("  [1] Random Forest (sklearn) - Faster, baseline")
    print("  [2] LSTM (PyTorch) - More advanced, slower")
    print("  [3] Both - Train both models\n")
    
    model_choice = input("Select model type (1-3, default: 1): ").strip()
    
    if model_choice == '2':
        model_type = 'lstm'
        model_name = "LSTM"
    elif model_choice == '3':
        model_type = 'both'
        model_name = "Both Models"
    else:
        model_type = 'sklearn'
        model_name = "Random Forest"
    
    print(f"\n✅ Selected: {model_name}\n")
    
    # Step 3: Confirm and launch
    print("[STEP 3/3] Training Configuration\n")
    print(f"  Data File: {Path(data_file).name}")
    print(f"  Symbol: {symbol}")
    print(f"  Model Type: {model_name}")
    print()
    
    confirm = input("Start training? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Training cancelled.")
        input("Press Enter to return to menu...")
        return False
    
    print("\n[LAUNCH] Starting train_models.py...")
    print("⏳ This may take several minutes...\n")
    print("=" * 80)
    
    try:
        cmd = [
            sys.executable, 'train_models.py',
            '--data-dir', 'data',
            '--output-dir', 'models'
        ]
        
        # Add model type if not both
        if model_type != 'both':
            cmd.extend(['--model', model_type])
        
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n[STOP] Training stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n✅ Training completed")
    input("Press Enter to return to menu...")

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

def download_data_from_mt5():
    """Download historical data from MT5"""
    print_header("💾 DOWNLOAD DATA FROM MT5")
    
    print("[STEP 1/5] MT5 Path\n")
    mt5_path = os.getenv('MT5_PATH')
    if mt5_path:
        print(f"Current MT5 Path: {mt5_path}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            mt5_path = input("Enter MT5 installation path: ").strip()
    else:
        print("Common MT5 paths:")
        print("  1. C:\\Program Files\\MetaTrader 5 (Default)")
        print("  2. C:\\Program Files (x86)\\MetaTrader 5")
        print("  3. Custom path...")
        choice = input("Select (1-3): ").strip()
        if choice == '1':
            mt5_path = "C:\\Program Files\\MetaTrader 5"
        elif choice == '2':
            mt5_path = "C:\\Program Files (x86)\\MetaTrader 5"
        else:
            mt5_path = input("Enter MT5 path: ").strip()
    
    if not mt5_path:
        print("❌ MT5 path is required")
        input("Press Enter to return to menu...")
        return False
    
    print(f"✅ MT5 Path: {mt5_path}\n")
    
    # Step 2: Account Number
    print("[STEP 2/5] Account Number\n")
    account = os.getenv('MT5_ACCOUNT')
    if account:
        print(f"Current Account: {account}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            account = input("Enter MT5 Account Number: ").strip()
    else:
        account = input("Enter MT5 Account Number: ").strip()
    
    if not account or not account.isdigit():
        print("❌ Valid account number required")
        input("Press Enter to return to menu...")
        return False
    
    print(f"✅ Account: {account}\n")
    
    # Step 3: Password
    print("[STEP 3/5] Password\n")
    password = os.getenv('MT5_PASSWORD')
    if password:
        print(f"Current Password: {'*' * len(password)}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            password = input("Enter MT5 Password: ").strip()
    else:
        password = input("Enter MT5 Password: ").strip()
    
    if not password:
        print("❌ Password is required")
        input("Press Enter to return to menu...")
        return False
    
    print(f"✅ Password: {'*' * len(password)}\n")
    
    # Step 4: Server
    print("[STEP 4/5] Server\n")
    server = os.getenv('MT5_SERVER')
    if server:
        print(f"Current Server: {server}")
        change = input("Change? (y/n): ").strip().lower()
        if change == 'y':
            print("\nCommon servers:")
            print("  1. VantageInternational-Demo")
            print("  2. VantageInternational-Live")
            print("  3. Other...")
            choice = input("Select (1-3): ").strip()
            if choice == '1':
                server = "VantageInternational-Demo"
            elif choice == '2':
                server = "VantageInternational-Live"
            else:
                server = input("Enter server name: ").strip()
    else:
        print("Common servers:")
        print("  1. VantageInternational-Demo")
        print("  2. VantageInternational-Live")
        print("  3. Other...")
        choice = input("Select (1-3): ").strip()
        if choice == '1':
            server = "VantageInternational-Demo"
        elif choice == '2':
            server = "VantageInternational-Live"
        else:
            server = input("Enter server name: ").strip()
    
    if not server:
        print("❌ Server is required")
        input("Press Enter to return to menu...")
        return False
    
    print(f"✅ Server: {server}\n")
    
    # Step 5: Symbol
    print("[STEP 5/5] Trading Symbol\n")
    symbols = [
        ('XAUUSD', 'Gold (XAUUSD)'),
        ('BTCUSD', 'Bitcoin (BTCUSD)'),
        ('EURUSD', 'EUR/USD (EURUSD)'),
        ('GBPUSD', 'GBP/USD (GBPUSD)'),
        ('USDJPY', 'USD/JPY (USDJPY)'),
        ('GOLD.ls', 'Gold Spot (GOLD.ls)'),
    ]
    
    print("Available symbols:\n")
    for i, (code, name) in enumerate(symbols, 1):
        print(f"  [{i}] {name}")
    print(f"  [0] Enter custom symbol")
    print()
    
    choice = input("Select symbol: ").strip()
    
    if choice == '0':
        symbol = input("Enter symbol (e.g., XAUUSD): ").strip().upper()
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(symbols):
            symbol = symbols[idx][0]
        else:
            print("Invalid choice. Using XAUUSD")
            symbol = 'XAUUSD'
    else:
        symbol = 'XAUUSD'
    
    if not symbol:
        print("❌ Symbol is required")
        input("Press Enter to return to menu...")
        return False
    
    print(f"✅ Symbol: {symbol}\n")
    
    # Summary
    print_header("📊 DOWNLOAD CONFIGURATION")
    print("[CONFIGURATION SUMMARY]\n")
    print(f"  MT5 Path:    {mt5_path}")
    print(f"  Account:     {account}")
    print(f"  Server:      {server}")
    print(f"  Symbol:      {symbol}")
    print(f"  Output Dir:  data/")
    print()
    
    confirm = input("Start downloading? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Download cancelled")
        input("Press Enter to return to menu...")
        return False
    
    print("\n[LAUNCH] Starting download_data.py...")
    print("⏳ This may take a few minutes...\n")
    print("=" * 80)
    
    try:
        cmd = [
            sys.executable, 'download_data.py',
            '--account', account,
            '--password', password,
            '--server', server,
            '--symbol', symbol,
            '--mt5-path', mt5_path,
            '--output-dir', 'data'
        ]
        
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n\n[STOP] Download stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    print("\n✅ Download completed")
    input("Press Enter to return to menu...")
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
        
        choice = input("Enter your choice (0-6): ").strip()
        
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
        elif choice == '6':
            download_data_from_mt5()
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
