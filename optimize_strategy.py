import pandas as pd
import numpy as np
from itertools import product
import sys

print("=" * 70)
print("STRATEGY PARAMETER OPTIMIZATION")
print("=" * 70)

# Load data
data_file = 'data/BTCUSD_M1_59days.csv'
df = pd.read_csv(data_file)
df['time'] = pd.to_datetime(df['time'])

# Parameter ranges to test
sma_fast_range = [5, 10, 15, 20]
sma_slow_range = [20, 30, 40, 50]
rsi_period_range = [10, 14, 20]
atr_sl_multiplier_range = [1.5, 2.0, 2.5, 3.0]
atr_tp_multiplier_range = [2.0, 2.5, 3.0, 4.0]

print(f"\nTesting parameter combinations...")
print(f"Total combinations: {len(sma_fast_range) * len(sma_slow_range) * len(rsi_period_range) * len(atr_sl_multiplier_range) * len(atr_tp_multiplier_range)}")

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def backtest_params(df, sma_fast, sma_slow, rsi_period, atr_sl_mult, atr_tp_mult):
    # Calculate indicators
    df = df.copy()
    df['sma_fast'] = df['close'].rolling(window=sma_fast).mean()
    df['sma_slow'] = df['close'].rolling(window=sma_slow).mean()
    df['rsi'] = calculate_rsi(df['close'], period=rsi_period)
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(window=14).mean()
    df = df.dropna()
    
    if len(df) < 100:
        return None
    
    # Run simulation
    balance = 1000.0
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        current_price = row['close']
        
        if position == 0:
            if (prev_row['sma_fast'] <= prev_row['sma_slow'] and 
                row['sma_fast'] > row['sma_slow'] and 
                row['rsi'] < 70):
                position = 1
                entry_price = current_price
                stop_loss = entry_price - (row['atr'] * atr_sl_mult)
                take_profit = entry_price + (row['atr'] * atr_tp_mult)
                
            elif (prev_row['sma_fast'] >= prev_row['sma_slow'] and 
                  row['sma_fast'] < row['sma_slow'] and 
                  row['rsi'] > 30):
                position = -1
                entry_price = current_price
                stop_loss = entry_price + (row['atr'] * atr_sl_mult)
                take_profit = entry_price - (row['atr'] * atr_tp_mult)
        
        elif position == 1:
            if current_price <= stop_loss or current_price >= take_profit: 
                pnl = (current_price - entry_price) * 0.01 * 100
                balance += pnl
                trades.append(pnl)
                position = 0
                
        elif position == -1:
            if current_price >= stop_loss or current_price <= take_profit:
                pnl = (entry_price - current_price) * 0.01 * 100
                balance += pnl
                trades.append(pnl)
                position = 0
    
    if len(trades) == 0:
        return None
    
    # Calculate metrics
    trades_series = pd.Series(trades)
    total_return = ((balance - 1000) / 1000) * 100
    win_rate = len(trades_series[trades_series > 0]) / len(trades) * 100
    profit_factor = abs(trades_series[trades_series > 0].sum() / trades_series[trades_series < 0].sum()) if trades_series[trades_series < 0].sum() != 0 else 0
    
    return {
        'sma_fast': sma_fast,
        'sma_slow': sma_slow,
        'rsi_period': rsi_period,
        'atr_sl_mult': atr_sl_mult,
        'atr_tp_mult': atr_tp_mult,
        'total_return':  total_return,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'total_trades': len(trades),
    }

# Grid search
results = []
total_combinations = len(list(product(sma_fast_range, sma_slow_range, rsi_period_range, atr_sl_multiplier_range, atr_tp_multiplier_range)))
counter = 0

for sma_fast, sma_slow, rsi_period, atr_sl_mult, atr_tp_mult in product(sma_fast_range, sma_slow_range, rsi_period_range, atr_sl_multiplier_range, atr_tp_multiplier_range):
    if sma_fast >= sma_slow: 
        continue
    
    counter += 1
    if counter % 50 == 0:
        print(f"Progress: {counter}/{total_combinations} ({counter/total_combinations*100:.1f}%)")
    
    result = backtest_params(df, sma_fast, sma_slow, rsi_period, atr_sl_mult, atr_tp_mult)
    if result:
        results.append(result)

# Sort by total return
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('total_return', ascending=False)

print(f"\n" + "=" * 70)
print(f"OPTIMIZATION RESULTS - TOP 10 PARAMETER SETS")
print(f"=" * 70)
print(results_df.head(10).to_string(index=False))

# Save results
results_df.to_csv('optimization_results.csv', index=False)
print(f"\n✅ Full results saved to: optimization_results.csv")

# Best parameters
best = results_df.iloc[0]
print(f"\n" + "=" * 70)
print(f"BEST PARAMETERS FOUND")
print(f"=" * 70)
print(f"SMA Fast: {best['sma_fast']}")
print(f"SMA Slow: {best['sma_slow']}")
print(f"RSI Period: {best['rsi_period']}")
print(f"ATR Stop Loss Multiplier: {best['atr_sl_mult']}")
print(f"ATR Take Profit Multiplier: {best['atr_tp_mult']}")
print(f"\nPerformance:")
print(f"Total Return: {best['total_return']:.2f}%")
print(f"Win Rate: {best['win_rate']:.1f}%")
print(f"Profit Factor: {best['profit_factor']:.2f}")
print(f"Total Trades: {int(best['total_trades'])}")