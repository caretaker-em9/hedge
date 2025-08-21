#!/usr/bin/env python3
"""
Main Application Runner
Combines the trading bot and web interface in a single application
"""

import sys
import os
import threading
import time
import asyncio
from trading_bot import TradingBot, BotConfig
from web_interface import app
import logging

# Import enhanced Telegram bot
try:
    from telegram_bot_enhanced import (
        telegram_notifier, 
        send_startup_notification, 
        send_bot_ready_notification,
        send_bot_stopped_notification
    )
    TELEGRAM_ENHANCED_AVAILABLE = True
except ImportError:
    TELEGRAM_ENHANCED_AVAILABLE = False
    logging.warning("Enhanced Telegram bot not available")

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
            # Hedging strategy parameters
            initial_trade_size=getattr(config, 'INITIAL_TRADE_SIZE', 30.0),
            long_position_size=getattr(config, 'LONG_POSITION_SIZE', 10.0),
            short_position_size=getattr(config, 'SHORT_POSITION_SIZE', 15.0),
            hedge_trigger_loss=getattr(config, 'HEDGE_TRIGGER_LOSS', -0.05),
            one_trade_per_pair=getattr(config, 'ONE_TRADE_PER_PAIR', True),
            exit_when_hedged=getattr(config, 'EXIT_WHEN_HEDGED', True),
            min_hedge_profit_ratio=getattr(config, 'MIN_HEDGE_PROFIT_RATIO', 1.0),
            # Telegram configuration
            telegram_enabled=getattr(config, 'TELEGRAM_ENABLED', False),
            telegram_bot_token=getattr(config, 'TELEGRAM_BOT_TOKEN', ''),
            telegram_chat_id=getattr(config, 'TELEGRAM_CHAT_ID', ''),
            # ROI configuration
            minimal_roi=getattr(config, 'MINIMAL_ROI', None),
            # Trailing stop configuration
            trailing_stop=getattr(config, 'TRAILING_STOP', False),
            trailing_stop_positive=getattr(config, 'TRAILING_STOP_POSITIVE', 0.005),
            trailing_stop_positive_offset=getattr(config, 'TRAILING_STOP_POSITIVE_OFFSET', 0.03),
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
    
    # Send Telegram startup notification
    if TELEGRAM_ENHANCED_AVAILABLE and getattr(config, 'TELEGRAM_ENABLED', False):
        try:
            # Prepare trading configuration for startup message
            trading_config = {
                'initial_balance': bot_config.initial_balance,
                'max_trades': bot_config.max_trades,
                'leverage': bot_config.leverage,
                'timeframe': bot_config.timeframe,
                'long_position_size': getattr(bot_config, 'long_position_size', 5.0),
                'short_position_size': getattr(bot_config, 'short_position_size', 10.0),
                'hedge_trigger_loss': getattr(bot_config, 'hedge_trigger_loss', -0.05),
                'one_trade_per_pair': getattr(bot_config, 'one_trade_per_pair', True)
            }
            
            # Send startup notification synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_startup_notification(trading_config))
            loop.close()
            logger.info("Telegram startup notification sent")
        except Exception as e:
            logger.error(f"Error sending Telegram startup notification: {e}")
    
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
