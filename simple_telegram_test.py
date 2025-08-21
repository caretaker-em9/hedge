#!/usr/bin/env python3
"""
Simple Telegram Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple():
    try:
        print("Testing config...")
        import config
        print(f"TELEGRAM_ENABLED: {config.TELEGRAM_ENABLED}")
        print(f"TELEGRAM_SEND_ENTRY_SIGNALS: {config.TELEGRAM_SEND_ENTRY_SIGNALS}")
        
        print("Testing telegram bot...")
        from telegram_bot import telegram_bot
        print(f"Bot enabled: {telegram_bot.enabled}")
        print(f"Send entry signals: {telegram_bot.send_entry_signals}")
        print(f"Is enabled: {telegram_bot.is_enabled()}")
        
        if telegram_bot.is_enabled():
            print("✅ Telegram is properly configured!")
        else:
            print("❌ Telegram is not configured properly")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
