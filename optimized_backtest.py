import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

print("=" * 70)
print("OPTIMIZED STRATEGY BACKTEST - VALIDATION")
print("=" * 70)

# Best parameters from optimization
SMA_FAST = 5
SMA_SLOW = 50
RSI_PERIOD = 20
ATR_SL_MULT = 2.5
ATR_TP_MULT = 4.0

print(f"\nOptimized Parameters:")
print(f"  SMA Fast: {SMA_FAST}")
print(f"  SMA Slow: {SMA_SLOW}")
print(f"  RSI Period: {RSI_PERIOD}")
print(f"  Stop Loss: {ATR_SL_MULT}x ATR")
print(f"  Take Profit: {ATR_TP_MULT}x ATR")

# Load data
data_file = 'data/BTCUSD_M1_59days.csv'
print(f"\n[1/5] Loading data from {data_file}...")

df = pd.read_csv(data_file)
df['time'] = pd.to_datetime(df['time'])
print(f"✅ Loaded {len(df):,} bars")
print(f"   Period: {df['time'].min()} to {df['time'].max()}")

# Use all data
start_date = df['time'].min()
end_date = df['time'].max()
print(f"\n[2/5] Using all available data:")
print(f"   Bars: {len(df):,}")
print(f"   From:  {start_date}")
print(f"   To:  {end_date}")

# Calculate indicators with optimized parameters
print(f"\n[3/5] Calculating technical indicators...")

df['sma_fast'] = df['close'].rolling(window=SMA_FAST).mean()
df['sma_slow'] = df['close'].rolling(window=SMA_SLOW).mean()

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = calculate_rsi(df['close'], period=RSI_PERIOD)

df['tr'] = np.maximum(
    df['high'] - df['low'],
    np.maximum(
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    )
)
df['atr'] = df['tr'].rolling(window=14).mean()

print(f"✅ Indicators calculated")

df = df.dropna()
print(f"   Valid bars: {len(df):,}")

# Strategy simulation
print(f"\n[4/5] Running optimized strategy simulation...")

initial_balance = 1000.0
balance = initial_balance
position = 0
entry_price = 0
entry_time = None
trades = []
equity_curve = [initial_balance]
peak_balance = initial_balance
max_drawdown_dollars = 0

lot_size = 0.01

