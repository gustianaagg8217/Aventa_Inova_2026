import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

print("=" * 70)
print("SIMPLE BACKTESTING ENGINE FOR GOLD HFT STRATEGY")
print("=" * 70)

# Load data
# Auto-detect data file
import glob
data_files = glob.glob('data/XAUUSD_M1_*.csv')
if not data_files:
    print(f"❌ No data files found in data/ folder")
    print("   Please run download_data.py first!")
    sys.exit(1)

# Use the latest/largest file
data_file = max(data_files, key=os.path.getsize)
print(f"\n[1/5] Loading data from {data_file}...")

if not os.path.exists(data_file):
    print(f"❌ Data file not found:  {data_file}")
    print("   Please run download_data.py first!")
    sys.exit(1)

df = pd.read_csv(data_file)
df['time'] = pd.to_datetime(df['time'])
print(f"✅ Loaded {len(df):,} bars")
print(f"   Period: {df['time'].min()} to {df['time'].max()}")

# Filter date range
start_date = df['time'].min()  # Mulai dari data pertama
end_date = df['time'].max()    # Sampai data terakhir
df = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
print(f"\n[2/5] Filtered to date range:")
print(f"   Bars: {len(df):,}")
print(f"   From: {df['time'].min()}")
print(f"   To: {df['time'].max()}")

if len(df) < 100:
    print(f"❌ Insufficient data for backtesting")
    sys.exit(1)

# Calculate indicators
print(f"\n[3/5] Calculating technical indicators...")

# Simple Moving Averages
df['sma_fast'] = df['close'].rolling(window=10).mean()
df['sma_slow'] = df['close'].rolling(window=30).mean()

# RSI
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = calculate_rsi(df['close'])

# ATR for volatility
df['tr'] = np.maximum(
    df['high'] - df['low'],
    np.maximum(
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    )
)
df['atr'] = df['tr'].rolling(window=14).mean()

print(f"✅ Indicators calculated")

# Drop NaN rows
df = df.dropna()
print(f"   Valid bars after indicators: {len(df):,}")

# Simple strategy: SMA crossover + RSI filter
print(f"\n[4/5] Running strategy simulation...")

initial_balance = 1000.0
balance = initial_balance
position = 0  # 0 = no position, 1 = long, -1 = short
entry_price = 0
trades = []
equity_curve = [initial_balance]

risk_per_trade = 0.005  # 0.5% (conservative)
lot_size = 0.01

for i in range(1, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    
    current_price = row['close']
    
    # Entry signals
    if position == 0:
        # Long signal:  Fast SMA crosses above Slow SMA + RSI < 70
        if (prev_row['sma_fast'] <= prev_row['sma_slow'] and 
            row['sma_fast'] > row['sma_slow'] and 
            row['rsi'] < 70):
            
            position = 1
            entry_price = current_price
            stop_loss = entry_price - (row['atr'] * 2)
            take_profit = entry_price + (row['atr'] * 3)
            
        # Short signal: Fast SMA crosses below Slow SMA + RSI > 30
        elif (prev_row['sma_fast'] >= prev_row['sma_slow'] and 
              row['sma_fast'] < row['sma_slow'] and 
              row['rsi'] > 30):
            
            position = -1
            entry_price = current_price
            stop_loss = entry_price + (row['atr'] * 2)
            take_profit = entry_price - (row['atr'] * 3)
    
    # Exit logic
    elif position == 1:  # Long position
        if current_price <= stop_loss or current_price >= take_profit:
            pnl = (current_price - entry_price) * lot_size * 100
            balance += pnl
            trades.append({
                'entry_time': df.iloc[i-1]['time'],
                'exit_time': row['time'],
                'direction':  'LONG',
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl
            })
            position = 0
            
    elif position == -1:  # Short position
        if current_price >= stop_loss or current_price <= take_profit:
            pnl = (entry_price - current_price) * lot_size * 100
            balance += pnl
            trades.append({
                'entry_time':  df.iloc[i-1]['time'],
                'exit_time': row['time'],
                'direction': 'SHORT',
                'entry_price': entry_price,
                'exit_price':  current_price,
                'pnl': pnl
            })
            position = 0
    
    equity_curve.append(balance)

print(f"✅ Simulation complete")

# Calculate metrics
print(f"\n[5/5] Calculating performance metrics...")

trades_df = pd.DataFrame(trades)
total_trades = len(trades_df)

if total_trades > 0:
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] < 0]
    
    win_rate = len(winning_trades) / total_trades * 100
    avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
    
    total_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
    total_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else 0
    
    total_return = ((balance - initial_balance) / initial_balance) * 100
    
    # Calculate drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Sharpe Ratio (simplified)
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    # Print results
    print(f"\n" + "=" * 70)
    print(f"BACKTEST RESULTS")
    print(f"=" * 70)
    print(f"\nPeriod: {start_date.date()} to {end_date.date()}")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"Final Balance: ${balance:.2f}")
    print(f"Total Return: {total_return: .2f}%")
    
    print(f"\n--- TRADE STATISTICS ---")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
    print(f"Losing Trades: {len(losing_trades)} ({100-win_rate:.1f}%)")
    
    print(f"\n--- PROFIT/LOSS ---")
    print(f"Gross Profit: ${total_profit:.2f}")
    print(f"Gross Loss: ${total_loss:.2f}")
    print(f"Net Profit: ${total_profit - total_loss:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    
    print(f"\n--- AVERAGE TRADE ---")
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Largest Win: ${winning_trades['pnl'].max():.2f}" if len(winning_trades) > 0 else "N/A")
    print(f"Largest Loss: ${losing_trades['pnl'].min():.2f}" if len(losing_trades) > 0 else "N/A")
    
    print(f"\n--- RISK METRICS ---")
    print(f"Max Drawdown: {max_drawdown:.2f}%")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    
    print(f"\n--- VERDICT ---")
    passed = 0
    total_checks = 4
    
    if win_rate >= 55:
        print(f"✅ Win Rate >= 55%: PASSED ({win_rate:.1f}%)")
        passed += 1
    else:
        print(f"❌ Win Rate >= 55%: FAILED ({win_rate:.1f}%)")
    
    if profit_factor >= 1.3:
        print(f"✅ Profit Factor >= 1.3: PASSED ({profit_factor:.2f})")
        passed += 1
    else:
        print(f"❌ Profit Factor >= 1.3: FAILED ({profit_factor:.2f})")
    
    if sharpe >= 1.0:
        print(f"✅ Sharpe Ratio >= 1.0: PASSED ({sharpe:.2f})")
        passed += 1
    else: 
        print(f"❌ Sharpe Ratio >= 1.0: FAILED ({sharpe:.2f})")
    
    if max_drawdown > -15:
        print(f"✅ Max Drawdown < 15%: PASSED ({max_drawdown:.2f}%)")
        passed += 1
    else:
        print(f"❌ Max Drawdown < 15%: FAILED ({max_drawdown:.2f}%)")
    
    print(f"\n{passed}/{total_checks} checks passed")
    
    if passed >= 3:
        print(f"\n🎉 Strategy is READY for paper trading!")
    else:
        print(f"\n⚠️ Strategy needs optimization before live trading")
    
    # Save results
    trades_df.to_csv('backtest_trades.csv', index=False)
    print(f"\n✅ Trade log saved to: backtest_trades.csv")
    
else:
    print(f"\n❌ No trades executed during backtest period")
    print(f"   Strategy might be too conservative or data insufficient")

print(f"\n" + "=" * 70)
print(f"BACKTEST COMPLETE")
print(f"=" * 70)