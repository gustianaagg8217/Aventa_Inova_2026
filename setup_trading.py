#!/usr/bin/env python3
"""
Setup script for MT5 credentials and initial configuration.
Run once at first time setup.
"""

import os
import sys
from pathlib import Path
from getpass import getpass
import yaml

def setup_env_variables():
    """Setup MT5 credentials"""
    print("\n" + "="*80)
    print("🔐 MT5 CREDENTIALS SETUP")
    print("="*80)
    print("\nEnter your MetaTrader 5 account details:")
    print("(These will be saved to Windows Environment Variables)")
    
    account = input("\n📊 MT5 Account Number (e.g., 11260163): ").strip()
    if not account.isdigit():
        print("❌ Invalid account number")
        return False
    
    password = getpass("🔑 MT5 Password (will be hidden): ")
    if not password:
        print("❌ Password cannot be empty")
        return False
    
    server = input("🌐 MT5 Server (e.g., VantageInternational-Demo): ").strip()
    if not server:
        print("❌ Server cannot be empty")
        return False
    
    # Set environment variables for current session
    os.environ['MT5_ACCOUNT'] = account
    os.environ['MT5_PASSWORD'] = password
    os.environ['MT5_SERVER'] = server
    
    print("\n✅ Credentials set for this session")
    print("\nTo make permanent (Windows only):")
    print("  1. Press Win + X")
    print("  2. Select 'Environment Variables'")
    print("  3. Click 'Environment Variables' button")
    print("  4. Add new User variables:")
    print(f"     - MT5_ACCOUNT = {account}")
    print(f"     - MT5_PASSWORD = {password}")
    print(f"     - MT5_SERVER = {server}")
    
    return True

def verify_config_files():
    """Verify or create configuration files"""
    print("\n" + "="*80)
    print("⚙️  CONFIGURATION FILES")
    print("="*80)
    
    config_dir = Path('config')
    
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
        print(f"✅ Created {config_dir} directory")
    
    # Check main config
    config_file = config_dir / 'config.yaml'
    if config_file.exists():
        print(f"✅ {config_file} exists")
    else:
        print(f"⚠️  {config_file} not found, creating...")
    
    # Check trading config
    trading_config_file = config_dir / 'trading_config.yaml'
    if trading_config_file.exists():
        print(f"✅ {trading_config_file} exists")
    else:
        print(f"⚠️  {trading_config_file} not found, creating...")
    
    return True

def check_models():
    """Check if models directory exists"""
    print("\n" + "="*80)
    print("🧠 ML MODELS")
    print("="*80)
    
    models_dir = Path('models')
    
    if not models_dir.exists():
        models_dir.mkdir(parents=True)
        print(f"✅ Created {models_dir} directory")
    
    model_files = list(models_dir.glob('*.pkl')) + list(models_dir.glob('*.pt'))
    
    if model_files:
        print(f"✅ Found {len(model_files)} trained model(s)")
    else:
        print(f"⚠️  No trained models found")
        print("\n   Run this to train models:")
        print("   → python train_models.py")
        print("\n   Training takes 5-10 minutes")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*80)
    print("📦 DEPENDENCIES")
    print("="*80)
    
    required = [
        'pandas',
        'numpy',
        'MetaTrader5',
        'torch',
        'scikit-learn',
        'pyyaml'
    ]
    
    missing = []
    for pkg in required:
        try:
            __import__(pkg if pkg != 'MetaTrader5' else 'mt5')
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg}")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\n   Install with:")
        print(f"   → pip install {' '.join(missing)}")
        return False
    
    return True

def summary():
    """Show setup summary"""
    print("\n" + "="*80)
    print("✅ SETUP COMPLETE")
    print("="*80)
    
    print("\n📋 Next Steps:\n")
    print("  1. Train ML Models (first time only):")
    print("     → python train_models.py")
    print("     → Takes 5-10 minutes\n")
    print("  2. Start Trading:")
    print("     → python start_trading.py")
    print("     → Select [1] for Auto Trading Bot\n")
    print("  3. Monitor Dashboard (optional, in separate window):")
    print("     → python start_trading.py")
    print("     → Select [2] for Dashboard\n")
    
    print("="*80)
    print("🎯 Full documentation: AUTO_TRADING_SETUP.md")
    print("="*80 + "\n")

def main():
    """Main setup flow"""
    print("\n" + "="*80)
    print("🚀 HFT TRADING SYSTEM - INITIAL SETUP")
    print("="*80)
    
    # Check dependencies
    if not check_dependencies():
        print("\n⚠️  Please install missing dependencies first")
        return False
    
    # Setup credentials
    if not setup_env_variables():
        print("\n❌ Setup cancelled")
        return False
    
    # Verify configs
    verify_config_files()
    
    # Check models
    check_models()
    
    # Summary
    summary()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
