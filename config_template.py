# Trading Bot Configuration
# Copy this file to config.py and update with your settings

# Binance Testnet API Configuration
BINANCE_TESTNET_API_KEY = "your_testnet_api_key_here"
BINANCE_TESTNET_SECRET = "your_testnet_secret_here"

# Trading Configuration
INITIAL_BALANCE = 100.0
MAX_TRADES = 5
LEVERAGE = 10.0
TIMEFRAME = "5m"

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

# Symbols to trade
TRADING_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT", 
    "BNB/USDT",
    "ADA/USDT",
    "SOL/USDT"
]

# Risk Management
RISK_PER_TRADE = 0.02  # 2% of balance per trade
TRAILING_STOP = True
TRAILING_STOP_POSITIVE = 0.005
TRAILING_STOP_POSITIVE_OFFSET = 0.03

# Web Interface
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
SECRET_KEY = "your_secret_key_here_change_this"
