#!/usr/bin/env python3
"""
MT5 integration for real-time inference and trade execution.

Connects to MetaTrader 5, fetches live market data, runs inference,
and executes trades based on predictions.

Requires: MetaTrader 5 terminal running, metatrader5 Python package

Usage:
    python mt5_integration.py --symbol GOLD --timeframe M1 --mode paper
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from inference import ModelPredictor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('mt5_integration')

# Optional MT5 import
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 not installed. Install: pip install metatrader5")


class MT5Connection:
    """Manage MT5 connection and data retrieval."""
    
    def __init__(self, login: int, password: str, server: str):
        """
        Connect to MT5 terminal.
        
        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 server name
        """
        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 not available")
        
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        
        self.connect()
    
    def connect(self):
        """Establish connection to MT5."""
        if mt5.initialize(login=self.login, password=self.password, server=self.server):
            self.connected = True
            logger.info(f"Connected to MT5: {self.server}")
            
            # Get account info
            acc_info = mt5.account_info()
            if acc_info:
                logger.info(f"Account: {acc_info.login}, Balance: {acc_info.balance}")
        else:
            raise ConnectionError(f"Failed to connect to MT5: {mt5.last_error()}")
    
    def disconnect(self):
        """Close MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def get_candles(self, symbol: str, timeframe: int, n_candles: int = 100) -> pd.DataFrame:
        """
        Fetch OHLC candles from MT5.
        
        Args:
            symbol: Trading symbol (e.g., 'XAUUSD')
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_M1)
            n_candles: Number of candles to fetch
            
        Returns:
            DataFrame with OHLC data
        """
        if not self.connected:
            raise RuntimeError("Not connected to MT5")
        
        ticks = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
        
        if ticks is None:
            logger.error(f"Failed to fetch {symbol} {timeframe}: {mt5.last_error()}")
            return None
        
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    
    def place_order(self, symbol: str, order_type: str, volume: float, 
                   price: Optional[float] = None, sl: Optional[float] = None, 
                   tp: Optional[float] = None, comment: str = "") -> int:
        """
        Place a market or pending order.
        
        Args:
            symbol: Trading symbol
            order_type: 'BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT'
            volume: Order volume in lots
            price: Order price (for pending orders)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Ticket number or None if failed
        """
        if not self.connected:
            raise RuntimeError("Not connected to MT5")
        
        # Map order types
        type_map = {
            'BUY': mt5.ORDER_TYPE_BUY,
            'SELL': mt5.ORDER_TYPE_SELL,
            'BUY_LIMIT': mt5.ORDER_TYPE_BUY_LIMIT,
            'SELL_LIMIT': mt5.ORDER_TYPE_SELL_LIMIT,
        }
        
        if order_type not in type_map:
            logger.error(f"Unknown order type: {order_type}")
            return None
        
        # Get current price for market orders
        if price is None:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None
            price = tick.bid if order_type in ['SELL', 'SELL_LIMIT'] else tick.ask
        
        # Create request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": type_map[order_type],
            "price": price,
            "sl": sl or 0.0,
            "tp": tp or 0.0,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Order placed: {symbol} {order_type} {volume} lot(s), ticket: {result.order}")
            return result.order
        else:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return None
    
    def close_position(self, symbol: str) -> bool:
        """Close open position for symbol."""
        # Implementation would query positions and close them
        logger.info(f"Closing position for {symbol}")
        return True


