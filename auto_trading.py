from logging import info
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, time
import time as time_module
import yaml
import json
import os
from pathlib import Path
from telegram_notifier import TelegramNotifier
from analytics import TradingAnalytics
from live_analytics import LivePerformanceTracker

print("=" * 80)
print("🤖 AUTOMATED TRADING BOT - OPTIMIZED GOLD STRATEGY")
print("=" * 80)
print("⚠️  WARNING: This bot will automatically execute trades!")
print("⚠️  Ensure you are using DEMO account for initial testing!")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================

class BotConfig:
    """Configuration for trading bot"""
    
    # MT5 Connection
    MT5_PATH = "C:\\Program Files\\XM Global MT5\\terminal64.exe"
    ACCOUNT = 11260163
    PASSWORD = 'Klapaucius82#'
    SERVER = 'VantageInternational-Demo'
    SYMBOL = 'BTCUSD'
    
    # Optimized Strategy Parameters
    SMA_FAST = 5
    SMA_SLOW = 50
    RSI_PERIOD = 20
    ATR_PERIOD = 14
    ATR_SL_MULT = 2.5
    ATR_TP_MULT = 4.0
    
    # Risk Management
    LOT_SIZE = 0.01
    MAX_POSITIONS = 1
    MAX_DAILY_TRADES = 15
    MAX_DAILY_LOSS = 50.0
    MAX_SPREAD = 30
    
    # Session Filtering
    TRADE_LONDON = True
    TRADE_NY = True
    TRADE_ASIAN = False
    
    LONDON_START = time(8, 0)
    LONDON_END = time(16, 0)
    NY_START = time(13, 0)
    NY_END = time(20, 0)
    ASIAN_START = time(0, 0)
    ASIAN_END = time(8, 0)
    
    # Bot Settings
    CHECK_INTERVAL = 1
    DATA_BARS = 100
    TIMEFRAME = mt5.TIMEFRAME_M1
    
    # Logging
    LOG_FILE = 'bot_trades.csv'
    STATE_FILE = 'bot_state.json'
    
    # Telegram Notifications
    TELEGRAM_ENABLED = True
    TELEGRAM_BOT_TOKEN = "8405053497:AAF48BoKZ75M0IVK_2Mj5jlk1UgEMYBKJM4"
    TELEGRAM_CHAT_ID = ["7521820149", "7567546279", "8076781246", "850240757"]
    
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_rsi(closes, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(closes)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(closes)
    rsi[:period] = 100.- 100./(1.+rs) if rs != 0 else 50

    for i in range(period, len(closes)):
        delta = deltas[i-1]
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else 0
        rsi[i] = 100.- 100./(1.+rs) if rs != 0 else 50
    return rsi

def get_current_session():
    """Determine current trading session (GMT)"""
    now_gmt = datetime.utcnow().time()
    
    if BotConfig.LONDON_START <= now_gmt < BotConfig.LONDON_END:
        return "LONDON"
    elif BotConfig.NY_START <= now_gmt < BotConfig.NY_END:  
        return "NY"
    elif BotConfig.ASIAN_START <= now_gmt < BotConfig.ASIAN_END:  
        return "ASIAN"
    else:
        return "ASIAN"

def is_trading_allowed():
    """Check if trading is allowed in current session"""
    session = get_current_session()
    
    if session == "LONDON" and BotConfig.TRADE_LONDON:
        return True
    elif session == "NY" and BotConfig.TRADE_NY:  
        return True
    elif session == "ASIAN" and BotConfig.TRADE_ASIAN:  
        return True
    else:  
        return False

def log_trade(trade_data):
    """Log trade to CSV file"""
    df = pd.DataFrame([trade_data])
    
    if os.path.exists(BotConfig.LOG_FILE):
        df.to_csv(BotConfig.LOG_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(BotConfig.LOG_FILE, mode='w', header=True, index=False)

def save_bot_state(state):
    """Save bot state to file"""
    with open(BotConfig.STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, default=str)

def load_bot_state():
    """Load bot state from file"""
    if os.path.exists(BotConfig.STATE_FILE):
        with open(BotConfig.STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'daily_trades': 0,
        'daily_pnl': 0.0,
        'last_trade_date': None,
        'total_trades': 0,
        'margin_status': None
    }

# ============================================================================
# TRADING BOT CLASS
# ============================================================================

class AutoTradingBot: 

    def format_title(self, title):
        """Standard notification title with symbol"""
        symbol = self.config.SYMBOL
        return f"{title} — <b>{symbol}</b>"


    def show_analytics(self):
        """Display trading analytics"""
        analytics = TradingAnalytics(self.config.LOG_FILE)
        analytics.print_dashboard()

    def show_live_performance(self):
        """Display live performance"""
        if self.mt5_connected:
            info = mt5.account_info()
            self.live_tracker.update(info)
            self.live_tracker.print_live_stats(info)
    
    def __init__(self):
        self.config = BotConfig()
        self.state = load_bot_state()
        self.running = False
        self.mt5_connected = False
        
        # Initialize performance tracker
        self.live_tracker = LivePerformanceTracker()
        
        # Track bot's own orders and notified deals
        self.bot_order_ids = set()  # ← This starts empty, but...
        self.notified_deals = set()
        
        # Initialize Telegram notifier
        if self.config.TELEGRAM_ENABLED:
            try:
                self.telegram = TelegramNotifier(
                    self.config.TELEGRAM_BOT_TOKEN,
                    self.config.TELEGRAM_CHAT_ID
                )
                print("✅ Telegram notifier initialized")
            except Exception as e:  
                print(f"⚠️ Telegram initialization failed: {e}")
                self.telegram = None
        else:
            self.telegram = None
        
    def connect_mt5(self):
        """Connect to MT5"""
        print(f"\n[CONNECT] Initializing MT5...")
        
        if not mt5.initialize(self.config.MT5_PATH):
            print(f"❌ MT5 initialize failed:  {mt5.last_error()}")
            return False
        
        if not mt5.login(self.config.ACCOUNT, password=self.config.PASSWORD, 
                        server=self.config.SERVER):
            print(f"❌ MT5 login failed: {mt5.last_error()}")
            return False
        
        info = mt5.account_info()
        print(f"✅ Connected to MT5")
        print(f"   Account: {info.login} ({info.name})")
        print(f"   Balance: ${info.balance:.2f}")
        print(f"   Server: {info.server}")
        
        self.mt5_connected = True

        # Initialize live performance tracker
        info = mt5.account_info()
        self.live_tracker.initialize(info)

        return True

    
    def disconnect_mt5(self):
        """Disconnect from MT5"""
        if self.mt5_connected:
            mt5.shutdown()
            self.mt5_connected = False
            print(f"\n[DISCONNECT] MT5 connection closed")
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        today = datetime.now().date().isoformat()
        if self.state.get('last_trade_date') != today:
            self.state['daily_trades'] = 0
            self.state['daily_pnl'] = 0.0
            self.state['last_trade_date'] = today
            save_bot_state(self.state)
            print(f"[RESET] Daily statistics reset for {today}")
    
    def check_risk_limits(self):
        """Check if risk limits are exceeded"""
        self.reset_daily_stats()
        
        # Check max daily trades
        if self.state['daily_trades'] >= self.config.MAX_DAILY_TRADES:
            return False, f"Max daily trades reached ({self.state['daily_trades']})"
        
        # Check max daily loss
        if self.state['daily_pnl'] <= -self.config.MAX_DAILY_LOSS:
            return False, f"Max daily loss reached (${self.state['daily_pnl']:.2f})"
        
        # Check max positions
        positions = mt5.positions_get(symbol=self.config.SYMBOL)
        if positions and len(positions) >= self.config.MAX_POSITIONS: 
            return False, f"Max positions reached ({len(positions)})"
        
        return True, "OK"
    
    def get_market_data(self):
        """Fetch and process market data"""
        rates = mt5.copy_rates_from_pos(self.config.SYMBOL, self.config.TIMEFRAME, 
                                        0, self.config.DATA_BARS)
        
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate indicators
        df['sma_fast'] = df['close'].rolling(window=self.config.SMA_FAST).mean()
        df['sma_slow'] = df['close'].rolling(window=self.config.SMA_SLOW).mean()
        df['rsi'] = calculate_rsi(df['close'].values, self.config.RSI_PERIOD)
        
        # Calculate ATR
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=self.config.ATR_PERIOD).mean()
        
        df = df.dropna()
        return df
    
    def check_spread(self):
        """Check if current spread is acceptable"""
        symbol_info = mt5.symbol_info(self.config.SYMBOL)
        if symbol_info is None:
            return False, 999
        
        spread = symbol_info.spread
        if spread > self.config.MAX_SPREAD:
            return False, spread
        
        return True, spread
    
    def detect_signal(self, df):
        """Detect trading signal using both ML predictions and technical indicators"""
        if len(df) < 2:
            return None
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Try to load ML model predictions for additional signal confirmation
        ml_prediction = None
        try:
            from inference import ModelPredictor
            from pathlib import Path
            
            predictor = ModelPredictor(model_dir=str(Path('models')))
            result = predictor.predict(df.tail(10))  # Use last 10 bars for prediction
            if result and 'predictions' in result and len(result['predictions']) > 0:
                ml_prediction = result['predictions'][-1]  # Last prediction
        except Exception as e:
            pass  # Continue with TA signals only if ML model fails
        
        # Technical Analysis: LONG signal (SMA crossover + RSI confirmation)
        ta_long_signal = (previous['sma_fast'] <= previous['sma_slow'] and 
                         current['sma_fast'] > current['sma_slow'] and 
                         current['rsi'] < 70)
        
        # Technical Analysis: SHORT signal (SMA crossover + RSI confirmation)
        ta_short_signal = (previous['sma_fast'] >= previous['sma_slow'] and 
                          current['sma_fast'] < current['sma_slow'] and 
                          current['rsi'] > 30)
        
        # Combine ML + TA signals
        # If ML model available: require both TA crossover AND positive ML prediction
        # If no ML model: use TA signals only
        
        if ta_long_signal:
            ml_confirms_long = (ml_prediction is None) or (ml_prediction > 0.0001)  # TA-only OR (TA + ML bullish)
            if ml_confirms_long:
                return {
                    'type':  'LONG',
                    'entry':  current['close'],
                    'sl': current['close'] - (current['atr'] * self.config.ATR_SL_MULT),
                    'tp': current['close'] + (current['atr'] * self.config.ATR_TP_MULT),
                    'atr': current['atr'],
                    'rsi': current['rsi'],
                    'ml_score': ml_prediction if ml_prediction else 0.0
                }
        
        if ta_short_signal:
            ml_confirms_short = (ml_prediction is None) or (ml_prediction < -0.0001)  # TA-only OR (TA + ML bearish)
            if ml_confirms_short:
                return {
                    'type': 'SHORT',
                    'entry':  current['close'],
                    'sl': current['close'] + (current['atr'] * self.config.ATR_SL_MULT),
                    'tp': current['close'] - (current['atr'] * self.config.ATR_TP_MULT),
                    'atr':  current['atr'],
                    'rsi': current['rsi'],
                    'ml_score': ml_prediction if ml_prediction else 0.0
                }
        
        return None
    
    def execute_trade(self, signal):
        """Execute trade on MT5"""
        symbol_info = mt5.symbol_info(self.config.SYMBOL)
        if symbol_info is None:
            print(f"❌ Symbol {self.config.SYMBOL} not found")
            return False
        
        # Prepare request
        if signal['type'] == 'LONG':
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(self.config.SYMBOL).ask
        else:  
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(self.config.SYMBOL).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.config.SYMBOL,
            "volume": self.config.LOT_SIZE,
            "type": order_type,
            "price": price,
            "sl": signal['sl'],
            "tp": signal['tp'],
            "deviation": 20,
            "magic": 2300,
            "comment":  "AutoBot",
            "type_time":  mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            print(f"❌ Order send failed: No result")
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE: 
            print(f"❌ Order failed: {result.retcode} - {result.comment}")
            return False
        
        # Success!  
        print(f"\n{'='*80}")
        print(f"✅ TRADE EXECUTED")
        print(f"{'='*80}")
        print(f"Direction:     {signal['type']}")
        print(f"Entry:         {price:.2f}")
        print(f"Stop Loss:     {signal['sl']:.2f}")
        print(f"Take Profit:   {signal['tp']:.2f}")
        print(f"Volume:        {self.config.LOT_SIZE}")
        print(f"Order ID:       {result.order}")
        print(f"RSI:           {signal['rsi']:.1f}")
        print(f"ATR:           {signal['atr']:.2f}")
        if 'ml_score' in signal:
            print(f"ML Score:      {signal['ml_score']:.6f}")
        print(f"{'='*80}")
        
        # 🆕 FIXED: Track both order AND position tickets
        self.bot_order_ids.add(result.order)  # Track order ticket
        
        # Wait for position to open and track position ticket
        time_module.sleep(0.5)  # Small delay for MT5
        positions = mt5.positions_get(symbol=self.config.SYMBOL)
        if positions:
            for pos in positions:
                # Track ALL current position tickets (including this new one)
                self.bot_order_ids.add(pos.ticket)
                print(f"[TRACK] Position ticket {pos.ticket} added to bot tracking")
        
        # Update state
        self.state['daily_trades'] += 1
        self.state['total_trades'] += 1
        save_bot_state(self.state)
        
        # Log trade
        log_trade({
            'timestamp':  datetime.now().isoformat(),
            'type': signal['type'],
            'entry': price,
            'sl': signal['sl'],
            'tp': signal['tp'],
            'volume': self.config.LOT_SIZE,
            'order_id': result.order,
            'rsi': signal['rsi'],
            'atr': signal['atr'],
            'session': get_current_session()
        })
        
        # Send Telegram notification
        if self.telegram:
            self.telegram.send_trade_open(
                trade_type=signal['type'],
                entry=price,
                sl=signal['sl'],
                tp=signal['tp'],
                rsi=signal['rsi'],
                atr=signal['atr'],
                session=get_current_session()
            )
        
        return True
    
    def monitor_positions(self):
        """Monitor open positions"""
        positions = mt5.positions_get(symbol=self.config.SYMBOL)
        
        if not positions:
            return
        
        for pos in positions:
            pnl = pos.profit
            self.state['daily_pnl'] = self.state.get('daily_pnl', 0) + pnl
            
            direction = "LONG" if pos.type == 0 else "SHORT"
            print(f"[POSITION] {direction} | Entry: {pos.price_open:.2f} | "
                  f"Current P&L: ${pnl:.2f}", end='\r')
    
    def detect_manual_trades(self):
        """Detect manual vs other auto-bot trades"""

        info = mt5.account_info()
        if info is None or info.margin_level is None:
            return

        margin = info.margin_level

        positions = mt5.positions_get(symbol=self.config.SYMBOL)
        if not positions:
            return

        for pos in positions:

            # Skip kalau sudah diproses
            if pos.ticket in self.bot_order_ids:
                continue

            # =====================================================
            # 1️⃣ BOT INI SENDIRI (magic = 2300)
            # =====================================================
            if pos.magic == 2300:
                self.bot_order_ids.add(pos.ticket)

                direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                pnl = pos.profit  # ✅ FIX UTAMA

                title = self.format_title("🚀 BOT ENTRY")

                message = f"""
    {title}

    Entry Type: <b>{direction}</b>
    Entry Price: {pos.price_open:.2f}
    Volume: {pos.volume}
    Magic: {pos.magic}

    P&L: ${pnl:.2f}
    Margin Level: {margin:.2f}%
    Balance: ${info.balance:.2f}
    Equity: ${info.equity:.2f}
    Free Margin: ${info.margin_free:.2f}
    Time: {datetime.now().strftime('%H:%M:%S')}
    """
                self.telegram.send_message(message)

                continue


            # =====================================================
            # 2️⃣ AUTO TRADE BOT LAIN (magic ≠ 0)
            # =====================================================
            if pos.magic != 0:
                self.bot_order_ids.add(pos.ticket)

                direction = "LONG" if pos.type == 0 else "SHORT"
                pnl = pos.profit

                print(f"\n{'='*80}")
                print(f"🤖 AUTO TRADE DETECTED (OTHER BOT)")
                print(f"{'='*80}")
                print(f"Direction: {direction}")
                print(f"Entry:     {pos.price_open:.2f}")
                print(f"Volume:    {pos.volume}")
                print(f"Ticket:    {pos.ticket}")
                print(f"Magic:     {pos.magic}")
                print(f"P&L:       ${pnl:.2f}")
                print(f"{'='*80}")

                if self.telegram:
                    direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"

                    title = self.format_title("🤖 AUTO TRADE OPEN")

                    message = f"""
    {title}

    Entry Type: <b>{direction}</b>
    Entry Price: {pos.price_open:.2f}
    Volume: {pos.volume}
    
    P&L: ${pnl:.2f}
    Margin Level: {margin:.2f}%
    Balance: ${info.balance:.2f}
    Equity: ${info.equity:.2f}
    Free Margin: ${info.margin_free:.2f}
    Time: {datetime.now().strftime('%H:%M:%S')}
    """
                self.telegram.send_message(message)

                continue

            # =====================================================
            # 3️⃣ MANUAL TRADE (magic = 0)
            # =====================================================
            if pos.magic == 0:
                self.bot_order_ids.add(pos.ticket)

                direction = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                pnl = pos.profit  # ✅ FIX

                title = self.format_title("🖐️ MANUAL TRADE OPEN")

                message = f"""
    {title}

    Entry Type: <b>{direction}</b>
    Entry Price: {pos.price_open:.2f}
    Volume: {pos.volume}

    P&L: ${pnl:.2f}
    Margin Level: {margin:.2f}%
    Balance: ${info.balance:.2f}
    Equity: ${info.equity:.2f}
    Free Margin: ${info.margin_free:.2f}
    Time: {datetime.now().strftime('%H:%M:%S')}
    """
                self.telegram.send_message(message)

                continue

    
    def monitor_closed_trades(self):
        """Notify ALL closed positions (bot / other bot / manual)"""
        
        info = mt5.account_info()
        if info is None or info.margin_level is None:
            return

        margin = info.margin_level

        from_date = datetime.now().replace(hour=0, minute=0, second=0)
        deals = mt5.history_deals_get(from_date, datetime.now())

        if not deals:
            return

        for deal in deals:
            if deal.symbol != self.config.SYMBOL:
                continue

            # Hanya deal CLOSE
            if deal.entry != mt5.DEAL_ENTRY_OUT:
                continue

            deal_id = f"close_{deal.position_id}"
            if deal_id in self.notified_deals:
                continue

            self.notified_deals.add(deal_id)

            # =====================================================
            # KLASIFIKASI
            # =====================================================
            if deal.magic == 2300:
                trade_type = "BOT CLOSED"
                emoji = "🤖"
            elif deal.magic != 0:
                trade_type = "AUTO BOT CLOSED"
                emoji = "🟡"
            else:
                trade_type = "MNL CLOSED/TP/SL"
                emoji = "🖐️"

            # Direction
            direction = "LONG" if deal.type == mt5.DEAL_TYPE_SELL else "SHORT"

            pnl = deal.profit
            status = "WIN" if pnl > 0 else "LOSS"
            result_emoji = "✅" if pnl > 0 else "❌"

            # =====================================================
            # NOTIFICATION
            # =====================================================
            if self.telegram:
                direction = "BUY" if deal.type == mt5.ORDER_TYPE_BUY else "SELL"

                title = self.format_title(f"{emoji} {trade_type}")

                message = f"""
    {title} {result_emoji}

    Entry Type: <b>{direction}</b>
    Entry Price: {deal.price:.2f}
    Close Price: {deal.price:.2f}

    Volume: {deal.volume}
    P&L: ${pnl:.2f}
    Margin Level: {margin:.2f}%
    Balance: ${info.balance:.2f}
    Equity: ${info.equity:.2f}
    Free Margin: ${info.margin_free:.2f}

    Time: {datetime.now().strftime('%H:%M:%S')}
    """
            self.telegram.send_message(message)
    
    def run(self):
        """Main bot loop"""
        print(f"\n{'='*80}")
        print(f"🤖 BOT STARTING")
        print(f"{'='*80}")
        print(f"Symbol:             {self.config.SYMBOL}")
        print(f"Strategy:        SMA {self.config.SMA_FAST}/{self.config.SMA_SLOW} + RSI {self.config.RSI_PERIOD}")
        print(f"Lot Size:        {self.config.LOT_SIZE}")
        print(f"Max Positions:   {self.config.MAX_POSITIONS}")
        print(f"Max Daily Trades: {self.config.MAX_DAILY_TRADES}")
        print(f"Max Daily Loss:  ${self.config.MAX_DAILY_LOSS}")
        print(f"Max Spread:      {self.config.MAX_SPREAD} points")
        print(f"Sessions:        London:   {self.config.TRADE_LONDON}, "
            f"NY:  {self.config.TRADE_NY}, Asian: {self.config.TRADE_ASIAN}")
        print(f"{'='*80}")
        
        # Connect to MT5
        if not self.connect_mt5():
            return
        
        self.running = True
        print(f"\n✅ Bot is LIVE!   Monitoring for signals...")
        print(f"Press Ctrl+C to stop\n")

        # 🆕 FORCE CLEAR tracking sets (ensure fresh start)
        print(f"[STARTUP] Clearing tracking sets...")
        print(f"[STARTUP] Previous bot_order_ids size: {len(self.bot_order_ids)}")
        self.bot_order_ids.clear()  # Force clear
        self.notified_deals.clear()  # Force clear
        print(f"[STARTUP] Tracking sets cleared")

        
        # Track existing positions on startup
        print(f"[STARTUP] Checking for existing positions...")
        startup_positions = mt5.positions_get(symbol=self.config.SYMBOL)

        if startup_positions:
            print(f"[STARTUP] Found {len(startup_positions)} position(s)")
            
            for pos in startup_positions: 
                print(f"\n[STARTUP] Position {pos.ticket}:")
                print(f"  - Type: {'BUY' if pos.type == 0 else 'SELL'}")
                print(f"  - Volume: {pos.volume}")
                print(f"  - Comment: '{pos.comment}'")
                print(f"  - Magic: {pos.magic}")
                
                if pos.comment == "AutoBot" or pos.magic == 234000:  # Bot's trades
                    self.bot_order_ids.add(pos.ticket)
                    print(f"  - Classification: BOT TRADE (tracked)")
                else:
                    print(f"  - Classification:  MANUAL TRADE (not tracked - will notify)")
        else:
            print(f"[STARTUP] No existing positions found")

        print(f"[STARTUP] Bot order IDs after startup: {self.bot_order_ids}")

        # Send Telegram startup notification
        if self.telegram:
            self.telegram.send_startup()

        # 🆕 FORCE IMMEDIATE MANUAL TRADE DETECTION
        print(f"\n[TEST] Running immediate manual trade detection...")
        self.detect_manual_trades()
        print(f"[TEST] Manual trade detection complete\n")
        
        try:
            while self.running:
                try:
                    self.check_margin_level()  # ← TAMBAHKAN DI SINI
                    # Check session
                    session = get_current_session()
                    trading_allowed = is_trading_allowed()
                    
                    # Check risk limits
                    risk_ok, risk_msg = self.check_risk_limits()
                    
                    # Get market data
                    df = self.get_market_data()
                    if df is None:  
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Failed to get market data")
                        time_module.sleep(self.config.CHECK_INTERVAL)
                        continue
                    
                    # Check for manual trades and closed trades
                    # 🆕 FORCE MANUAL DETECTION TEST
                    print("\n[TEST] Force running manual trade detection...")
                    self.detect_manual_trades()
                    print("[TEST] Manual detection test complete\n")
                    self.monitor_closed_trades()
                    
                    # Check for existing positions
                    positions = mt5.positions_get(symbol=self.config.SYMBOL)
                    has_position = positions is not None and len(positions) > 0
                    
                    # Monitor existing positions
                    if has_position: 
                        self.monitor_positions()
                        time_module.sleep(self.config.CHECK_INTERVAL)
                        continue
                    
                    # Check if trading allowed
                    if not trading_allowed: 
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"Session:   {session} (Trading disabled)        ", end='\r')
                        time_module.sleep(self.config.CHECK_INTERVAL)
                        continue
                    
                    # Check risk limits
                    if not risk_ok:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                            f"⚠️ Trading halted:   {risk_msg}")
                        time_module.sleep(1)
                        continue
                    
                    # Check spread
                    spread_ok, spread = self.check_spread()
                    if not spread_ok:  
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"⚠️ Spread too wide: {spread} points        ", end='\r')
                        time_module.sleep(self.config.CHECK_INTERVAL)
                        continue
                    
                    # Detect signal
                    signal = self.detect_signal(df)
                    
                    if signal:  
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
                            f"🎯 {signal['type']} SIGNAL DETECTED!")
                        print(f"   Session: {session} | Spread: {spread} points")
                        
                        # Execute trade
                        if self.execute_trade(signal):
                            print(f"✅ Trade executed successfully!")
                        else:
                            print(f"❌ Trade execution failed!")
                    else:
                        # Status update
                        current = df.iloc[-1]
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                            f"Session: {session} | Price: {current['close']:.2f} | "
                            f"RSI: {current['rsi']:.1f} | Spread: {spread} | "
                            f"Trades: {self.state['daily_trades']}/{self.config.MAX_DAILY_TRADES} | "
                            f"P&L: ${self.state['daily_pnl']:.2f}        ", end='\r')
                    
                    time_module.sleep(self.config.CHECK_INTERVAL)
                    
                except Exception as e:  
                    print(f"\n❌ Error in main loop: {e}")
                    time_module.sleep(10)
                    continue
        
        except KeyboardInterrupt:  
            print(f"\n\n{'='*80}")
            print(f"🛑 Bot stopped by user")
            print(f"{'='*80}")
        
        finally:
            self.disconnect_mt5()
            save_bot_state(self.state)
            print(f"\n📊 Final Statistics:")
            print(f"   Total Trades Today: {self.state['daily_trades']}")
            print(f"   Daily P&L: ${self.state['daily_pnl']:.2f}")
            print(f"   Total Trades (All Time): {self.state['total_trades']}")
            print(f"\n✅ Bot shutdown complete")

    def check_margin_level(self):
        """Monitor margin level and send warning notifications"""

        info = mt5.account_info()
        if info is None or info.margin_level is None:
            return

        margin = info.margin_level

        # =========================
        # KLASIFIKASI LEVEL
        # =========================
        if margin >= 500:
            status = "SAFE"
            emoji = "🟢"
            label = "MARGIN SAFE"
        elif margin >= 300:
            status = "DECLINING"
            emoji = "🟡"
            label = "MARGIN DECLINING"
        elif margin >= 200:
            status = "WARNING"
            emoji = "🟠"
            label = "MARGIN WARNING"
        elif margin >= 120:
            status = "CRITICAL"
            emoji = "🔴"
            label = "MARGIN CRITICAL"
        else:
            status = "MARGIN_CALL"
            emoji = "☠️"
            label = "MARGIN CALL IMMINENT"

        # =========================
        # ANTI-SPAM: hanya jika berubah
        # =========================
        if self.state.get("margin_status") == status:
            return

        self.state["margin_status"] = status
        save_bot_state(self.state)

        # =========================
        # TELEGRAM NOTIFICATION
        # =========================
        if self.telegram:
            title = self.format_title(f"{emoji} {label}")

            message = f"""
    {title}

    Margin Level: {margin:.2f}%
    Balance: ${info.balance:.2f}
    Equity: ${info.equity:.2f}
    Free Margin: ${info.margin_free:.2f}

    ⚠️ Immediate action recommended
    Time: {datetime.now().strftime('%H:%M:%S')}
    """
        self.telegram.send_message(message)

        print(f"[MARGIN] {label} - {margin:.2f}%")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Safety confirmation
    print("\n⚠️  AUTO-TRADING BOT - SAFETY CHECK")
    print("=" * 80)
    print("This bot will automatically execute trades on your MT5 account.")
    print("Make sure you understand the risks and have tested on DEMO first!")
    print("=" * 80)
    
    confirm = input("\nType 'START' to begin bot:  ")
    
    if confirm.upper() != 'START':
        print("Bot not started.Exiting...")
        exit()
    
    # Start bot
    bot = AutoTradingBot()
    bot.run()