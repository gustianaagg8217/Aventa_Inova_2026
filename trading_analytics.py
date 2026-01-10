import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import MetaTrader5 as mt5

# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class TradingAnalytics:
    """Comprehensive trading analytics and performance tracking"""
    
    def __init__(self, trades_file='bot_trades.csv', closed_trades_file='bot_closed_trades.csv'):
        self.trades_file = trades_file
        self.closed_trades_file = closed_trades_file
        self.df_open = None
        self.df_closed = None
        self.load_trades()
    
    def load_trades(self):
        """Load trade history from CSV files"""
        # Load open trades
        if os.path.exists(self.trades_file):
            try:
                self.df_open = pd.read_csv(self.trades_file)
                self.df_open['timestamp'] = pd.to_datetime(self.df_open['timestamp'])
                print(f"✅ Loaded {len(self.df_open)} open trades")
            except Exception as e:
                print(f"⚠️ Error loading open trades: {e}")
                self.df_open = pd.DataFrame()
        else:
            print(f"⚠️ No open trade history found")
            self.df_open = pd.DataFrame()
        
        # Load closed trades
        if os.path.exists(self.closed_trades_file):
            try:
                self.df_closed = pd.read_csv(self.closed_trades_file)
                self.df_closed['close_time'] = pd.to_datetime(self.df_closed['close_time'])
                print(f"✅ Loaded {len(self.df_closed)} closed trades")
            except Exception as e:
                print(f"⚠️ Error loading closed trades: {e}")
                self.df_closed = pd.DataFrame()
        else:
            print(f"⚠️ No closed trade history found")
            self.df_closed = pd.DataFrame()
    
    def get_summary_stats(self):
        """Get overall performance summary"""
        if self.df_closed.empty:
            total_open = len(self.df_open) if not self.df_open.empty else 0
            return {
                'total_open_trades': total_open,
                'status': 'No closed trades yet'
            }
        
        wins = self.df_closed[self.df_closed['pnl'] > 0]
        losses = self.df_closed[self.df_closed['pnl'] <= 0]
        
        total_pnl = self.df_closed['pnl'].sum()
        win_rate = (len(wins) / len(self.df_closed) * 100) if len(self.df_closed) > 0 else 0
        
        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
        
        gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Calculate consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for pnl in self.df_closed['pnl']:
            if pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        stats = {
            'total_open_trades': len(self.df_open) if not self.df_open.empty else 0,
            'total_closed_trades': len(self.df_closed),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_trade': self.df_closed['pnl'].max(),
            'worst_trade': self.df_closed['pnl'].min(),
            'avg_trade':  self.df_closed['pnl'].mean(),
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
        }
        
        return stats
    
    def get_daily_performance(self, days=30):
        """Get performance for last N days"""
        if self.df_closed.empty:
            return None
        
        df = self.df_closed.copy()
        df['date'] = pd.to_datetime(df['close_time']).dt.date
        
        daily = df.groupby('date').agg({
            'pnl': ['sum', 'count', 'mean'],
        }).reset_index()
        
        daily.columns = ['date', 'pnl', 'trades', 'avg_pnl']
        
        # Calculate win rate per day
        daily['wins'] = daily.apply(
            lambda row: len(df[(df['date'] == row['date']) & (df['pnl'] > 0)]),
            axis=1
        )
        daily['win_rate'] = (daily['wins'] / daily['trades'] * 100)
        
        return daily.tail(days)
    
    def get_trade_type_performance(self):
        """Analyze performance by trade type (LONG vs SHORT)"""
        if self.df_closed.empty or 'type' not in self.df_closed.columns:
            return None
        
        performance = {}
        
        for trade_type in ['LONG', 'SHORT']:
            trades = self.df_closed[self.df_closed['type'] == trade_type]
            if len(trades) > 0:
                wins = trades[trades['pnl'] > 0]
                performance[trade_type] = {
                    'total':  len(trades),
                    'wins': len(wins),
                    'losses': len(trades) - len(wins),
                    'win_rate': len(wins) / len(trades) * 100,
                    'total_pnl': trades['pnl'].sum(),
                    'avg_pnl': trades['pnl'].mean(),
                }
        
        return performance
    
    def get_hourly_performance(self):
        """Analyze performance by hour of day"""
        if self.df_closed.empty: 
            return None
        
        df = self.df_closed.copy()
        df['hour'] = pd.to_datetime(df['close_time']).dt.hour
        
        hourly = df.groupby('hour').agg({
            'pnl': ['sum', 'count', 'mean'],
        }).reset_index()
        
        hourly.columns = ['hour', 'total_pnl', 'trades', 'avg_pnl']
        
        return hourly
    
    def get_drawdown_info(self):
        """Calculate drawdown statistics"""
        if self.df_closed.empty:
            return None
        
        df = self.df_closed.copy().sort_values('close_time')
        df['cumulative_pnl'] = df['pnl'].cumsum()
        df['peak'] = df['cumulative_pnl'].cummax()
        df['drawdown'] = df['peak'] - df['cumulative_pnl']
        df['drawdown_pct'] = (df['drawdown'] / df['peak'] * 100).fillna(0)
        
        max_drawdown = df['drawdown'].max()
        max_drawdown_pct = df['drawdown_pct'].max()
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'current_drawdown': df['drawdown'].iloc[-1] if len(df) > 0 else 0,
        }
    
    def print_dashboard(self):
        """Print comprehensive analytics dashboard"""
        print("\n" + "="*80)
        print("📊 TRADING ANALYTICS DASHBOARD")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        stats = self.get_summary_stats()
        
        if 'status' in stats:
            print("\n⚠️ " + stats['status'])
            if stats['total_open_trades'] > 0:
                print(f"   Open Trades: {stats['total_open_trades']}")
            print("\n   Start trading to see analytics!")
            return
        
        # Overall Performance
        print("\n📈 OVERALL PERFORMANCE")
        print("-"*80)
        print(f"Open Trades:         {stats['total_open_trades']}")
        print(f"Closed Trades:      {stats['total_closed_trades']}")
        print(f"Wins:               {stats['wins']} ({stats['win_rate']:.1f}%)")
        print(f"Losses:             {stats['losses']}")
        print(f"Max Consecutive W:   {stats['max_consecutive_wins']}")
        print(f"Max Consecutive L:  {stats['max_consecutive_losses']}")
        
        # P&L Metrics
        print("\n💰 PROFIT & LOSS")
        print("-"*80)
        pnl_emoji = "📈" if stats['total_pnl'] > 0 else "📉"
        print(f"{pnl_emoji} Total P&L:          ${stats['total_pnl']:.2f}")
        print(f"Gross Profit:       ${stats['gross_profit']:.2f}")
        print(f"Gross Loss:         ${stats['gross_loss']:.2f}")
        print(f"Average Trade:      ${stats['avg_trade']:.2f}")
        print(f"Average Win:        ${stats['avg_win']:.2f}")
        print(f"Average Loss:       ${stats['avg_loss']:.2f}")
        
        pf_emoji = "🟢" if stats['profit_factor'] > 1.5 else "🟡" if stats['profit_factor'] > 1.0 else "🔴"
        print(f"{pf_emoji} Profit Factor:      {stats['profit_factor']:.2f}")
        print(f"Best Trade:         ${stats['best_trade']:.2f}")
        print(f"Worst Trade:        ${stats['worst_trade']:.2f}")
        
        # Drawdown
        dd_info = self.get_drawdown_info()
        if dd_info:
            print("\n📉 DRAWDOWN ANALYSIS")
            print("-"*80)
            print(f"Max Drawdown:       ${dd_info['max_drawdown']:.2f} ({dd_info['max_drawdown_pct']:.2f}%)")
            print(f"Current Drawdown:   ${dd_info['current_drawdown']:.2f}")
        
        # Trade Type Performance
        type_perf = self.get_trade_type_performance()
        if type_perf:
            print("\n📊 LONG vs SHORT PERFORMANCE")
            print("-"*80)
            for trade_type, data in type_perf.items():
                print(f"{trade_type:6s}  Trades: {data['total']:3d}  Wins: {data['wins']:3d} ({data['win_rate']:.1f}%)  P&L: ${data['total_pnl']:.2f}")
        
        # Daily Performance (Last 7 Days)
        daily = self.get_daily_performance(7)
        if daily is not None and not daily.empty:
            print("\n📅 LAST 7 DAYS")
            print("-"*80)
            print(f"{'Date':<12} {'Trades': >8} {'Wins':>6} {'Win%':>8} {'Avg P&L':>10} {'Total P&L':>12}")
            print("-"*80)
            for _, row in daily.iterrows():
                date_str = str(row['date'])
                trades = int(row['trades'])
                wins = int(row['wins'])
                wr = row['win_rate']
                avg_pnl = row['avg_pnl']
                total_pnl = row['pnl']
                
                print(f"{date_str:<12} {trades:>8d} {wins:>6d} {wr: >7.1f}% ${avg_pnl:>8.2f} ${total_pnl:>11.2f}")
        
        # Best Trading Hours
        hourly = self.get_hourly_performance()
        if hourly is not None and not hourly.empty:
            top_hours = hourly.nlargest(5, 'total_pnl')
            if not top_hours.empty:
                print("\n⏰ TOP 5 PROFITABLE HOURS (GMT)")
                print("-"*80)
                print(f"{'Hour':>6} {'Trades':>8} {'Total P&L':>12} {'Avg P&L':>10}")
                print("-"*80)
                for _, row in top_hours.iterrows():
                    hour = int(row['hour'])
                    trades = int(row['trades'])
                    total_pnl = row['total_pnl']
                    avg_pnl = row['avg_pnl']
                    print(f"{hour:02d}:00  {trades:>8d} ${total_pnl:>11.2f} ${avg_pnl:>9.2f}")
        
        print("\n" + "="*80)
    
    def export_report(self, filename='trading_report.json'):
        """Export analytics to JSON file"""
        stats = self.get_summary_stats()
        
        if 'status' in stats: 
            print("⚠️ No closed trades to export")
            return
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': stats,
            'trade_type_performance': self.get_trade_type_performance(),
            'drawdown_info': self.get_drawdown_info(),
            'daily_performance': self.get_daily_performance(30).to_dict('records') if self.get_daily_performance(30) is not None else None,
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Report exported to {filename}")
    
    def export_excel(self, filename='trading_report.xlsx'):
        """Export detailed report to Excel"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Open trades
                if not self.df_open.empty:
                    self.df_open.to_excel(writer, sheet_name='Open Trades', index=False)
                
                # Closed trades
                if not self.df_closed.empty:
                    self.df_closed.to_excel(writer, sheet_name='Closed Trades', index=False)
                
                # Summary stats
                stats = self.get_summary_stats()
                if stats and 'status' not in stats:
                    stats_df = pd.DataFrame([stats])
                    stats_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Daily performance
                daily = self.get_daily_performance(30)
                if daily is not None and not daily.empty:
                    daily.to_excel(writer, sheet_name='Daily Performance', index=False)
                
                # Hourly performance
                hourly = self.get_hourly_performance()
                if hourly is not None and not hourly.empty:
                    hourly.to_excel(writer, sheet_name='Hourly Performance', index=False)
            
            print(f"✅ Excel report exported to {filename}")
        except Exception as e:
            print(f"⚠️ Excel export failed: {e}")
            print("   Install openpyxl:  pip install openpyxl")


# ============================================================================
# LIVE PERFORMANCE TRACKER
# ============================================================================

class LivePerformanceTracker:
    """Track live performance metrics"""
    
    def __init__(self):
        self.start_balance = 0
        self.start_equity = 0
        self.peak_balance = 0
        self.peak_equity = 0
        self.current_drawdown = 0
        self.max_drawdown = 0
        self.session_start = datetime.now()
    
    def initialize(self, account_info):
        """Initialize tracker with account info"""
        self.start_balance = account_info.balance
        self.start_equity = account_info.equity
        self.peak_balance = account_info.balance
        self.peak_equity = account_info.equity
        print(f"\n📊 Live Performance Tracker Initialized")
        print(f"   Starting Balance: ${self.start_balance:.2f}")
        print(f"   Starting Equity:   ${self.start_equity:.2f}")
    
    def update(self, account_info):
        """Update performance metrics"""
        current_equity = account_info.equity
        
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Calculate drawdown
        self.current_drawdown = ((self.peak_equity - current_equity) / self.peak_equity * 100) if self.peak_equity > 0 else 0
        
        # Update max drawdown
        if self.current_drawdown > self.max_drawdown:
            self.max_drawdown = self.current_drawdown
    
    def get_session_stats(self, account_info):
        """Get current session statistics"""
        current_balance = account_info.balance
        current_equity = account_info.equity
        
        session_pnl = current_balance - self.start_balance
        session_pnl_pct = (session_pnl / self.start_balance * 100) if self.start_balance > 0 else 0
        
        floating_pnl = current_equity - current_balance
        
        session_duration = datetime.now() - self.session_start
        hours = session_duration.total_seconds() / 3600
        
        return {
            'start_balance': self.start_balance,
            'current_balance': current_balance,
            'current_equity': current_equity,
            'peak_balance': self.peak_balance,
            'peak_equity':  self.peak_equity,
            'session_pnl': session_pnl,
            'session_pnl_pct': session_pnl_pct,
            'floating_pnl': floating_pnl,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'session_duration_hours': hours,
        }
    
    def print_live_stats(self, account_info):
        """Print live statistics"""
        stats = self.get_session_stats(account_info)
        
        print("\n" + "="*70)
        print("📊 LIVE SESSION PERFORMANCE")
        print("="*70)
        
        pnl_emoji = "📈" if stats['session_pnl'] > 0 else "📉" if stats['session_pnl'] < 0 else "➖"
        float_emoji = "🟢" if stats['floating_pnl'] > 0 else "🔴" if stats['floating_pnl'] < 0 else "⚪"
        
        print(f"Start Balance:      ${stats['start_balance']:.2f}")
        print(f"Current Balance:    ${stats['current_balance']:.2f}")
        print(f"Current Equity:     ${stats['current_equity']:.2f}")
        print(f"Peak Equity:        ${stats['peak_equity']:.2f}")
        print(f"{pnl_emoji} Session P&L:        ${stats['session_pnl']:.2f} ({stats['session_pnl_pct']: .2f}%)")
        print(f"{float_emoji} Floating P&L:       ${stats['floating_pnl']:.2f}")
        print(f"Current Drawdown:   {stats['current_drawdown']:.2f}%")
        print(f"Max Drawdown:       {stats['max_drawdown']:.2f}%")
        print(f"Session Duration:   {stats['session_duration_hours']:.1f} hours")
        print("="*70)

# ============================================================================
# MAIN MENU
# ============================================================================

def main():
    print("\n" + "="*80)
    print("📊 TRADING BOT ANALYTICS SYSTEM")
    print("="*80)
    
    analytics = TradingAnalytics()
    
    while True:
        print("\n📋 MAIN MENU:")
        print("1.View Analytics Dashboard")
        print("2.View Last 30 Days Performance")
        print("3.Export JSON Report")
        print("4.Export Excel Report")
        print("5.View Hourly Performance")
        print("6.Check Live Performance (requires MT5 connection)")
        print("7.Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            analytics.print_dashboard()
        
        elif choice == '2': 
            daily = analytics.get_daily_performance(30)
            if daily is not None and not daily.empty:
                print("\n" + "="*80)
                print("📅 LAST 30 DAYS PERFORMANCE")
                print("="*80)
                print(f"{'Date':<12} {'Trades': >8} {'Wins':>6} {'Win%':>8} {'Avg P&L': >10} {'Total P&L':>12}")
                print("-"*80)
                for _, row in daily.iterrows():
                    date_str = str(row['date'])
                    trades = int(row['trades'])
                    wins = int(row['wins'])
                    wr = row['win_rate']
                    avg_pnl = row['avg_pnl']
                    total_pnl = row['pnl']
                    print(f"{date_str:<12} {trades:>8d} {wins:>6d} {wr:>7.1f}% ${avg_pnl:>8.2f} ${total_pnl:>11.2f}")
                print("="*80)
            else:
                print("\n⚠️ No daily data available")
        
        elif choice == '3':
            analytics.export_report()
        
        elif choice == '4':
            analytics.export_excel()
        
        elif choice == '5': 
            hourly = analytics.get_hourly_performance()
            if hourly is not None and not hourly.empty:
                print("\n" + "="*80)
                print("⏰ HOURLY PERFORMANCE (GMT)")
                print("="*80)
                print(f"{'Hour':>6} {'Trades':>8} {'Total P&L':>12} {'Avg P&L':>10}")
                print("-"*80)
                for _, row in hourly.iterrows():
                    hour = int(row['hour'])
                    trades = int(row['trades'])
                    total_pnl = row['total_pnl']
                    avg_pnl = row['avg_pnl']
                    print(f"{hour:02d}:00  {trades:>8d} ${total_pnl:>11.2f} ${avg_pnl:>9.2f}")
                print("="*80)
            else:
                print("\n⚠️ No hourly data available")
        
        elif choice == '6':
            print("\n🔌 Connecting to MT5...")
            if mt5.initialize():
                info = mt5.account_info()
                if info:
                    tracker = LivePerformanceTracker()
                    tracker.initialize(info)
                    tracker.update(info)
                    tracker.print_live_stats(info)
                    mt5.shutdown()
                else:
                    print("❌ Failed to get account info")
            else:
                print("❌ Failed to connect to MT5")
                print("   Make sure MT5 is running and bot has connected at least once")
        
        elif choice == '7':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid option")


if __name__ == "__main__":
    main()