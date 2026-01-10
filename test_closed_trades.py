# Create test_closed_trades.py
import pandas as pd
from datetime import datetime, timedelta

data = []
for i in range(20):
    data.append({
        'close_time': datetime.now() - timedelta(days=i),
        'ticket': 1000 + i,
        'type': 'LONG' if i % 2 == 0 else 'SHORT',
        'entry_price': 4500 + (i * 10),
        'exit_price':  4510 + (i * 10),
        'volume': 0.01,
        'pnl': (5.0 if i % 3 != 0 else -3.0),  # 66% win rate
        'exit_reason': 'Take Profit' if i % 3 != 0 else 'Stop Loss',
        'duration': 'TBD'
    })

df = pd.DataFrame(data)
df.to_csv('bot_closed_trades.csv', index=False)
print("✅ Test data created!")