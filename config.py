# Default configuration file
# This is created automatically if config.py doesn't exist

# Binance Testnet API Configuration
BINANCE_TESTNET_API_KEY = "ed7c2aa7483d7218db4be1a43c6cbb6a7fa49bebf48df13c256f9c92054070cc"
BINANCE_TESTNET_SECRET = "107d36fde411bbf834f5d86a9de3e7df2baf9476e00cfd38558b35fb7e7bfd3b"

# Trading Configuration
INITIAL_BALANCE = 30.0
MAX_TRADES = 2
LEVERAGE = 10.0
TIMEFRAME = "5m"

# Hedging Strategy Configuration
INITIAL_TRADE_SIZE = 30.0  # Initial trade allocation per pair
LONG_POSITION_SIZE = 5.0  # Size of initial long position
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
TRAILING_STOP = False  # Disable trailing stops for hedging strategy
TRAILING_STOP_POSITIVE = 0.005
TRAILING_STOP_POSITIVE_OFFSET = 0.03

# Hedging Exit Strategy
EXIT_WHEN_HEDGED = True  # Exit both positions when hedge covers loss
MIN_HEDGE_PROFIT_RATIO = 1.0  # Hedge profit should at least cover long loss

# Web Interface
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
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
