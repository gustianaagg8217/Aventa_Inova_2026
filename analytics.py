import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class TradingAnalytics:
    """Comprehensive trading analytics and performance tracking"""
    
    def __init__(self, trades_file='bot_trades.csv'):
        self.trades_file = trades_file
        self.df = None
        self.load_trades()
    
    def load_trades(self):
        """Load trade history from CSV"""
        if os.path.exists(self.trades_file):
            try:
                self.df = pd.read_csv(self.trades_file)
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                print(f"✅ Loaded {len(self.df)} trades")
            except Exception as e:
                print(f"⚠️ Error loading trades: {e}")
                self.df = pd.DataFrame()
        else:
            print(f"⚠️ No trade history found")
            self.df = pd.DataFrame()
    
    def calculate_pnl(self):
        """Calculate P&L for each trade (simulated for now)"""
        if self.df.empty:
            return
        
        # For demo purposes - in real system, get actual closed trade data
        # This assumes we have closed_trades.csv with actual P&L
        if os.path.exists('bot_closed_trades.csv'):
            closed_df = pd.read_csv('bot_closed_trades.csv')
            return closed_df
        
        return pd.DataFrame()
    
    def get_summary_stats(self):
        """Get overall performance summary"""
        if self.df.empty:
            return None
        
        # Try to get closed trades with actual P&L
        closed_df = self.calculate_pnl()
        
        if closed_df.empty:
            stats = {
                'total_trades': len(self.df),
                'status': 'No closed trades yet'
            }
        else: 
            wins = closed_df[closed_df['pnl'] > 0]
            losses = closed_df[closed_df['pnl'] <= 0]
            
            total_pnl = closed_df['pnl'].sum()
            win_rate = (len(wins) / len(closed_df) * 100) if len(closed_df) > 0 else 0
            
            avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
            avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0
            
            profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if len(losses) > 0 and losses['pnl'].sum() != 0 else 0
            
            stats = {
                'total_trades': len(self.df),
                'closed_trades': len(closed_df),
                'open_trades': len(self.df) - len(closed_df),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor':  profit_factor,
                'best_trade':  closed_df['pnl'].max() if not closed_df.empty else 0,
                'worst_trade': closed_df['pnl'].min() if not closed_df.empty else 0,
            }
        
        return stats
    
    def get_session_performance(self):
        """Analyze performance by trading session"""
        if self.df.empty or 'session' not in self.df.columns:
            return None
        
        closed_df = self.calculate_pnl()
        if closed_df.empty or 'session' not in closed_df.columns:
            return None
        
        # Merge session info
        if 'timestamp' in closed_df.columns and 'timestamp' in self.df.columns:
            # Match by approximate timestamp or order_id
            session_perf = {}
            
            for session in ['LONDON', 'NY', 'ASIAN']:
                session_trades = self.df[self.df['session'] == session]
                if len(session_trades) > 0:
                    session_perf[session] = {
                        'trades': len(session_trades),
                        'avg_rsi': session_trades['rsi'].mean() if 'rsi' in session_trades.columns else 0
                    }
            
            return session_perf
        
        return None
    
    def get_daily_performance(self, days=7):
        """Get performance for last N days"""
        if self.df.empty:
            return None
        
        closed_df = self.calculate_pnl()
        if closed_df.empty:
            return None
        
        closed_df['date'] = pd.to_datetime(closed_df['close_time']).dt.date
        daily = closed_df.groupby('date').agg({
            'pnl': ['sum', 'count'],
        }).reset_index()
        
        daily.columns = ['date', 'pnl', 'trades']
        daily['win_rate'] = daily.apply(
            lambda row: len(closed_df[(closed_df['date'] == row['date']) & (closed_df['pnl'] > 0)]) / row['trades'] * 100 if row['trades'] > 0 else 0,
            axis=1
        )
        
        return daily.tail(days)
    
    def get_rr_analysis(self):
        """Analyze risk/reward ratios"""
        if self.df.empty:
            return None
        
        if 'sl' in self.df.columns and 'tp' in self.df.columns and 'entry' in self.df.columns:
            self.df['risk'] = abs(self.df['entry'] - self.df['sl'])
            self.df['reward'] = abs(self.df['entry'] - self.df['tp'])
            self.df['rr_ratio'] = self.df['reward'] / self.df['risk']
            
            return {
                'avg_rr': self.df['rr_ratio'].mean(),
                'min_rr': self.df['rr_ratio'].min(),
                'max_rr': self.df['rr_ratio'].max(),
            }
        
        return None
    
    def print_dashboard(self):
        """Print comprehensive analytics dashboard"""
        print("\n" + "="*80)
        print("📊 TRADING ANALYTICS DASHBOARD")
        print("="*80)
        
        stats = self.get_summary_stats()
        
        if stats is None or 'status' in stats:
            print("\n⚠️  No trade data available yet")
            print("   Start trading to see analytics!")
            return
        
        # Overall Performance
        print("\n📈 OVERALL PERFORMANCE")
        print("-"*80)
        print(f"Total Trades:       {stats['total_trades']}")
        print(f"Closed Trades:     {stats['closed_trades']}")
        print(f"Open Trades:       {stats['open_trades']}")
        print(f"Wins:              {stats['wins']} ({stats['win_rate']:.1f}%)")
        print(f"Losses:            {stats['losses']}")
        
        # P&L Metrics
        print("\n💰 PROFIT & LOSS")
        print("-"*80)
        pnl_emoji = "📈" if stats['total_pnl'] > 0 else "📉"
        print(f"{pnl_emoji} Total P&L:         ${stats['total_pnl']:.2f}")
        print(f"Average Win:       ${stats['avg_win']:.2f}")
        print(f"Average Loss:      ${stats['avg_loss']:.2f}")
        print(f"Profit Factor:     {stats['profit_factor']:.2f}")
        print(f"Best Trade:        ${stats['best_trade']:.2f}")
        print(f"Worst Trade:       ${stats['worst_trade']:.2f}")
        
        # Risk/Reward
        rr = self.get_rr_analysis()
        if rr: 
            print("\n⚖️  RISK/REWARD ANALYSIS")
            print("-"*80)
            print(f"Average R: R:        1:{rr['avg_rr']:.2f}")
            print(f"Min R:R:           1:{rr['min_rr']:.2f}")
            print(f"Max R:R:            1:{rr['max_rr']:.2f}")
        
        # Session Performance
        session_perf = self.get_session_performance()
        if session_perf:
            print("\n🌍 SESSION PERFORMANCE")
            print("-"*80)
            for session, data in session_perf.items():
                print(f"{session: 10s}  Trades: {data['trades']: 3d}  Avg RSI: {data['avg_rsi']:.1f}")
        
        # Daily Performance
        daily = self.get_daily_performance(7)
        if daily is not None and not daily.empty:
            print("\n📅 LAST 7 DAYS")
            print("-"*80)
            print(f"{'Date':<12} {'Trades': >8} {'P&L':>12} {'Win Rate':>10}")
            print("-"*80)
            for _, row in daily.iterrows():
                pnl_str = f"${row['pnl']:>8.2f}"
                wr_str = f"{row['win_rate']: >6.1f}%"
                print(f"{str(row['date']):<12} {row['trades']: >8.0f} {pnl_str: >12} {wr_str: >10}")
        
        print("\n" + "="*80)
        print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def export_report(self, filename='trading_report.json'):
        """Export analytics to JSON file"""
        stats = self.get_summary_stats()
        if stats is None: 
            print("⚠️  No data to export")
            return
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': stats,
            'rr_analysis': self.get_rr_analysis(),
            'session_performance': self.get_session_performance(),
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"✅ Report exported to {filename}")
    
    def export_excel(self, filename='trading_report.xlsx'):
        """Export detailed report to Excel"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # All trades
                if not self.df.empty:
                    self.df.to_excel(writer, sheet_name='All Trades', index=False)
                
                # Closed trades
                closed_df = self.calculate_pnl()
                if not closed_df.empty:
                    closed_df.to_excel(writer, sheet_name='Closed Trades', index=False)
                
                # Summary stats
                stats = self.get_summary_stats()
                if stats: 
                    stats_df = pd.DataFrame([stats])
                    stats_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Daily performance
                daily = self.get_daily_performance(30)
                if daily is not None and not daily.empty:
                    daily.to_excel(writer, sheet_name='Daily Performance', index=False)
            
            print(f"✅ Excel report exported to {filename}")
        except Exception as e:
            print(f"⚠️  Excel export failed: {e}")
            print("   Install openpyxl:  pip install openpyxl")


# Standalone execution for quick analytics check
if __name__ == "__main__":
    print("="*80)
    print("📊 TRADING ANALYTICS")
    print("="*80)
    
    analytics = TradingAnalytics()
    analytics.print_dashboard()
    
    # Export options
    print("\n📁 EXPORT OPTIONS:")
    print("1.JSON Report")
    print("2.Excel Report")
    print("3.Both")
    print("4.Skip")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        analytics.export_report()
    elif choice == '2':
        analytics.export_excel()
    elif choice == '3':
        analytics.export_report()
        analytics.export_excel()
    
    print("\n✅ Analytics complete!")