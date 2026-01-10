import pandas as pd
import json
import os
from datetime import datetime
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_data():
    """Load bot data"""
    trades = []
    state = {}
    
    if os.path.exists('bot_trades.csv'):
        trades_df = pd.read_csv('bot_trades.csv')
        trades = trades_df.to_dict('records')
    
    if os.path.exists('bot_state.json'):
        with open('bot_state.json', 'r') as f:
            state = json.load(f)
    
    return trades, state

def calculate_metrics(trades):
    """Calculate performance metrics"""
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    
    metrics = {
        'total_trades': len(df),
        'open_trades': 0,
        'closed_trades': 0,
        'wins': 0,
        'losses': 0,
        'win_rate':  0,
        'total_pnl': 0,
        'best_trade': 0,
        'worst_trade':  0,
        'avg_win':  0,
        'avg_loss': 0,
        'profit_factor': 0,
        'avg_trade_duration':  'N/A'
    }
    
    return metrics

def display_dashboard(trades, state, metrics):
    """Display dashboard"""
    clear_screen()
    
    print("=" * 80)
    print("🤖 AUTO-TRADING BOT - LIVE DASHBOARD")
    print("=" * 80)
    print(f"Last Update:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Bot Status
    print("🟢 BOT STATUS")
    print("-" * 80)
    print(f"Status:          LIVE & ACTIVE")
    print(f"Today's Trades:  {state.get('daily_trades', 0)}/15")
    print(f"Total Trades:    {state.get('total_trades', 0)}")
    print(f"Daily P&L:       ${state.get('daily_pnl', 0):.2f}")
    print()
    
    # Recent Trades
    print("📊 RECENT TRADES")
    print("-" * 80)
    if trades:
        recent = trades[-5:]  # Last 5 trades
        for i, trade in enumerate(reversed(recent), 1):
            timestamp = trade.get('timestamp', 'N/A')
            if timestamp != 'N/A':
                # Format timestamp nicely
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime('%m-%d %H:%M:%S')
                except:
                    pass
            
            trade_type = trade.get('type', 'N/A')
            entry = trade.get('entry', 0)
            session = trade.get('session', 'N/A')
            rsi = trade.get('rsi', 0)
            
            # Fixed formatting (no space in format specifier)
            print(f"{i}. [{timestamp}] {trade_type:<5s} @ {entry:7.2f} | RSI:{rsi: 5.1f} | {session}")
    else:
        print("No trades yet")
    print()
    
    # Session Breakdown
    print("⏰ SESSION BREAKDOWN")
    print("-" * 80)
    if trades:
        df = pd.DataFrame(trades)
        session_counts = df['session'].value_counts()
        for session, count in session_counts.items():
            pct = (count / len(df)) * 100
            print(f"{session: <10s}: {count: 2d} trades ({pct: 5.1f}%)")
    else:
        print("No data yet")
    print()
    
    # Trade Type Breakdown
    if trades:
        print("📈 DIRECTION BREAKDOWN")
        print("-" * 80)
        df = pd.DataFrame(trades)
        type_counts = df['type'].value_counts()
        for trade_type, count in type_counts.items():
            pct = (count / len(df)) * 100
            print(f"{trade_type:<6s}: {count:2d} trades ({pct:5.1f}%)")
        print()
    
    # Average RSI
    if trades:
        print("📊 INDICATOR STATS")
        print("-" * 80)
        df = pd.DataFrame(trades)
        print(f"Average RSI:     {df['rsi'].mean():.2f}")
        print(f"RSI Range:      {df['rsi'].min():.2f} - {df['rsi'].max():.2f}")
        if 'atr' in df.columns:
            print(f"Average ATR:    {df['atr'].mean():.2f}")
        print()
    
    print("=" * 80)
    print("Press Ctrl+C to exit | Refreshes every 30 seconds")
    print("=" * 80)

def main():
    """Main dashboard loop"""
    print("Starting dashboard...")
    print("Press Ctrl+C to stop")
    time.sleep(2)
    
    try:
        while True:
            trades, state = load_data()
            metrics = calculate_metrics(trades)
            display_dashboard(trades, state, metrics)
            time.sleep(30)  # Refresh every 30 seconds
    
    except KeyboardInterrupt: 
        print("\n\nDashboard stopped")

if __name__ == "__main__":
    main()