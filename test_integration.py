#!/usr/bin/env python3
"""
Integration Test Script for Signal Service
Verifies all components are properly integrated and ready for use.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("\n" + "="*60)
    print("🧪 INTEGRATION TEST - Signal Service")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Import main GUI launcher
    tests_total += 1
    print("\n[1/5] Testing GUI Launcher import...")
    try:
        from gui_launcher import MainWindow, TradingConfig
        print("    ✅ MainWindow imported successfully")
        print("    ✅ TradingConfig imported successfully")
        tests_passed += 1
    except ImportError as e:
        print(f"    ❌ Failed to import gui_launcher: {e}")
    
    # Test 2: Import SignalServiceTab
    tests_total += 1
    print("\n[2/5] Testing SignalServiceTab import...")
    try:
        from signal_service_tab import SignalServiceTab
        print("    ✅ SignalServiceTab imported successfully")
        tests_passed += 1
    except ImportError as e:
        print(f"    ❌ Failed to import signal_service_tab: {e}")
    
    # Test 3: Import SignalBroadcaster
    tests_total += 1
    print("\n[3/5] Testing SignalBroadcaster import...")
    try:
        from signal_service import SignalBroadcaster
        print("    ✅ SignalBroadcaster imported successfully")
        tests_passed += 1
    except ImportError as e:
        print(f"    ❌ Failed to import signal_service: {e}")
    
    # Test 4: Check TradingConfig has signal service fields
    tests_total += 1
    print("\n[4/5] Testing TradingConfig signal service fields...")
    try:
        from gui_launcher import TradingConfig
        config = TradingConfig()
        
        required_fields = [
            'signal_service_enabled',
            'signal_bot_token',
            'signal_chat_ids',
            'signal_symbols',
            'signal_tp_percent',
            'signal_sl_percent',
            'signal_min_confidence',
            'signal_filter_type',
            'signal_template',
            'signal_history_file',
            'max_signals_per_hour'
        ]
        
        missing_fields = [f for f in required_fields if not hasattr(config, f)]
        
        if missing_fields:
            print(f"    ❌ Missing fields: {missing_fields}")
        else:
            print("    ✅ All signal service fields present in TradingConfig:")
            for field in required_fields:
                value = getattr(config, field)
                print(f"       - {field}: {value}")
            tests_passed += 1
    
    except Exception as e:
        print(f"    ❌ Error checking config fields: {e}")
    
    # Test 5: Check SignalServiceTab has get_config method
    tests_total += 1
    print("\n[5/5] Testing SignalServiceTab.get_config() method...")
    try:
        from signal_service_tab import SignalServiceTab
        from gui_launcher import TradingConfig
        
        config = TradingConfig()
        # Note: We can't instantiate SignalServiceTab without PyQt6 running
        # but we can check if method exists in the class
        if hasattr(SignalServiceTab, 'get_config'):
            print("    ✅ SignalServiceTab.get_config() method exists")
            tests_passed += 1
        else:
            print("    ❌ SignalServiceTab.get_config() method not found")
    
    except Exception as e:
        print(f"    ❌ Error checking get_config method: {e}")
    
    # Summary
    print("\n" + "="*60)
    print(f"📊 INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print("="*60)
    
    if tests_passed == tests_total:
        print("\n✅ ALL TESTS PASSED - Integration Complete!")
        print("\nReady for user testing via:")
        print("  > python gui_launcher.py")
        return 0
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed - Check errors above")
        return 1

if __name__ == "__main__":
    sys.exit(test_imports())
