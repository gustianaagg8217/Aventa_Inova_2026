import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import time
import yaml

print("=" * 70)
print("PAPER TRADING - OPTIMIZED GOLD STRATEGY")
print("=" * 70)

# Optimized parameters
SMA_FAST = 5
SMA_SLOW = 50
RSI_PERIOD = 20
ATR_SL_MULT = 2.5
ATR_TP_MULT = 4.0
LOT_SIZE = 0.01

# MT5 Connection
account = 9234227
password = 'Klapaucius8#'
server = 'InstaForex-Server'
symbol = 'XAUUSD'

print(f"\n[1/5] Connecting to MT5...")
if not mt5.initialize("C:\\Program Files\\XM Global MT5\\terminal64.exe"):
    print(f"❌ Initialize failed:  {mt5.last_error()}")
    exit()

if not mt5.login(account, password=password, server=server):
    print(f"❌ Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit()

info = mt5.account_info()
print(f"✅ Connected to MT5")
print(f"   Account: {info.login} ({info.name})")
print(f"   Balance: ${info.balance:.2f}")
print(f"   Server: {info.server}")

print(f"\n[2/5] Initializing strategy...")
print(f"  Symbol: {symbol}")
print(f"  SMA Fast/Slow: {SMA_FAST}/{SMA_SLOW}")
print(f"  RSI Period:  {RSI_PERIOD}")
print(f"  Stop Loss: {ATR_SL_MULT}x ATR")
print(f"  Take Profit: {ATR_TP_MULT}x ATR")
print(f"  Lot Size: {LOT_SIZE}")

def calculate_rsi(closes, period=14):
    deltas = np.diff(closes)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(closes)
    rsi[:period] = 100.- 100./(1.+rs)

    for i in range(period, len(closes)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down
        rsi[i] = 100.- 100./(1.+rs)

    return rsi

print(f"\n[3/5] Fetching historical data...")
timeframe = mt5.TIMEFRAME_M1
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

if rates is None:
    print(f"❌ Failed to get rates: {mt5.last_error()}")
    mt5.shutdown()
    exit()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculate indicators
df['sma_fast'] = df['close'].rolling(window=SMA_FAST).mean()
df['sma_slow'] = df['close'].rolling(window=SMA_SLOW).mean()
df['rsi'] = calculate_rsi(df['close'].values, RSI_PERIOD)
df['atr'] = df['close'].rolling(window=14).std() * 1.5  # Simplified ATR

print(f"✅ Data loaded:  {len(df)} bars")
print(f"   Latest close: {df.iloc[-1]['close']:.2f}")
print(f"   SMA Fast: {df.iloc[-1]['sma_fast']:.2f}")
print(f"   SMA Slow:  {df.iloc[-1]['sma_slow']:.2f}")
print(f"   RSI: {df.iloc[-1]['rsi']:.1f}")

print(f"\n[4/5] Checking current positions...")
positions = mt5.positions_get(symbol=symbol)
print(f"   Open positions: {len(positions) if positions else 0}")

print(f"\n[5/5] Monitoring for signals...")
print(f"{'='*70}")
print(f"PAPER TRADING MODE - DEMO ACCOUNT ONLY")
print(f"Strategy will log signals but you can manually execute trades")
print(f"Press Ctrl+C to stop")
print(f"{'='*70}\n")

# Trading loop
try:
    while True:
        # Fetch latest data
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        if rates is None:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Failed to get rates")
            time.sleep(60)
            continue
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['sma_fast'] = df['close'].rolling(window=SMA_FAST).mean()
        df['sma_slow'] = df['close'].rolling(window=SMA_SLOW).mean()
        df['rsi'] = calculate_rsi(df['close'].values, RSI_PERIOD)
        df['atr'] = df['close'].rolling(window=14).std() * 1.5
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for signals
        positions = mt5.positions_get(symbol=symbol)
        has_position = positions is not None and len(positions) > 0
        
        if not has_position:
            # Long signal
            if (previous['sma_fast'] <= previous['sma_slow'] and 
                current['sma_fast'] > current['sma_slow'] and 
                current['rsi'] < 70):
                
                stop_loss = current['close'] - (current['atr'] * ATR_SL_MULT)
                take_profit = current['close'] + (current['atr'] * ATR_TP_MULT)
                
                print(f"\n🟢 [{datetime.now().strftime('%H:%M:%S')}] LONG SIGNAL")
                print(f"   Entry: {current['close']:.2f}")
                print(f"   Stop Loss: {stop_loss:.2f}")
                print(f"   Take Profit: {take_profit:.2f}")
                print(f"   RSI: {current['rsi']:.1f}")
                
            # Short signal
            elif (previous['sma_fast'] >= previous['sma_slow'] and 
                  current['sma_fast'] < current['sma_slow'] and 
                  current['rsi'] > 30):
                
                stop_loss = current['close'] + (current['atr'] * ATR_SL_MULT)
                take_profit = current['close'] - (current['atr'] * ATR_TP_MULT)
                
                print(f"\n🔴 [{datetime.now().strftime('%H:%M:%S')}] SHORT SIGNAL")
                print(f"   Entry: {current['close']:.2f}")
                print(f"   Stop Loss: {stop_loss:.2f}")
                print(f"   Take Profit: {take_profit:.2f}")
                print(f"   RSI: {current['rsi']:.1f}")
        else:
            # Monitor open position
            pos = positions[0]
            pnl = pos.profit
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Position: {pos.type} | Entry: {pos.price_open:.2f} | Current: {current['close']:.2f} | P&L: ${pnl:.2f}", end='\r')
        
        time.sleep(60)  # Check every minute

except KeyboardInterrupt:
    print(f"\n\n{'='*70}")
    print(f"Paper trading stopped by user")
    print(f"{'='*70}")

finally:
    mt5.shutdown()
    print(f"✅ MT5 connection closed")