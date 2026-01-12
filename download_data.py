import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Optional

# Default connection settings (can be overridden by caller)
DEFAULT_ACCOUNT = None
DEFAULT_PASSWORD = None
DEFAULT_SERVER = None


def download_symbol(symbol: str = 'GOLD.ls', mt5_path: Optional[str] = None, account: Optional[int] = None,
                    password: Optional[str] = None, server: Optional[str] = None, timeframe: str = 'M1',
                    output_dir: str = 'data', strategies: Optional[list] = None) -> str:
    """Download historical bars from MT5 for `symbol` and save to CSV in `output_dir`.

    Returns path to saved CSV file.
    """
    # Map timeframe string to MT5 constant
    tf_map = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'H1': mt5.TIMEFRAME_H1,
        'D1': mt5.TIMEFRAME_D1,
    }
    tf = tf_map.get(timeframe, mt5.TIMEFRAME_M1)

    # Use provided credentials or defaults
    account = account or DEFAULT_ACCOUNT
    password = password or DEFAULT_PASSWORD
    server = server or DEFAULT_SERVER

    # Initialize MT5
    if mt5_path:
        ok = mt5.initialize(mt5_path)
    else:
        ok = mt5.initialize()

    if not ok:
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    # Login if credentials provided
    if account and password and server:
        if not mt5.login(account, password=password, server=server):
            mt5.shutdown()
            raise RuntimeError(f"MT5 login failed: {mt5.last_error()}")

    # Default strategies
    if strategies is None:
        strategies = [
            {"days": 90, "method": "range"},
            {"days": 60, "method": "range"},
            {"days": 30, "method": "range"},
            {"count": 100000, "method": "count"},
            {"count": 50000, "method": "count"},
        ]

    rates = None
    try:
        for strategy in strategies:
            if strategy.get("method") == "range":
                days = strategy.get("days", 30)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                rates = mt5.copy_rates_range(symbol, tf, start_date, end_date)
            elif strategy.get("method") == "count":
                count = strategy.get("count", 50000)
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

            if rates is not None and len(rates) > 0:
                break

        if rates is None or len(rates) == 0:
            raise RuntimeError(f"Failed to download data for {symbol}: {mt5.last_error()}")

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        days_actual = (df['time'].max() - df['time'].min()).days
        filename = Path(output_dir) / f"{symbol.replace('.', '_')}_M1_{days_actual}days.csv"
        df.to_csv(filename, index=False)

        return str(filename)

    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    # Simple CLI behavior when run standalone
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--symbol', default='GOLD.ls')
    p.add_argument('--mt5-path', default=None)
    p.add_argument('--output-dir', default='data')
    args = p.parse_args()

    print('Starting download...')
    try:
        out = download_symbol(symbol=args.symbol, mt5_path=args.mt5_path, output_dir=args.output_dir)
        print(f"Downloaded to: {out}")
    except Exception as e:
        print(f"Download failed: {e}")