for i in range(1, len(df)):
    row = df.iloc[i]
    prev_row = df.iloc[i-1]
    current_price = row['close']
    
    # Entry signals
    if position == 0:
        if (prev_row['sma_fast'] <= prev_row['sma_slow'] and 
            row['sma_fast'] > row['sma_slow'] and 
            row['rsi'] < 70):
            
            position = 1
            entry_price = current_price
            entry_time = row['time']
            stop_loss = entry_price - (row['atr'] * ATR_SL_MULT)
            take_profit = entry_price + (row['atr'] * ATR_TP_MULT)
            
        elif (prev_row['sma_fast'] >= prev_row['sma_slow'] and 
              row['sma_fast'] < row['sma_slow'] and 
              row['rsi'] > 30):
            
            position = -1
            entry_price = current_price
            entry_time = row['time']
            stop_loss = entry_price + (row['atr'] * ATR_SL_MULT)
            take_profit = entry_price - (row['atr'] * ATR_TP_MULT)
    
    # Exit logic
    elif position == 1:
        hit_sl = current_price <= stop_loss
        hit_tp = current_price >= take_profit
        
        if hit_sl or hit_tp:
            pnl = (current_price - entry_price) * lot_size * 100
            balance += pnl
            trades.append({
                'entry_time': entry_time,
                'exit_time': row['time'],
                'direction': 'LONG',
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'exit_reason': 'Stop Loss' if hit_sl else 'Take Profit'
            })
            position = 0
            
    elif position == -1:
        hit_sl = current_price >= stop_loss
        hit_tp = current_price <= take_profit
        
        if hit_sl or hit_tp:
            pnl = (entry_price - current_price) * lot_size * 100
            balance += pnl
            trades.append({
                'entry_time': entry_time,
                'exit_time': row['time'],
                'direction': 'SHORT',
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl': pnl,
                'exit_reason': 'Stop Loss' if hit_sl else 'Take Profit'
            })
            position = 0
    
    equity_curve.append(balance)
    
    # Track drawdown
    if balance > peak_balance:
        peak_balance = balance
    drawdown = peak_balance - balance
    if drawdown > max_drawdown_dollars:
        max_drawdown_dollars = drawdown

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
    max_drawdown_pct = (max_drawdown_dollars / peak_balance) * 100
    
    # Sharpe Ratio
    equity_series = pd.Series(equity_curve)
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    # Exit reason analysis
    sl_exits = len(trades_df[trades_df['exit_reason'] == 'Stop Loss'])
    tp_exits = len(trades_df[trades_df['exit_reason'] == 'Take Profit'])
    
    # Print results
    print(f"\n" + "=" * 70)
    print(f"BACKTEST RESULTS - OPTIMIZED STRATEGY")
    print(f"=" * 70)
    print(f"\nPeriod: {start_date.date()} to {end_date.date()}")
    print(f"Initial Balance: ${initial_balance:.2f}")
    print(f"Final Balance: ${balance:.2f}")
    print(f"Net Profit: ${balance - initial_balance:.2f}")
    print(f"Total Return: {total_return: .2f}%")
    
    print(f"\n--- TRADE STATISTICS ---")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {len(winning_trades)} ({win_rate:.1f}%)")
    print(f"Losing Trades: {len(losing_trades)} ({100-win_rate:.1f}%)")
    print(f"Stop Loss Exits: {sl_exits} ({sl_exits/total_trades*100:.1f}%)")
    print(f"Take Profit Exits: {tp_exits} ({tp_exits/total_trades*100:.1f}%)")
    
    print(f"\n--- PROFIT/LOSS ---")
    print(f"Gross Profit: ${total_profit:.2f}")
    print(f"Gross Loss: ${total_loss:.2f}")
    print(f"Net Profit: ${total_profit - total_loss:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Risk: Reward Ratio: 1:{ATR_TP_MULT/ATR_SL_MULT:.2f}")
    
    print(f"\n--- AVERAGE TRADE ---")
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Average Trade: ${(total_profit - total_loss) / total_trades:.2f}")
    print(f"Largest Win: ${winning_trades['pnl'].max():.2f}" if len(winning_trades) > 0 else "N/A")
    print(f"Largest Loss: ${losing_trades['pnl'].min():.2f}" if len(losing_trades) > 0 else "N/A")
    
    print(f"\n--- RISK METRICS ---")
    print(f"Max Drawdown: {max_drawdown_pct:.2f}% (${max_drawdown_dollars:.2f})")
    print(f"Sharpe Ratio:  {sharpe:.2f}")
    print(f"Peak Balance: ${peak_balance:.2f}")
    
    print(f"\n--- VERDICT ---")
    passed = 0
    total_checks = 4
    
    if total_return > 0:
        print(f"✅ Total Return > 0%:  PASSED ({total_return:.2f}%)")
        passed += 1
    else:
        print(f"❌ Total Return > 0%: FAILED ({total_return:.2f}%)")
    
    if profit_factor >= 1.2:
        print(f"✅ Profit Factor >= 1.2: PASSED ({profit_factor:.2f})")
        passed += 1
    else: 
        print(f"❌ Profit Factor >= 1.2: FAILED ({profit_factor:.2f})")
    
    if sharpe >= 0.5:
        print(f"✅ Sharpe Ratio >= 0.5: PASSED ({sharpe:.2f})")
        passed += 1
    else:
        print(f"❌ Sharpe Ratio >= 0.5: FAILED ({sharpe:.2f})")
    
    if max_drawdown_pct < 20:
        print(f"✅ Max Drawdown < 20%: PASSED ({max_drawdown_pct:.2f}%)")
        passed += 1
    else:
        print(f"❌ Max Drawdown < 20%:  FAILED ({max_drawdown_pct:.2f}%)")
    
    print(f"\n{passed}/{total_checks} checks passed")
    
    if passed >= 3:
        print(f"\n🎉 Strategy is READY for paper trading!")
    else:
        print(f"\n⚠️ Strategy needs more testing")
    
    # Save results
    trades_df.to_csv('optimized_backtest_trades.csv', index=False)
    print(f"\n✅ Trade log saved to:  optimized_backtest_trades.csv")
    
    # Monthly breakdown
    trades_df['month'] = pd.to_datetime(trades_df['exit_time']).dt.to_period('M')
    monthly = trades_df.groupby('month')['pnl'].agg(['sum', 'count'])
    print(f"\n--- MONTHLY BREAKDOWN ---")
    print(monthly.to_string())

print(f"\n" + "=" * 70)
print(f"VALIDATION COMPLETE")
print(f"=" * 70)