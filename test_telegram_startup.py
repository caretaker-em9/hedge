#!/usr/bin/env python3

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_telegram_startup_messages():
    """Test Telegram startup messages functionality"""
    
    try:
        from telegram_bot_enhanced import (
            telegram_notifier, 
            send_startup_notification,
            send_bot_ready_notification, 
            send_health_check_notification
        )
        
        print("🚀 Testing Telegram Startup Messages")
        print("=" * 50)
        
        if not telegram_notifier.is_enabled():
            print("❌ Telegram bot is not enabled or configured")
            print("Current config:")
            print(f"  Bot Token: {'Set' if telegram_notifier.bot_token else 'Missing'}")
            print(f"  Chat ID: {'Set' if telegram_notifier.chat_id else 'Missing'}")
            print(f"  Enabled: {telegram_notifier.enabled}")
            return
        
        print("✅ Telegram bot is configured")
        print(f"📱 Chat ID: {telegram_notifier.chat_id}")
        
        # Test startup message
        print("\n🚀 Sending startup message...")
        test_config = {
            'initial_balance': 30.0,
            'max_trades': 2,
            'leverage': 10,
            'timeframe': '5m',
            'long_position_size': 5.0,
            'short_position_size': 10.0,
            'hedge_trigger_loss': -0.05,
            'one_trade_per_pair': True
        }
        
        success = await send_startup_notification(test_config)
        if success:
            print("✅ Startup message sent successfully!")
        else:
            print("❌ Failed to send startup message")
            return
        
        # Wait before next message
        await asyncio.sleep(3)
        
        # Test bot ready message
        print("\n✅ Sending bot ready message...")
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        success = await send_bot_ready_notification(len(test_symbols), test_symbols)
        if success:
            print("✅ Bot ready message sent successfully!")
        else:
            print("❌ Failed to send bot ready message")
        
        # Wait before next message
        await asyncio.sleep(3)
        
        # Test health check
        print("\n💓 Sending health check...")
        success = await send_health_check_notification()
        if success:
            print("✅ Health check sent successfully!")
        else:
            print("❌ Failed to send health check")
        
        print("\n🎉 Telegram startup message testing completed!")
        print("\nMessages should appear in your Telegram chat.")
        print("If you received all messages, the integration is working correctly!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure telegram_bot_enhanced.py is in the correct location")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram_startup_messages())
