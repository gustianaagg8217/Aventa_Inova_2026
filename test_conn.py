import MetaTrader5 as mt5
import yaml

# Load config
with open('config/mt5_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get credentials from environment variables (sesuai config Anda)
import os
account = 9234227
password = 'Klapaucius8#'
server = 'InstaForex-Server'

print(f'Connecting to MT5...')
print(f'Account: {account}')
print(f'Server: {server}')

# Initialize MT5
if not mt5.initialize("C:\\Program Files\\mt53\\terminal64.exe"):
    print(f'❌ MT5 initialize failed:  {mt5.last_error()}')
    exit()

# Login
authorized = mt5.login(account, password=password, server=server)

if authorized:
    info = mt5.account_info()
    print(f'✅ Connected successfully!')
    print(f'   Account: {info.login}')
    print(f'   Name: {info.name}')
    print(f'   Balance: ${info.balance:.2f}')
    print(f'   Equity: ${info.equity:.2f}')
    print(f'   Margin Free: ${info.margin_free:.2f}')
    print(f'   Server: {info.server}')
    
    # Check GOLD symbol
    symbols = ['GOLD', 'XAUUSD', 'XAUUSD', 'GOLD_ls']
    print(f'\\nChecking GOLD symbols...')
    for sym in symbols:
        info = mt5.symbol_info(sym)
        if info: 
            print(f'✅ {sym} - Available')
            print(f'   Bid: {info.bid}')
            print(f'   Ask: {info.ask}')
            print(f'   Spread: {info.spread}')
            break
    else:
        print(f'❌ No GOLD symbol found')
else:
    print(f'❌ Login failed:  {mt5.last_error()}')

mt5.shutdown()
