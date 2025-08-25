# Default configuration file
# This is created automatically if config.py doesn't exist

# Binance Testnet API Configuration
BINANCE_TESTNET_API_KEY = "ed7c2aa7483d7218db4be1a43c6cbb6a7fa49bebf48df13c256f9c92054070cc"
BINANCE_TESTNET_SECRET = "107d36fde411bbf834f5d86a9de3e7df2baf9476e00cfd38558b35fb7e7bfd3b"

# Trading Configuration
INITIAL_BALANCE = 30.0
MAX_TRADES = 2  # Maximum 2 trades: 1 long position + 1 hedge position
LEVERAGE = 10.0
TIMEFRAME = "5m"

# Hedging Strategy Configuration
INITIAL_TRADE_SIZE = 30.0  # Initial trade allocation per pair
LONG_POSITION_SIZE = 6.0  # Size of initial long position (increased from 5.0)
SHORT_POSITION_SIZE = 10.0  # Size of hedge short position
HEDGE_TRIGGER_LOSS = -0.05  # -5% loss triggers hedge position
ONE_TRADE_PER_PAIR = True  # Only allow one active trade pair at a time

# Symbol Selection Configuration
MAX_SYMBOLS = 100  # Maximum number of symbols to trade
MIN_24H_VOLUME = 1000000  # Minimum 24h volume in USDT (1M)
SYMBOL_UPDATE_INTERVAL = 3600  # Update symbol list every hour (seconds)
FILTER_BY_VOLUME = True  # Enable dynamic symbol filtering by volume

# Strategy Parameters (from original Freqtrade strategy)
STRATEGY_PARAMS = {
    "base_nb_candles_buy": 17,
    "base_nb_candles_sell": 49,
    "low_offset": 0.978,
    "high_offset": 1.019,
    "ewo_low": -17.457,
    "ewo_high": 3.34,
    "rsi_buy": 65,
    "fast_ewo": 50,
    "slow_ewo": 200,
    "stoploss": -0.189
}

# ROI Configuration (Freqtrade style)
MINIMAL_ROI = {
    "0": 0.70,    # 70% ROI (exit immediately if profit hits 70%)
    "1": 0.65,    # 65% ROI after 1 minute
    "2": 0.60,    # 60% ROI after 2 minutes
    "3": 0.55,    # 55% ROI after 3 minutes
    "4": 0.50,    # 50% ROI after 4 minutes
    "5": 0.45,    # 45% ROI after 5 minutes
    "6": 0.40,    # 40% ROI after 6 minutes
    "7": 0.35,    # 35% ROI after 7 minutes
    "8": 0.30,    # 30% ROI after 8 minutes
    "9": 0.25,    # 25% ROI after 9 minutes
    "10": 0.20,   # 20% ROI after 10 minutes
    "15": 0.15,   # 15% ROI after 15 minutes
    "20": 0.10,   # 10% ROI after 20 minutes
    "30": 0.07,   # 7% ROI after 30 minutes
    "45": 0.05,   # 5% ROI after 45 minutes
    "60": 0.03,   # 3% ROI after 60 minutes
    "90": 0.01,   # 1% ROI after 90 minutes
    "120": 0      # Exit after 120 minutes (2 hours)
}

# Symbols to trade (fallback list if volume filtering fails)
TRADING_SYMBOLS = [
    # Major pairs
    "BTC/USDT", "ETH/USDT", "BNB/USDT", 
    # Large cap altcoins
    "ADA/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "DOT/USDT", 
    "AVAX/USDT", "LUNA/USDT", "LINK/USDT", "UNI/USDT", "LTC/USDT",
    "BCH/USDT", "MATIC/USDT", "ALGO/USDT", "VET/USDT", "ATOM/USDT",
    # Mid cap altcoins
    "ICP/USDT", "THETA/USDT", "FIL/USDT", "TRX/USDT", "ETC/USDT",
    "XLM/USDT", "MANA/USDT", "SAND/USDT", "CRO/USDT", "NEAR/USDT",
    "GALA/USDT", "SHIB/USDT", "FTM/USDT", "ONE/USDT", "HBAR/USDT",
    # Additional pairs for more opportunities
    "CAKE/USDT", "KSM/USDT", "WAVES/USDT", "ENJ/USDT", "BAT/USDT",
    "ZIL/USDT", "QTUM/USDT", "ICX/USDT", "ZEC/USDT", "DASH/USDT",
    "NEO/USDT", "IOTA/USDT", "XTZ/USDT", "EOS/USDT", "OMG/USDT"
]

# Risk Management
RISK_PER_TRADE = 0.30  # 30% of balance for hedging strategy (initial trade size)
TRAILING_STOP = True  # Disable trailing stops for hedging strategy
TRAILING_STOP_POSITIVE = 0.005
TRAILING_STOP_POSITIVE_OFFSET = 0.03

# Hedging Exit Strategy
EXIT_WHEN_HEDGED = True  # Exit both positions when hedge covers loss
MIN_HEDGE_PROFIT_RATIO = 1.0  # Hedge profit should at least cover long loss

# Web Interface
WEB_HOST = "0.0.0.0"
WEB_PORT = 5020
SECRET_KEY = "trading_bot_secret_key_change_this_in_production"

# Authentication
WEB_USERNAME = "hedgeadmin"
WEB_PASSWORD = "makemoney@123"
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "8368420281:AAE4MLYuDyyxEj3yN5brdC51Mv7W1l6QNYk"  # Get from @BotFather
TELEGRAM_CHAT_ID = "584235730"     # Your chat ID or group chat ID
TELEGRAM_ENABLED = True  # Set to True to enable Telegram notifications
TELEGRAM_SEND_ENTRY_SIGNALS = True
TELEGRAM_SEND_EXIT_SIGNALS = True
TELEGRAM_SEND_PROFITS = True
TELEGRAM_SEND_ERRORS = True
TELEGRAM_SEND_STATUS_UPDATES = True
