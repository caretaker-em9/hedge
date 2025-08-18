#!/usr/bin/env python3
"""
Main Application Runner
Combines the trading bot and web interface in a single application
"""

import sys
import os
import threading
import time
from trading_bot import TradingBot, BotConfig
from web_interface import app
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration"""
    try:
        import config
        
        # Create bot configuration from config file
        bot_config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,
            max_trades=config.MAX_TRADES,
            leverage=config.LEVERAGE,
            timeframe=config.TIMEFRAME,
            symbols=config.TRADING_SYMBOLS,
            max_symbols=getattr(config, 'MAX_SYMBOLS', 100),
            min_24h_volume=getattr(config, 'MIN_24H_VOLUME', 1000000),
            filter_by_volume=getattr(config, 'FILTER_BY_VOLUME', True),
            **config.STRATEGY_PARAMS
        )
        
        return bot_config, config
    
    except ImportError:
        logger.error("Configuration file not found!")
        logger.error("Please copy config_template.py to config.py and update with your settings")
        sys.exit(1)

def main():
    """Main application entry point"""
    logger.info("Starting Trading Bot Application...")
    
    # Load configuration
    bot_config, config = load_config()
    
    # Validate API keys
    if (config.BINANCE_TESTNET_API_KEY == "your_testnet_api_key_here" or 
        config.BINANCE_TESTNET_SECRET == "your_testnet_secret_here"):
        logger.warning("Using default API keys - bot will run in demo mode")
        logger.warning("Please update config.py with your Binance Testnet API keys for live trading")
    
    # Initialize global bot instance for web interface
    global bot
    bot = TradingBot(bot_config)
    
    # Update web interface app configuration
    app.secret_key = config.SECRET_KEY
    
    # Make bot available to web interface
    import web_interface
    web_interface.bot = bot
    
    logger.info("Configuration loaded successfully")
    logger.info(f"Initial Balance: ${bot_config.initial_balance}")
    logger.info(f"Max Trades: {bot_config.max_trades}")
    logger.info(f"Trading Symbols: {', '.join(bot_config.symbols)}")
    
    # Start web interface
    logger.info(f"Starting web interface on http://localhost:{config.WEB_PORT}")
    logger.info("You can access the dashboard in your browser")
    logger.info("Use the web interface to start/stop the trading bot")
    
    try:
        app.run(
            debug=False,  # Set to False for production
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        # Cleanup
        if hasattr(bot, 'is_running') and bot.is_running:
            bot.stop()
        logger.info("Application stopped")

if __name__ == "__main__":
    main()
