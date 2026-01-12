#!/usr/bin/env python3
"""
Real-time market monitoring and prediction system.

Fetches live XAUUSD data, runs inference, and displays predictions.
Supports multiple data sources: MT5, yfinance, or CSV rolling window.

Usage:
    # With MT5 (requires terminal running)
    python real_time_monitor.py --source mt5 --login 123456 --password pass --server server

    # With yfinance (fallback for testing)
    python real_time_monitor.py --source yfinance

    # With CSV rolling window (for backtesting)
    python real_time_monitor.py --source csv --data-file data/XAUUSD_M1_59days.csv --interval 60
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from inference import ModelPredictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('real_time_monitor')

# Optional imports
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class DataSourceMT5:
    """Fetch live data from MetaTrader 5."""
    
    def __init__(self, login: int, password: str, server: str):
        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 not installed")
        
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to MT5."""
        if mt5.initialize(login=self.login, password=self.password, server=self.server):
            self.connected = True
            logger.info(f"Connected to MT5: {self.server}")
        else:
            raise ConnectionError(f"Failed to connect to MT5: {mt5.last_error()}")
    
    def get_candles(self, symbol: str = 'XAUUSD', timeframe: int = None, n_candles: int = 100) -> pd.DataFrame:
        """Fetch OHLC candles from MT5."""
        if not self.connected:
            raise RuntimeError("Not connected to MT5")
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M1
        
        ticks = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
        
        if ticks is None:
            logger.error(f"Failed to fetch {symbol}: {mt5.last_error()}")
            return None
        
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df[['time', 'open', 'high', 'low', 'close']]
    
    def disconnect(self):
        """Disconnect from MT5."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")


class DataSourceYFinance:
    """Fetch data from yfinance (limited real-time, mainly for demo)."""
    
    def __init__(self):
        if not YFINANCE_AVAILABLE:
            raise RuntimeError("yfinance not installed: pip install yfinance")
        logger.info("Using yfinance data source")
    
    def get_candles(self, symbol: str = 'GC=F', interval: str = '5m', n_candles: int = 100) -> pd.DataFrame:
        """
        Fetch candles from yfinance.
        Note: yfinance has limited real-time data.
        
        Args:
            symbol: yfinance symbol (GC=F for gold futures)
            interval: Candle interval (5m, 15m, 1h, 1d) - 1m may not be available
            n_candles: Number of candles to fetch
        """
        try:
            # Fetch data with suppressed output
            df = yf.download(symbol, period='7d', interval=interval, progress=False)
            
            if df is None or len(df) == 0:
                logger.warning(f"No data retrieved for {symbol}")
                return None
            
            # Reset index to get time as column
            df = df.reset_index()
            
            # Handle column names (might be tuple for multi-index)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            # Standardize columns to lowercase
            df.columns = [str(col).lower() for col in df.columns]
            
            # Rename time/date columns
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'time'})
            elif 'datetime' in df.columns:
                df = df.rename(columns={'datetime': 'time'})
            
            # Ensure time column exists and is datetime
            if 'time' not in df.columns:
                logger.warning("No time/date column found in yfinance data")
                return None
            
            df['time'] = pd.to_datetime(df['time'])
            
            # Return last n_candles with required columns
            cols = [col for col in ['time', 'open', 'high', 'low', 'close'] if col in df.columns]
            if len(cols) < 5:
                logger.warning(f"Missing columns in yfinance data. Found: {cols}")
                return None
            
            return df[cols].tail(n_candles).reset_index(drop=True)
        
        except Exception as e:
            logger.error(f"Failed to fetch from yfinance: {e}", exc_info=False)
            return None


class DataSourceCSV:
    """Rolling window over CSV data (for backtesting/demo)."""
    
    def __init__(self, data_file: Path):
        self.data_file = Path(data_file)
        self.df = self._load_data()
        self.current_idx = 0
        logger.info(f"Loaded {len(self.df)} rows from {data_file}")
    
    def _load_data(self) -> pd.DataFrame:
        """Load CSV data."""
        df = pd.read_csv(self.data_file)
        df['time'] = pd.to_datetime(df.get('time', df.index))
        return df[['time', 'open', 'high', 'low', 'close']].sort_values('time').reset_index(drop=True)
    
    def get_candles(self, n_candles: int = 100) -> pd.DataFrame:
        """
        Return sliding window of candles.
        Advances pointer each call for simulation.
        """
        end_idx = min(self.current_idx + n_candles, len(self.df))
        start_idx = max(0, end_idx - n_candles)
        
        df = self.df.iloc[start_idx:end_idx].copy()
        
        # Advance for next call
        self.current_idx = end_idx
        
        return df if len(df) > 0 else None


class RealTimeMonitor:
    """Monitor live market data and generate trading signals."""
    
    def __init__(self, model_dir: Path = Path('models'), source: str = 'csv', **source_kwargs):
        """
        Initialize monitor.
        
        Args:
            model_dir: Directory with trained models
            source: Data source ('mt5', 'yfinance', 'csv')
            **source_kwargs: Arguments for data source
        """
        self.predictor = ModelPredictor(model_dir=model_dir)
        self.source = source
        self.data_source = self._init_data_source(source, source_kwargs)
        
        self.lookback_bars = 100
        self.lookback_data = None
        self.predictions = []
        self.signals = []
        
        logger.info(f"Monitor initialized with {source} data source")
        logger.info(f"Model: {self.predictor.model_name}, Type: {type(self.predictor.model).__name__}")
    
    def _init_data_source(self, source: str, kwargs: Dict):
        """Initialize data source."""
        if source == 'mt5':
            if not MT5_AVAILABLE:
                raise RuntimeError("MT5 not available")
            return DataSourceMT5(kwargs['login'], kwargs['password'], kwargs['server'])
        
        elif source == 'yfinance':
            if not YFINANCE_AVAILABLE:
                raise RuntimeError("yfinance not available")
            return DataSourceYFinance()
        
        elif source == 'csv':
            data_file = kwargs.get('data_file', 'data/XAUUSD_M1_59days.csv')
            return DataSourceCSV(data_file)
        
        else:
            raise ValueError(f"Unknown source: {source}")
    
    def fetch_data(self, **kwargs) -> pd.DataFrame:
        """Fetch latest data."""
        if self.source == 'mt5':
            return self.data_source.get_candles(**kwargs)
        elif self.source == 'yfinance':
            return self.data_source.get_candles(**kwargs)
        elif self.source == 'csv':
            return self.data_source.get_candles(**kwargs)
    
    def run_single_iteration(self, symbol: str = 'XAUUSD') -> Dict:
        """Run one prediction iteration."""
        # Fetch data
        df = self.fetch_data(n_candles=self.lookback_bars)
        
        if df is None or len(df) == 0:
            logger.warning("No data fetched")
            return None
        
        # Make prediction
        result = self.predictor.predict(df)
        pred = result['predictions'][-1]
        close = result['close'][-1]
        timestamp = df['time'].iloc[-1]
        
        # Generate signal
        if pred > 0.0001:  # Threshold for BUY
            signal = 'BUY'
        elif pred < -0.0001:  # Threshold for SELL
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        result_dict = {
            'timestamp': timestamp,
            'close': float(close),
            'prediction': float(pred),
            'signal': signal,
            'bars_processed': len(df),
        }
        
        return result_dict
    
    def run_continuous(self, interval_seconds: int = 60, max_iterations: int = None, symbol: str = 'XAUUSD'):
        """
        Run continuous monitoring loop.
        
        Args:
            interval_seconds: Wait time between iterations
            max_iterations: Max iterations (None = infinite)
            symbol: Trading symbol
        """
        import time
        
        logger.info(f"Starting continuous monitoring for {symbol}")
        logger.info(f"Interval: {interval_seconds}s, Max iterations: {max_iterations}")
        
        iteration = 0
        try:
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {iteration}")
                logger.info(f"{'='*60}")
                
                result = self.run_single_iteration(symbol)
                
                if result:
                    self.predictions.append(result)
                    self.signals.append(result['signal'])
                    
                    # Display results
                    print(f"\n📊 {result['timestamp']}")
                    print(f"   Close: ${result['close']:.2f}")
                    print(f"   Prediction: {result['prediction']:.2e}")
                    print(f"   Signal: {result['signal']}")
                    
                    # Log to file
                    self._log_result(result)
                
                # Wait before next iteration
                if max_iterations is None or iteration < max_iterations:
                    logger.info(f"Waiting {interval_seconds}s until next update...")
                    time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("\n\nMonitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
        finally:
            self._print_summary()
            if hasattr(self.data_source, 'disconnect'):
                self.data_source.disconnect()
    
    def _log_result(self, result: Dict):
        """Save result to log file."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / 'realtime_predictions.jsonl'
        with open(log_file, 'a') as f:
            f.write(json.dumps({**result, 'timestamp': str(result['timestamp'])}) + '\n')
    
    def _print_summary(self):
        """Print monitoring summary."""
        if not self.signals:
            return
        
        print(f"\n\n{'='*60}")
        print("📈 MONITORING SUMMARY")
        print(f"{'='*60}")
        print(f"Total Iterations: {len(self.signals)}")
        print(f"Buy Signals: {self.signals.count('BUY')}")
        print(f"Sell Signals: {self.signals.count('SELL')}")
        print(f"Hold Signals: {self.signals.count('HOLD')}")
        
        if self.predictions:
            preds = np.array([p['prediction'] for p in self.predictions])
            print(f"\nPrediction Stats:")
            print(f"  Mean: {preds.mean():.2e}")
            print(f"  Std: {preds.std():.2e}")
            print(f"  Min: {preds.min():.2e}")
            print(f"  Max: {preds.max():.2e}")
        
        print(f"\nLogs saved to: logs/realtime_predictions.jsonl")


