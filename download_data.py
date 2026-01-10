import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

# Connection settings
account = 11260163
password = 'Klapaucius82#'
server = 'VantageInternational-Demo'

# Initialize and login
print("=" * 60)
print("GOLD DATA DOWNLOADER FOR HFT BACKTESTING")
print("=" * 60)
print("\nConnecting to MT5...")

if not mt5.initialize("C:\\Program Files\\XM Global MT5\\terminal64.exe"):
    print(f"❌ Initialize failed: {mt5.last_error()}")
    exit()

if not mt5.login(account, password=password, server=server):
    print(f"❌ Login failed: {mt5.last_error()}")
    mt5.shutdown()
    exit()

info = mt5.account_info()
print(f"✅ Connected to MT5")
print(f"   Account:  {info.login} ({info.name})")
print(f"   Server: {info.server}")

# Download settings
symbol = 'BTCUSD'
timeframe = mt5.TIMEFRAME_M1

print(f"\n{'=' * 60}")
print(f"DOWNLOAD CONFIGURATION")
print(f"{'=' * 60}")
print(f"Symbol: {symbol}")
print(f"Timeframe: M1 (1 minute bars)")

# Try multiple download strategies
strategies = [
    {"days": 90, "method": "range"},
    {"days": 60, "method": "range"},
    {"days": 30, "method": "range"},
    {"count": 100000, "method": "count"},
    {"count": 50000, "method": "count"},
]

rates = None

for strategy in strategies:
    if strategy["method"] == "range": 
        days = strategy["days"]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"\nTrying:  {days} days ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
        
    elif strategy["method"] == "count":
        count = strategy["count"]
        print(f"\nTrying: Last {count: ,} bars")
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    if rates is not None and len(rates) > 0:
        print(f"✅ Success! Downloaded {len(rates):,} bars")
        break
    else:
        error = mt5.last_error()
        print(f"   Failed: {error}")

if rates is None or len(rates) == 0:
    print(f"\n❌ All download strategies failed!")
    print(f"\nPossible issues:")
    print(f"1.Broker doesn't provide enough historical data")
    print(f"2.Symbol '{symbol}' has limited history")
    print(f"3.Try downloading directly from MT5:")
    print(f"   - Open {symbol} chart")
    print(f"   - Press Home to scroll to oldest data")
    print(f"   - Wait for data to load")
    print(f"   - Try script again")
    mt5.shutdown()
    exit()

# Convert to DataFrame
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Create data folder if not exists
os.makedirs('data', exist_ok=True)

# Calculate actual days
days_actual = (df['time'].max() - df['time'].min()).days

# Save to CSV
filename = f'data/{symbol.replace(".", "_")}_M1_{days_actual}days.csv'
df.to_csv(filename, index=False)

print(f"\n{'=' * 60}")
print(f"✅ DOWNLOAD SUCCESSFUL!")
print(f"{'=' * 60}")
print(f"Total bars:  {len(df):,}")
print(f"From: {df.iloc[0]['time']}")
print(f"To: {df.iloc[-1]['time']}")
print(f"Actual period: {days_actual} days")
print(f"Saved to: {filename}")
print(f"File size: {os.path.getsize(filename) / 1024 / 1024:.2f} MB")

# Statistics
print(f"\n{'=' * 60}")
print(f"DATA STATISTICS")
print(f"{'=' * 60}")
print(f"Price Range:")
print(f"   High: {df['high'].max():.2f}")
print(f"   Low: {df['low'].min():.2f}")
print(f"   Range: {df['high'].max() - df['low'].min():.2f}")
print(f"\nAverage Values:")
print(f"   Open: {df['open'].mean():.2f}")
print(f"   Volume: {df['tick_volume'].mean():.0f}")
print(f"\nData Quality:")
print(f"   Missing bars: {df.isnull().sum().sum()}")
print(f"   Completeness: {(len(df) / (days_actual * 24 * 60)) * 100:.1f}%")

# Show sample data
print(f"\n{'=' * 60}")
print(f"SAMPLE DATA (First 5 rows)")
print(f"{'=' * 60}")
print(df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].head().to_string(index=False))

print(f"\n{'=' * 60}")
print(f"SAMPLE DATA (Last 5 rows)")
print(f"{'=' * 60}")
print(df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].tail().to_string(index=False))

mt5.shutdown()
print(f"\n{'=' * 60}")
print("✅ DONE! Data ready for backtesting.")
print(f"{'=' * 60}")