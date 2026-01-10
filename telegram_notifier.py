import requests
import json
from datetime import datetime

class TelegramNotifier:
    def __init__(self, bot_token, chat_ids):  # chat_ids: list or str
        self.bot_token = bot_token
        if isinstance(chat_ids, str):
            self.chat_ids = [chat_ids]
        else:
            self.chat_ids = chat_ids
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message, parse_mode="HTML"):
        """Kirim ke SEMUA chat_id dalam list"""
        success = True
        for chat_id in self.chat_ids:
            try:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode
                }
                response = requests.post(url, json=data, timeout=10)
                if response.status_code != 200:
                    print(f"Telegram error ({chat_id}): {response.text}")
                    success = False
            except Exception as e:
                print(f"Failed to send Telegram ({chat_id}): {e}")
                success = False
        return success
    
    def send_startup(self):
        """Bot startup notification"""
        message = """
🤖 <b>AVENTA BOT STARTED</b>

Status: LIVE & MONITORING
Time: {}
Strategy: SMA 5/50 + RSI 20

Ready to trade!  🚀
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return self.send_message(message)
    
    def send_trade_open(self, trade_type, entry, sl, tp, rsi, atr, session):
        """Trade execution alert"""
        
        risk = abs(entry - sl)
        reward = abs(entry - tp)
        rr_ratio = reward / risk if risk > 0 else 0
        
        emoji = "🟢" if trade_type == "LONG" else "🔴"
        
        message = f"""
{emoji} <b>TRADE OPENED</b>

Direction: {trade_type}
Entry: {entry:.2f}
Stop Loss: {sl:.2f} (Risk: {risk:.2f})
Take Profit: {tp:.2f} (Reward: {reward:.2f})
R:R Ratio: 1:{rr_ratio:.2f}

RSI: {rsi:.1f}
ATR: {atr:.2f}
Session: {session}
Time: {datetime.now().strftime('%H:%M:%S')}

Position is OPEN ⏳
"""
        return self.send_message(message)
    
    def send_trade_close(self, trade_type, entry, exit_price, pnl, reason):
        """Position close alert"""
        
        emoji = "✅" if pnl > 0 else "❌"
        status = "WIN" if pnl > 0 else "LOSS"
        
        message = f"""
{emoji} <b>POSITION CLOSED - {status}</b>

Direction: {trade_type}
Entry: {entry:.2f}
Exit: {exit_price:.2f}
P&L: ${pnl:.2f}
Reason: {reason}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        return self.send_message(message)
    
    def send_daily_summary(self, trades, wins, losses, pnl, balance):
        """Daily performance summary"""
        
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        emoji = "📈" if pnl > 0 else "📉"
        
        message = f"""
{emoji} <b>DAILY SUMMARY</b>

Date: {datetime.now().strftime('%Y-%m-%d')}

Total Trades: {trades}
Wins: {wins} ({win_rate:.1f}%)
Losses: {losses}
Net P&L: ${pnl:.2f}

Balance: ${balance:.2f}
Bot Status:  ACTIVE ✅
"""
        return self.send_message(message)
    
    def send_alert(self, title, message):
        """Generic alert"""
        full_message = f"""
⚠️ <b>{title}</b>

{message}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(full_message)
    
    def send_error(self, error_msg):
        """Error notification"""
        message = f"""
🚨 <b>BOT ERROR</b>

{error_msg}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check bot status! 
"""
        return self.send_message(message)

# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_telegram():
    """Test Telegram notifications"""
    print("=" * 70)
    print("📱 TELEGRAM NOTIFICATION TEST")
    print("=" * 70)
    
    # ⚠️ UPDATE WITH YOUR VALUES! 
    BOT_TOKEN = "8405053497:AAF48BoKZ75M0IVK_2Mj5jlk1UgEMYBKJM4"  # ✅
    CHAT_ID = "7521820149"  # ✅
    
    print(f"\nBot Token: {BOT_TOKEN[: 20]}...")
    print(f"Chat ID: {CHAT_ID}")
    
    # Create notifier
    notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)
    
    # Test 1: Simple message
    print("\n[1/5] Testing simple message...")
    if notifier.send_message("🤖 Test message from trading bot! "):
        print("✅ Simple message sent!")
    else:
        print("❌ Failed to send simple message")
        return
    
    # Test 2: Startup notification
    print("\n[2/5] Testing startup notification...")
    if notifier.send_startup():
        print("✅ Startup notification sent!")
    else:
        print("❌ Failed to send startup")
    
    # Test 3: Trade open
    print("\n[3/5] Testing trade open notification...")
    if notifier.send_trade_open(
        trade_type="LONG",
        entry=4450.50,
        sl=4440.00,
        tp=4470.00,
        rsi=55.5,
        atr=1.5,
        session="NY"
    ):
        print("✅ Trade open notification sent!")
    else:
        print("❌ Failed to send trade open")
    
    # Test 4: Trade close
    print("\n[4/5] Testing trade close notification...")
    if notifier.send_trade_close(
        trade_type="LONG",
        entry=4450.50,
        exit_price=4470.00,
        pnl=19.50,
        reason="Take Profit"
    ):
        print("✅ Trade close notification sent!")
    else:
        print("❌ Failed to send trade close")
    
    # Test 5: Daily summary
    print("\n[5/5] Testing daily summary...")
    if notifier.send_daily_summary(
        trades=10,
        wins=6,
        losses=4,
        pnl=25.50,
        balance=1075.50
    ):
        print("✅ Daily summary sent!")
    else:
        print("❌ Failed to send daily summary")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETE!")
    print("Check your Telegram for 5 messages")
    print("=" * 70)

if __name__ == "__main__":
    test_telegram()