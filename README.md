# Freqtrade to CCXT Trading Bot

This project converts a Freqtrade trading strategy (ElliotV5_SMA) into a standalone Python trading bot that can execute trades on Binance Testnet using CCXT. The bot includes a web interface for monitoring trades, viewing charts, and managing the bot.

## Features

- **Trading Strategy**: Implements the original Freqtrade ElliotV5_SMA strategy logic
- **Binance Integration**: Uses CCXT to connect to Binance Testnet for futures trading
- **Advanced Web Dashboard**: Flask-based web interface with real-time monitoring
- **Enhanced Candlestick Charts**: Professional-grade charts with volume bars and signal overlays
- **Multi-Symbol Trading**: Dynamic volume-based symbol selection (up to 100 pairs)
- **Risk Management**: Configurable stop-loss, position sizing, and maximum trades
- **Trade Logging**: Complete trade history with P&L calculations
- **Interactive Charts**: 
  - **Candlestick Charts**: OHLC candles with volume bars
  - **Technical Indicators**: RSI and EWO with colored zones
  - **Signal Overlays**: Entry/exit signals directly on price charts
  - **Portfolio Performance**: Real-time P&L tracking with trade markers
- **Portfolio Tracking**: Real-time portfolio performance monitoring

## Strategy Overview

The bot implements the ElliotV5_SMA strategy with the following signals:

### Entry Conditions
1. **EWO High Condition**: 
   - Price below MA * low_offset
   - EWO above high threshold
   - RSI below buy threshold
   
2. **EWO Low Condition**:
   - Price below MA * low_offset  
   - EWO below low threshold

### Exit Conditions
- Price above MA * high_offset

### Risk Management
- Stop loss: -18.9%
- Leverage: 10x (isolated futures)
- Maximum 5 concurrent trades
- Position sizing based on 2% risk per trade

## Installation

### Prerequisites
- Python 3.8 or higher
- Ubuntu/Debian system (for TA-Lib installation)

### Quick Setup
```bash
# Clone or download the project files
cd /path/to/hedge

# Run the setup script
./setup.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv trading_bot_env
source trading_bot_env/bin/activate

# Install TA-Lib dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y build-essential wget

# Install TA-Lib C library
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..

# Install Python packages
pip install -r requirements.txt
```

## Configuration

1. **Copy the configuration template**:
   ```bash
   cp config_template.py config.py
   ```

2. **Update config.py with your settings**:
   ```python
   # Binance Testnet API keys
   BINANCE_TESTNET_API_KEY = "your_actual_testnet_api_key"
   BINANCE_TESTNET_SECRET = "your_actual_testnet_secret"
   
   # Trading parameters
   INITIAL_BALANCE = 100.0
   MAX_TRADES = 5
   LEVERAGE = 10.0
   ```

3. **Get Binance Testnet API Keys**:
   - Go to [Binance Testnet](https://testnet.binance.vision/)
   - Create an account and generate API keys
   - Enable futures trading permissions

## Usage

### Starting the Application
```bash
# Activate virtual environment
source trading_bot_env/bin/activate

# Run the application
python main.py
```

### Web Interface
1. Open your browser to `http://localhost:5000`
2. Use the dashboard to:
   - Start/stop the trading bot
   - Monitor trade history
   - View real-time charts with signals
   - Track portfolio performance

### Dashboard Features

#### Bot Status & Portfolio
- Current bot status (running/stopped)
- Real-time balance and P&L
- Number of open trades

#### Charts
- **P&L Chart**: Portfolio performance over time
- **Price Charts**: Candlestick charts with moving averages and entry/exit signals
- **Indicator Charts**: RSI and EWO indicators with strategy thresholds

#### Charts
- **P&L Chart**: Portfolio performance over time with trade markers
- **Candlestick Charts**: Professional OHLC candles with:
  - Volume bars below price chart
  - Moving averages (EMA 17 and EMA 49)
  - Buy signals (green triangles pointing up)
  - Sell signals (red triangles pointing down)
  - Enhanced hover information
- **Technical Indicator Charts**: RSI and EWO with:
  - Colored zones (overbought/oversold for RSI)
  - Strategy thresholds clearly marked
  - Filled areas for better visualization

#### Trade History
- Complete trade log with entry/exit details
- Real-time P&L calculations
- Trade signal information

## File Structure

```
hedge/
├── trading_bot.py          # Main trading bot logic
├── web_interface.py        # Flask web application
├── main.py                # Application runner
├── config.py              # Configuration file
├── config_template.py     # Configuration template
├── requirements.txt       # Python dependencies
├── setup.sh              # Setup script
├── templates/
│   └── dashboard.html     # Web dashboard template
└── README.md             # This file
```

## Strategy Parameters

The strategy uses these key parameters (configurable in config.py):

```python
STRATEGY_PARAMS = {
    "base_nb_candles_buy": 17,      # EMA period for buy signals
    "base_nb_candles_sell": 49,     # EMA period for sell signals
    "low_offset": 0.978,            # Buy threshold multiplier
    "high_offset": 1.019,           # Sell threshold multiplier
    "ewo_low": -17.457,            # EWO low threshold
    "ewo_high": 3.34,              # EWO high threshold
    "rsi_buy": 65,                 # RSI buy threshold
    "fast_ewo": 50,                # EWO fast period
    "slow_ewo": 200,               # EWO slow period
    "stoploss": -0.189             # Stop loss percentage
}
```

## Safety Features

- **Testnet Only**: Configured for Binance Testnet by default
- **Mock Mode**: Falls back to demo mode if no API keys provided
- **Position Limits**: Maximum 5 concurrent positions
- **Stop Loss**: Automatic stop loss at -18.9%
- **Risk Management**: 2% risk per trade with 10x leverage

## Monitoring and Logging

- All activities logged to `trading_app.log`
- Real-time trade monitoring via web interface
- Portfolio performance tracking
- Technical indicator visualization

## Important Notes

⚠️ **This is for educational and testing purposes only**
- Always test thoroughly on testnet before considering live trading
- Past performance does not guarantee future results
- Cryptocurrency trading involves significant risk
- Never risk more than you can afford to lose

## Troubleshooting

### Common Issues

1. **TA-Lib Installation Issues**:
   ```bash
   # Make sure you have the C library installed
   sudo apt-get install -y build-essential
   # Then reinstall TA-Lib
   pip uninstall TA-Lib
   pip install TA-Lib
   ```

2. **API Connection Issues**:
   - Verify your testnet API keys are correct
   - Check that futures trading is enabled for your testnet account
   - Ensure you're using testnet endpoints

3. **Web Interface Not Loading**:
   - Check if port 5000 is available
   - Try accessing via `http://127.0.0.1:5000` instead
   - Check firewall settings

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes. Use at your own risk.

## Disclaimer

This software is provided for educational and research purposes only. The authors are not responsible for any financial losses incurred through the use of this software. Always test thoroughly and never trade with funds you cannot afford to lose.