def main():
    """Run real-time monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time market monitoring with ML predictions")
    parser.add_argument("--source", choices=['mt5', 'yfinance', 'csv'], default='csv',
                       help="Data source")
    parser.add_argument("--login", type=int, help="MT5 login")
    parser.add_argument("--password", type=str, help="MT5 password")
    parser.add_argument("--server", type=str, help="MT5 server")
    parser.add_argument("--symbol", type=str, default='XAUUSD', help="Trading symbol")
    parser.add_argument("--data-file", type=str, default='data/XAUUSD_M1_59days.csv',
                       help="CSV data file (for csv source)")
    parser.add_argument("--interval", type=float, default=1, help="Monitoring interval in seconds (for demo)")
    parser.add_argument("--iterations", type=int, help="Max iterations (default: infinite)")
    parser.add_argument("--model-dir", type=str, default="models", help="Model directory")
    
    args = parser.parse_args()
    
    try:
        # Prepare data source kwargs
        source_kwargs = {}
        if args.source == 'mt5':
            if not all([args.login, args.password, args.server]):
                print("Error: --login, --password, --server required for MT5")
                return
            source_kwargs = {'login': args.login, 'password': args.password, 'server': args.server}
        elif args.source == 'csv':
            source_kwargs = {'data_file': args.data_file}
        
        # Initialize monitor
        monitor = RealTimeMonitor(
            model_dir=args.model_dir,
            source=args.source,
            **source_kwargs
        )
        
        # Run monitoring
        monitor.run_continuous(
            interval_seconds=args.interval,
            max_iterations=args.iterations,
            symbol=args.symbol
        )
    
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}", exc_info=True)


if __name__ == "__main__":
    main()
