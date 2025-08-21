#!/usr/bin/env python3
"""
Test Telegram Entry Signal Configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_config():
    """Test telegram configuration and send a test entry signal"""
    print("🔍 Testing Telegram Configuration")
    print("=" * 50)
    
    try:
        # Test configuration loading
        import config
        print("✅ Config loaded successfully")
        
        print(f"📋 Configuration:")
        print(f"   TELEGRAM_ENABLED: {getattr(config, 'TELEGRAM_ENABLED', 'NOT SET')}")
        print(f"   TELEGRAM_BOT_TOKEN: {'SET' if getattr(config, 'TELEGRAM_BOT_TOKEN', '') else 'NOT SET'}")
        print(f"   TELEGRAM_CHAT_ID: {getattr(config, 'TELEGRAM_CHAT_ID', 'NOT SET')}")
        print(f"   TELEGRAM_SEND_ENTRY_SIGNALS: {getattr(config, 'TELEGRAM_SEND_ENTRY_SIGNALS', 'NOT SET')}")
        
        # Test telegram bot import
        try:
            from telegram_bot import telegram_bot, send_trade_entry_notification
            print("✅ Telegram bot imported successfully")
        except Exception as e:
            print(f"❌ Telegram bot import failed: {e}")
            return
        
        # Test telegram bot initialization
        print(f"\n📱 Telegram Bot Status:")
        print(f"   Enabled: {telegram_bot.enabled}")
        print(f"   Token configured: {'YES' if telegram_bot.bot_token else 'NO'}")
        print(f"   Chat ID configured: {'YES' if telegram_bot.chat_id else 'NO'}")
        print(f"   Send entry signals: {telegram_bot.send_entry_signals}")
        print(f"   Is enabled: {telegram_bot.is_enabled()}")
        
        if not telegram_bot.is_enabled():
            print("❌ Telegram bot is not properly configured!")
            return
        
        # Test sending a sample entry signal
        print(f"\n📤 Testing entry signal notification...")
        
        # Create a sample trade dict
        sample_trade = {
            'symbol': 'BTC/USDT',
            'side': 'long',
            'amount': 0.001,
            'price': 50000.0,
            'timestamp': 1692633600.0,  # Sample timestamp
            'entry_signal': 'EWO_RSI_Signal',
            'market_conditions': {'description': 'Test signal'},
            'pnl': 0.0
        }
        
        try:
            result = await send_trade_entry_notification(sample_trade)
            if result:
                print("✅ Test entry signal sent successfully!")
                print("   Check your Telegram for the message.")
            else:
                print("❌ Failed to send test entry signal")
        except Exception as e:
            print(f"❌ Error sending test signal: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🧪 Telegram Entry Signal Test")
    asyncio.run(test_telegram_config())

if __name__ == "__main__":
    main()
