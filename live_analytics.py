import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import os

class LivePerformanceTracker:
    """Track live performance metrics"""
    
    def __init__(self):
        self.start_balance = 0
        self.peak_balance = 0
        self.current_drawdown = 0
        self.max_drawdown = 0
        self.trade_count = 0
        self.session_start = datetime.now()
    
    def initialize(self, account_info):
        """Initialize tracker with account info"""
        self.start_balance = account_info.balance
        self.peak_balance = account_info.balance
        print(f"📊 Performance tracker initialized")
        print(f"   Starting Balance: ${self.start_balance:.2f}")
    
    def update(self, account_info):
        """Update performance metrics"""
        current_balance = account_info.balance
        
        # Update peak
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Calculate drawdown
        self.current_drawdown = ((self.peak_balance - current_balance) / self.peak_balance * 100) if self.peak_balance > 0 else 0
        
        # Update max drawdown
        if self.current_drawdown > self.max_drawdown:
            self.max_drawdown = self.current_drawdown
    
    def get_session_stats(self, account_info):
        """Get current session statistics"""
        current_balance = account_info.balance
        session_pnl = current_balance - self.start_balance
        session_pnl_pct = (session_pnl / self.start_balance * 100) if self.start_balance > 0 else 0
        
        session_duration = datetime.now() - self.session_start
        hours = session_duration.total_seconds() / 3600
        
        return {
            'start_balance': self.start_balance,
            'current_balance': current_balance,
            'peak_balance': self.peak_balance,
            'session_pnl': session_pnl,
            'session_pnl_pct': session_pnl_pct,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'session_duration_hours': hours,
        }
    
    def print_live_stats(self, account_info):
        """Print live statistics"""
        stats = self.get_session_stats(account_info)
        
        print("\n" + "="*60)
        print("📊 LIVE PERFORMANCE")
        print("="*60)
        
        pnl_emoji = "📈" if stats['session_pnl'] > 0 else "📉" if stats['session_pnl'] < 0 else "➖"
        
        print(f"Start Balance:     ${stats['start_balance']:.2f}")
        print(f"Current Balance:   ${stats['current_balance']:.2f}")
        print(f"Peak Balance:      ${stats['peak_balance']:.2f}")
        print(f"{pnl_emoji} Session P&L:      ${stats['session_pnl']:.2f} ({stats['session_pnl_pct']: +.2f}%)")
        print(f"Current Drawdown:  {stats['current_drawdown']:.2f}%")
        print(f"Max Drawdown:      {stats['max_drawdown']:.2f}%")
        print(f"Session Duration:   {stats['session_duration_hours']:.1f} hours")
        print("="*60)