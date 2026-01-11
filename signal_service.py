"""
Signal Service for broadcasting trading signals via Telegram.
Dedicated for commercial signal distribution with TP/SL recommendations.
"""

import logging
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class SignalBroadcaster:
    """Broadcasts trading signals to subscriber list with TP/SL recommendations."""
    
    def __init__(self, bot_token: str, history_file: str = "logs/signal_history.csv"):
        """Initialize signal broadcaster.
        
        Args:
            bot_token: Telegram bot token for signal service
            history_file: Path to CSV file for logging signal history
        """
        self.bot_token = bot_token
        self.history_file = Path(history_file)
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Create history CSV file if not exists."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_file.exists():
            with open(self.history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'symbol', 'signal_type', 'price', 'ml_score',
                    'tp_price', 'sl_price', 'tp_percent', 'sl_percent',
                    'chat_ids_sent', 'status', 'error_message'
                ])
    
    def format_signal_minimal(self, symbol: str, signal_type: str, price: float, 
                             ml_score: float, tp_price: float, sl_price: float) -> str:
        """Format signal as minimal message.
        
        Example: 🟢 BUY XAUUSD @ 2024.50 | TP: 2050.00 | SL: 2020.00 | ML: 0.85
        """
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        return (
            f"{emoji} <b>{signal_type}</b> {symbol}\n"
            f"Entry: ${price:.2f}\n"
            f"TP: ${tp_price:.2f}\n"
            f"SL: ${sl_price:.2f}\n"
            f"ML Score: {ml_score:.4f}"
        )
    
    def format_signal_detailed(self, symbol: str, signal_type: str, price: float,
                              ml_score: float, tp_price: float, sl_price: float,
                              tp_percent: float, sl_percent: float,
                              sma_fast: Optional[float] = None,
                              sma_slow: Optional[float] = None,
                              rsi: Optional[float] = None) -> str:
        """Format signal with detailed technical indicators."""
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        message = (
            f"{emoji} <b>SIGNAL TRADING AVENTA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Signal:</b> {signal_type} {symbol}\n"
            f"<b>Entry Price:</b> ${price:.2f}\n"
            f"<b>Take Profit:</b> ${tp_price:.2f} (+{tp_percent:.2f}%)\n"
            f"<b>Stop Loss:</b> ${sl_price:.2f} (-{sl_percent:.2f}%)\n"
            f"\n<b>Risk/Reward Ratio:</b> {(tp_percent/sl_percent):.2f}:1\n"
            f"<b>ML Confidence:</b> {ml_score*100:.1f}%\n"
        )
        
        if sma_fast and sma_slow:
            message += f"\n<b>Technical Indicators:</b>\n"
            message += f"SMA Fast: ${sma_fast:.2f}\n"
            message += f"SMA Slow: ${sma_slow:.2f}\n"
        
        if rsi:
            message += f"RSI: {rsi:.1f}\n"
        
        message += (
            f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Aventa Trading Signals</i>\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        return message
    
    def send_signal(self, 
                   symbol: str,
                   signal_type: str,  # BUY or SELL
                   price: float,
                   ml_score: float,
                   tp_price: float,
                   sl_price: float,
                   tp_percent: float,
                   sl_percent: float,
                   chat_ids: List[str],
                   template: str = "detailed",
                   **kwargs) -> Dict:
        """Send signal to all subscribers.
        
        Args:
            symbol: Trading symbol (e.g., XAUUSD)
            signal_type: BUY or SELL
            price: Current entry price
            ml_score: ML model confidence score
            tp_price: Take profit price
            sl_price: Stop loss price
            tp_percent: TP as percentage
            sl_percent: SL as percentage
            chat_ids: List of telegram chat IDs to send to
            template: Format template (minimal/detailed)
            **kwargs: Additional data (sma_fast, sma_slow, rsi, etc.)
        
        Returns:
            Dict with status, sent_count, failed_count, errors
        """
        try:
            # Format message
            if template == "minimal":
                message = self.format_signal_minimal(symbol, signal_type, price, ml_score, tp_price, sl_price)
            else:  # detailed
                message = self.format_signal_detailed(
                    symbol, signal_type, price, ml_score, tp_price, sl_price,
                    tp_percent, sl_percent,
                    kwargs.get('sma_fast'),
                    kwargs.get('sma_slow'),
                    kwargs.get('rsi')
                )
            
            # Send to all subscribers
            sent_count = 0
            failed_count = 0
            failed_ids = []
            
            for chat_id in chat_ids:
                try:
                    response = requests.post(
                        self.api_url,
                        json={
                            'chat_id': chat_id,
                            'text': message,
                            'parse_mode': 'HTML'
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        sent_count += 1
                        logger.info(f"Signal sent to {chat_id}: {symbol} {signal_type}")
                    else:
                        failed_count += 1
                        failed_ids.append(chat_id)
                        logger.warning(f"Failed to send to {chat_id}: {response.text}")
                
                except Exception as e:
                    failed_count += 1
                    failed_ids.append(chat_id)
                    logger.error(f"Error sending to {chat_id}: {e}")
            
            # Log to history
            self._log_signal(
                symbol, signal_type, price, ml_score, tp_price, sl_price,
                tp_percent, sl_percent, sent_count, failed_count, failed_ids
            )
            
            status = "success" if failed_count == 0 else "partial"
            return {
                'status': status,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total': len(chat_ids),
                'failed_ids': failed_ids
            }
        
        except Exception as e:
            logger.error(f"Error in send_signal: {e}")
            self._log_signal(
                symbol, signal_type, price, ml_score, tp_price, sl_price,
                tp_percent, sl_percent, 0, len(chat_ids), chat_ids,
                error_msg=str(e)
            )
            return {
                'status': 'failed',
                'error': str(e),
                'sent_count': 0,
                'failed_count': len(chat_ids)
            }
    
    def _log_signal(self, symbol: str, signal_type: str, price: float, ml_score: float,
                   tp_price: float, sl_price: float, tp_percent: float, sl_percent: float,
                   sent_count: int, failed_count: int, chat_ids_sent: List[str] = None,
                   error_msg: str = ""):
        """Log signal to CSV history."""
        try:
            with open(self.history_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    symbol,
                    signal_type,
                    f"{price:.2f}",
                    f"{ml_score:.6f}",
                    f"{tp_price:.2f}",
                    f"{sl_price:.2f}",
                    f"{tp_percent:.2f}",
                    f"{sl_percent:.2f}",
                    ",".join(chat_ids_sent) if chat_ids_sent else "",
                    "success" if failed_count == 0 else "partial",
                    error_msg
                ])
        except Exception as e:
            logger.error(f"Error logging signal: {e}")
    
    def get_signal_history(self, limit: int = 50) -> List[Dict]:
        """Get recent signals from history.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of signal records
        """
        history = []
        try:
            with open(self.history_file, 'r') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    history.insert(0, row)  # Reverse order (newest first)
        except Exception as e:
            logger.error(f"Error reading signal history: {e}")
        
        return history
    
    def get_statistics(self) -> Dict:
        """Get signal statistics from history."""
        try:
            with open(self.history_file, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
            
            if not records:
                return {
                    'total_signals': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'success_rate': 0,
                    'total_sent': 0,
                    'total_failed': 0
                }
            
            total = len(records)
            buys = sum(1 for r in records if r['signal_type'] == 'BUY')
            sells = sum(1 for r in records if r['signal_type'] == 'SELL')
            successes = sum(1 for r in records if r['status'] == 'success')
            
            total_sent = sum(int(r.get('chat_ids_sent', '').count(',') + 1) 
                            for r in records if r.get('chat_ids_sent'))
            total_failed = sum(int(r.get('error_message', '') != '') for r in records)
            
            return {
                'total_signals': total,
                'buy_signals': buys,
                'sell_signals': sells,
                'success_rate': (successes / total * 100) if total > 0 else 0,
                'total_sent': total_sent,
                'total_failed': total_failed
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
