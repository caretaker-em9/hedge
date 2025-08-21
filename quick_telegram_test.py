#!/usr/bin/env python3
"""
Quick Telegram Test with Timeout
"""

import asyncio
import sys
import os
import signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def timeout_handler(signum, frame):
    print("❌ TIMEOUT: Telegram test took too long")
    sys.exit(1)

async def quick_telegram_test():
    """Quick telegram test with timeout"""
    try:
        print("🧪 Quick Telegram Test (10 second timeout)")
        print("-" * 40)
        
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 second timeout
        
        # Test imports
        from telegram_bot import telegram_bot
        print(f"✅ Bot loaded - Enabled: {telegram_bot.enabled}")
        
        if not telegram_bot.enabled:
            print("❌ Bot is disabled")
            return
        
        # Quick message test
        print("📤 Sending test message...")
        result = await telegram_bot.send_message("🧪 Quick test " + str(asyncio.get_event_loop().time()))
        
        if result:
            print("✅ Message sent successfully!")
        else:
            print("❌ Message failed to send")
            
        signal.alarm(0)  # Cancel timeout
        
    except asyncio.TimeoutError:
        print("❌ TIMEOUT: Request took too long")
    except Exception as e:
        print(f"❌ Error: {e}")
        signal.alarm(0)

def main():
    try:
        asyncio.run(quick_telegram_test())
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