class TradingBot:
    """Autonomous trading bot using ML predictions."""
    
    def __init__(self, model_dir: Path = Path('models'), 
                 login: int = None, password: str = None, server: str = None):
        """
        Initialize trading bot.
        
        Args:
            model_dir: Directory with trained models
            login, password, server: MT5 credentials (optional for backtesting)
        """
        self.predictor = ModelPredictor(model_dir=model_dir)
        self.mt5 = None
        
        if login and password and server:
            self.mt5 = MT5Connection(login, password, server)
        else:
            logger.info("MT5 connection not configured - bot in simulation mode")
        
        self.lookback_bars = 100  # For feature computation
        self.min_prediction_strength = 0.0  # Minimum prediction magnitude to trade
        self.position_size = 0.1  # In lots
    
    def fetch_market_data(self, symbol: str = 'XAUUSD', timeframe: int = None) -> pd.DataFrame:
        """Fetch recent market data."""
        if self.mt5 is None:
            raise RuntimeError("MT5 not connected")
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M1
        
        df = self.mt5.get_candles(symbol, timeframe, self.lookback_bars)
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        """Generate trading signals from latest bar."""
        if df is None or len(df) == 0:
            return {'signal': None, 'strength': 0}
        
        # Get prediction for latest bar
        result = self.predictor.predict(df)
        pred = result['predictions'][-1]
        
        # Signal generation logic
        # Positive prediction -> BUY, Negative -> SELL
        if abs(pred) < self.min_prediction_strength:
            signal = 'HOLD'
        elif pred > 0:
            signal = 'BUY'
        else:
            signal = 'SELL'
        
        return {
            'signal': signal,
            'prediction': float(pred),
            'timestamp': pd.Timestamp.now(),
            'close': float(df['close'].iloc[-1]),
        }
    
    def execute_trade(self, signal: Dict, symbol: str = 'XAUUSD'):
        """Execute trade based on signal."""
        if signal['signal'] == 'HOLD':
            logger.info(f"No trade signal (prediction: {signal['prediction']:.2e})")
            return None
        
        if self.mt5 is None:
            logger.info(f"[SIMULATION] {signal['signal']} {symbol} at {signal['close']}")
            return None
        
        order_type = signal['signal']
        ticket = self.mt5.place_order(
            symbol=symbol,
            order_type=order_type,
            volume=self.position_size,
            comment=f"ML signal: {signal['prediction']:.2e}"
        )
        
        return ticket
    
    def run_realtime_loop(self, symbol: str = 'XAUUSD', interval_seconds: int = 60):
        """Run continuous trading loop (requires MT5)."""
        if self.mt5 is None:
            logger.error("MT5 not connected - cannot run real-time loop")
            return
        
        logger.info(f"Starting real-time trading loop for {symbol}...")
        
        try:
            while True:
                # Fetch data
                df = self.fetch_market_data(symbol)
                if df is None:
                    logger.warning("Failed to fetch data, retrying...")
                    continue
                
                # Generate signals
                signal = self.generate_signals(df)
                logger.info(f"Signal: {signal['signal']}, Pred: {signal['prediction']:.2e}")
                
                # Execute if signal
                if signal['signal'] != 'HOLD':
                    self.execute_trade(signal, symbol)
                
                # Wait for next interval
                import time
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("Stopping trading loop...")
        finally:
            if self.mt5:
                self.mt5.disconnect()
    
    def backtest_day(self, symbol: str = 'XAUUSD', date_str: str = None) -> Dict:
        """Backtest on historical data for a specific day."""
        if self.mt5 is None:
            logger.error("MT5 not connected")
            return None
        
        logger.info(f"Backtesting {symbol} for {date_str}...")
        
        # Implementation would fetch historical data and simulate trades
        return {
            'symbol': symbol,
            'date': date_str,
            'trades': [],
            'pnl': 0,
        }


def main():
    """Demo trading bot."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MT5 Trading Bot")
    parser.add_argument("--mode", choices=['paper', 'backtest', 'live'], default='paper',
                       help="Trading mode")
    parser.add_argument("--symbol", type=str, default='XAUUSD', help="Trading symbol")
    parser.add_argument("--login", type=int, help="MT5 login")
    parser.add_argument("--password", type=str, help="MT5 password")
    parser.add_argument("--server", type=str, help="MT5 server")
    parser.add_argument("--model-dir", type=str, default="models", help="Model directory")
    
    args = parser.parse_args()
    
    # Initialize bot
    try:
        if args.mode == 'live':
            if not all([args.login, args.password, args.server]):
                print("Error: --login, --password, --server required for live mode")
                return
            bot = TradingBot(args.model_dir, args.login, args.password, args.server)
        else:
            bot = TradingBot(args.model_dir)
        
        # Show model info
        info = bot.predictor.get_model_info()
        print(f"\n=== Model Info ===")
        print(f"Type: {info['model_type']}")
        if 'test_metrics' in info:
            print(f"Test R2: {info['test_metrics']['r2']:.4f}")
        
        # Run mode
        if args.mode == 'paper':
            print(f"\n[PAPER MODE] Bot ready for {args.symbol}")
            print("Demo: would fetch data and generate signals...")
        elif args.mode == 'live':
            print(f"\n[LIVE MODE] Starting real-time trading for {args.symbol}...")
            bot.run_realtime_loop(args.symbol)
    
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")


if __name__ == "__main__":
    main()
