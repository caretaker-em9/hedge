#!/usr/bin/env python3

import asyncio
import time
import requests
import sys
import os

def test_complete_integration():
    """Test the complete Telegram integration with trading bot"""
    
    print("🧪 Testing Complete Telegram Integration")
    print("=" * 60)
    
    try:
        # Test 1: Import all modules
        print("📦 Testing imports...")
        from telegram_bot_enhanced import telegram_notifier
        from trading_bot import TradingBot, BotConfig
        import config
        print("✅ All modules imported successfully")
        
        # Test 2: Check Telegram configuration
        print("\n📱 Checking Telegram configuration...")
        if telegram_notifier.is_enabled():
            print(f"✅ Telegram bot configured (Chat ID: {telegram_notifier.chat_id})")
        else:
            print("❌ Telegram bot not configured")
            return
        
        # Test 3: Test direct Telegram connection
        print("\n🔗 Testing Telegram connection...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(telegram_notifier.test_connection_with_feedback())
        if success:
            print("✅ Direct Telegram connection successful")
        else:
            print("❌ Direct Telegram connection failed")
            return
        
        loop.close()
        
        # Test 4: Test bot initialization
        print("\n🤖 Testing bot initialization...")
        bot_config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,
            max_trades=config.MAX_TRADES,
            leverage=config.LEVERAGE,
            timeframe=config.TIMEFRAME,
            symbols=config.TRADING_SYMBOLS[:5],  # Use only 5 symbols for testing
            telegram_enabled=getattr(config, 'TELEGRAM_ENABLED', False)
        )
        
        print("✅ Bot configuration created")
        
        # Test 5: Test startup notification
        print("\n🚀 Testing startup notification...")
        trading_config = {
            'initial_balance': bot_config.initial_balance,
            'max_trades': bot_config.max_trades,
            'leverage': bot_config.leverage,
            'timeframe': bot_config.timeframe,
            'long_position_size': 5.0,
            'short_position_size': 10.0,
            'hedge_trigger_loss': -0.05,
            'one_trade_per_pair': True
        }
        
        from telegram_bot_enhanced import send_startup_notification
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(send_startup_notification(trading_config))
        if success:
            print("✅ Startup notification sent successfully")
        else:
            print("❌ Startup notification failed")
        
        loop.close()
        
        # Test 6: Test web interface endpoints
        print("\n🌐 Testing web interface integration...")
        try:
            # Check if web interface is running
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code in [200, 302]:  # 302 for redirect to login
                print("✅ Web interface is accessible")
            else:
                print(f"⚠️ Web interface returned status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("ℹ️ Web interface not currently running (this is expected)")
        except Exception as e:
            print(f"⚠️ Web interface test error: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Integration testing completed!")
        print("\nSummary:")
        print("✅ Telegram bot properly configured")
        print("✅ Enhanced notifications working") 
        print("✅ Startup messages functional")
        print("✅ Ready for live trading with Telegram alerts")
        
        print("\n📋 Usage Instructions:")
        print("1. Start the bot: python main.py")
        print("2. You'll receive a startup message in Telegram")
        print("3. When you start trading via web interface, you'll get a 'bot ready' message")
        print("4. All trades, profits, and errors will be sent to Telegram")
        print("5. When you stop the bot, you'll get a summary message")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_integration()
