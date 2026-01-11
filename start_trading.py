#!/usr/bin/env python3
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
    required_env = ['MT5_ACCOUNT', 'MT5_PASSWORD', 'MT5_SERVER']
    missing = [var for var in required_env if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("\n📋 Please set these before running:")
        print("  $env:MT5_ACCOUNT = 'your_account'")
        print("  $env:MT5_PASSWORD = 'your_password'")
        print("  $env:MT5_SERVER = 'your_server'")
        
        # Try to get from config files
        config_path = Path('config/config.yaml')
        if config_path.exists():
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
                account = cfg.get('trading', {}).get('account')
                server = cfg.get('trading', {}).get('server')
                if account and server:
                    print(f"\n✅ Found in config: Account={account}, Server={server}")
                    print("⏳ Password still needed in environment variable")
                    return False
        
        return False
    
    print("✅ Credentials validated\n")
    return True

def check_models():
    """Check if trained models exist"""
    print("[CHECK] Checking for trained models...")
    
    model_dir = Path('models')
    if not model_dir.exists():
        print(f"❌ Models directory not found: {model_dir}")
        return False
    
    model_files = list(model_dir.glob('*.pkl')) + list(model_dir.glob('*.pt'))
    
    if not model_files:
        print(f"⚠️  No trained models found in {model_dir}")
        print("❓ Run: python train_models.py")
        return False
    
    print(f"✅ Found {len(model_files)} trained model(s)")
    for f in model_files[:3]:  # Show first 3
        print(f"   - {f.name}")
    if len(model_files) > 3:
        print(f"   ... and {len(model_files)-3} more")
    print()
    return True

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

def start_trading_bot():
    """Start the auto trading bot"""
    print_header("🚀 STARTING AUTO TRADING BOT")
    
    # Validation
    print("[VALIDATION] Running pre-flight checks...\n")
    
    if not check_config():
        print("❌ Configuration check failed")
        return False
    
    if not check_models():
        print("⚠️  No models found. Continuing with TA-only mode (no ML)")
    
    if not check_credentials():
        print("❌ Credentials validation failed")
        return False
    
    # Show bot configuration
    config_path = Path('config/config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
            symbol = cfg.get('trading', {}).get('symbol', 'BTCUSD')
            paper = cfg.get('system', {}).get('paper_trading', False)
    
    print("[BOT CONFIG]")
    print(f"  Symbol: {symbol}")
    print(f"  Mode: {'📃 PAPER TRADING' if paper else '💰 LIVE TRADING'}")
    print()
    
    if not paper:
        print("⚠️  WARNING: LIVE TRADING MODE IS ENABLED")
        confirm = input("Type 'LIVE' to confirm: ")
        if confirm != 'LIVE':
            print("❌ Cancelled")
            return False
    
    # Start bot
    print("\n[LAUNCH] Starting auto_trading.py...")
    print("=" * 80)
    
    try:
        subprocess.run(
            [sys.executable, 'auto_trading.py'],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n[STOP] Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True

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
    print_header("🤖 HFT TRADING SYSTEM LAUNCHER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Symbol: BTCUSD | Live Trading: Enabled" if not Path('config/config.yaml').exists() 
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
