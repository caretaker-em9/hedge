#!/usr/bin/env python3

import asyncio
import sys
import os

# Add current directory to path to import telegram_bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot import telegram_bot
from datetime import datetime

async def test_telegram_bot():
    """Test Telegram bot functionality with sample data"""
    
    print("🤖 Testing Telegram Bot Integration")
    print("=" * 50)
    
    # Check if telegram is configured
    if not telegram_bot.is_enabled():
        print("❌ Telegram bot is not enabled or configured")
        print("\nTo configure Telegram bot:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Get your chat ID")
        print("4. Update config.py with:")
        print("   TELEGRAM_BOT_TOKEN = 'your_bot_token'")
        print("   TELEGRAM_CHAT_ID = 'your_chat_id'")
        print("   TELEGRAM_ENABLED = True")
        return
    
    print("✅ Telegram bot is configured and enabled")
    print(f"Bot Token: {telegram_bot.bot_token[:10]}...")
    print(f"Chat ID: {telegram_bot.chat_id}")
    
    # Test connection
    print("\n📡 Testing connection...")
    if await telegram_bot.test_connection():
        print("✅ Connection test successful!")
    else:
        print("❌ Connection test failed!")
        return
    
    # Test trade entry notification
    print("\n📈 Testing trade entry notification...")
    sample_trade_entry = {
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 0.001,
        'price': 45000.0,
        'timestamp': datetime.now().timestamp(),
        'entry_reason': 'Strong bullish EWO signal detected with favorable RSI conditions and SMA crossover confirmation',
        'technical_indicators': {
            'rsi': 62.5,
            'sma_fast': 44950.0,
            'sma_slow': 44800.0,
            'macd_signal': 'bullish'
        },
        'market_conditions': {
            'trend': 'uptrend',
            'volatility': 'moderate',
            'volume_profile': 'high'
        }
    }
    
    if await telegram_bot.send_trade_entry(sample_trade_entry):
        print("✅ Trade entry notification sent!")
    else:
        print("❌ Failed to send trade entry notification")
    
    # Wait a moment between messages
    await asyncio.sleep(2)
    
    # Test trade exit notification
    print("\n📉 Testing trade exit notification...")
    sample_trade_exit = {
        'symbol': 'BTC/USDT',
        'side': 'buy',
        'amount': 0.001,
        'price': 45000.0,
        'exit_price': 46350.0,
        'timestamp': datetime.now().timestamp(),
        'exit_timestamp': datetime.now().timestamp(),
        'pnl': 13.5,
        'pnl_percentage': 3.0,
        'exit_reason': 'Profit target reached: 3% gain achieved with strong momentum continuation'
    }
    
    if await telegram_bot.send_trade_exit(sample_trade_exit):
        print("✅ Trade exit notification sent!")
    else:
        print("❌ Failed to send trade exit notification")
    
    # Wait a moment between messages
    await asyncio.sleep(2)
    
    # Test hedge completion notification
    print("\n🔄 Testing hedge completion notification...")
    sample_long_trade = {
        'symbol': 'ETH/USDT',
        'side': 'buy',
        'price': 3000.0,
        'exit_price': 2850.0,
        'pnl': -15.0
    }
    
    sample_short_trade = {
        'symbol': 'ETH/USDT',
        'side': 'sell',
        'price': 2850.0,
        'exit_price': 2800.0,
        'pnl': 17.5
    }
    
    if await telegram_bot.send_hedge_completion(sample_long_trade, sample_short_trade, 2.5):
        print("✅ Hedge completion notification sent!")
    else:
        print("❌ Failed to send hedge completion notification")
    
    # Wait a moment between messages
    await asyncio.sleep(2)
    
    # Test error notification
    print("\n🚨 Testing error notification...")
    if await telegram_bot.send_error("Sample error for testing", "Test context"):
        print("✅ Error notification sent!")
    else:
        print("❌ Failed to send error notification")
    
    # Wait a moment between messages
    await asyncio.sleep(2)
    
    # Test status notification
    print("\n📊 Testing status notification...")
    if await telegram_bot.send_bot_status("running", 30.0, 2, 15.75):
        print("✅ Status notification sent!")
    else:
        print("❌ Failed to send status notification")
    
    # Wait a moment between messages
    await asyncio.sleep(2)
    
    # Test daily summary
    print("\n📅 Testing daily summary...")
    if await telegram_bot.send_daily_summary(8, 45.25, 75.0, 22.50, -8.25):
        print("✅ Daily summary sent!")
    else:
        print("❌ Failed to send daily summary")
    
    print("\n" + "=" * 50)
    print("🎉 Telegram bot testing completed!")
    print("\nIf all tests passed, your Telegram bot is ready for live trading notifications!")

def print_setup_instructions():
    """Print setup instructions for Telegram bot"""
    print("""
🤖 TELEGRAM BOT SETUP INSTRUCTIONS
=" * 50

Step 1: Create a Telegram Bot
1. Open Telegram and search for @BotFather
2. Start a chat and send /newbot
3. Choose a name for your bot (e.g., "My Trading Bot")
4. Choose a username (must end with 'bot', e.g., "mytradingbot")
5. Copy the bot token provided by BotFather

Step 2: Get Your Chat ID
Method 1 - Using @userinfobot:
1. Search for @userinfobot on Telegram
2. Start a chat and send any message
3. Copy your User ID (this is your chat ID)

Method 2 - Using your bot:
1. Send a message to your bot (anything)
2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
3. Look for "chat":{"id": YOUR_CHAT_ID}

Step 3: Configure the Bot
Update your config.py file:

TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGhIJklmnopQrsTuvwxyz123456789"
TELEGRAM_CHAT_ID = "123456789"
TELEGRAM_ENABLED = True

# Optional: Customize notifications
TELEGRAM_SEND_ENTRY_SIGNALS = True
TELEGRAM_SEND_EXIT_SIGNALS = True
TELEGRAM_SEND_PROFITS = True
TELEGRAM_SEND_ERRORS = True
TELEGRAM_SEND_STATUS_UPDATES = True

Step 4: Test the Bot
Run: python test_telegram_bot.py

Step 5: Install Dependencies
Make sure aiohttp is installed:
pip install aiohttp>=3.8.0

FEATURES:
✅ Trade entry/exit signals with detailed analysis
✅ Hedge completion summaries with P&L breakdown
✅ Real-time error notifications
✅ Bot status updates (start/stop)
✅ Daily trading summaries
✅ Rich formatting with emojis and technical details
✅ Configurable notification types
✅ Async support for non-blocking operation

SECURITY NOTES:
- Keep your bot token secret
- Only share your chat ID with trusted parties
- Consider using a private group for notifications
- Bot tokens can be regenerated if compromised

For group notifications:
1. Add your bot to a group
2. Make it an admin (optional)
3. Get the group chat ID (negative number)
4. Use the group chat ID in config
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print_setup_instructions()
    else:
        asyncio.run(test_telegram_bot())
