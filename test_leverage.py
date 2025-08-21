#!/usr/bin/env python3
"""
Test Leverage Configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import time

def test_leverage_config():
    """Test leverage configuration with different parameter formats"""
    print("🔧 Testing Leverage Configuration")
    print("=" * 50)
    
    try:
        # Load configuration
        import config
        print("✅ Config loaded")
        
        # Initialize exchange
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_TESTNET_API_KEY,
            'secret': config.BINANCE_TESTNET_SECRET,
            'sandbox': True,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })
        print("✅ Exchange initialized")
        
        test_symbol = 'BTC/USDT'
        target_leverage = int(config.LEVERAGE)  # Ensure integer
        
        print(f"\n🎯 Testing leverage configuration for {test_symbol}")
        print(f"   Target leverage: {target_leverage}x")
        
        # Method 1: Integer leverage
        print(f"\n📋 Method 1: Integer leverage")
        try:
            result = exchange.set_leverage(target_leverage, test_symbol)
            print(f"   ✅ Method 1 successful: {result}")
        except Exception as e:
            print(f"   ❌ Method 1 failed: {e}")
        
        time.sleep(1)  # Rate limit protection
        
        # Method 2: String leverage  
        print(f"\n📋 Method 2: String leverage")
        try:
            result = exchange.set_leverage(str(target_leverage), test_symbol)
            print(f"   ✅ Method 2 successful: {result}")
        except Exception as e:
            print(f"   ❌ Method 2 failed: {e}")
        
        time.sleep(1)  # Rate limit protection
        
        # Method 3: Using direct API call
        print(f"\n📋 Method 3: Direct API parameters")
        try:
            result = exchange.fapiPrivate_post_leverage({
                'symbol': test_symbol.replace('/', ''),
                'leverage': target_leverage
            })
            print(f"   ✅ Method 3 successful: {result}")
        except Exception as e:
            print(f"   ❌ Method 3 failed: {e}")
        
        # Test margin mode setting
        print(f"\n📋 Testing margin mode configuration")
        try:
            result = exchange.set_margin_mode('isolated', test_symbol)
            print(f"   ✅ Margin mode set successfully: {result}")
        except Exception as e:
            print(f"   ⚠️  Margin mode: {e}")
        
        # Verify current settings
        print(f"\n📊 Verifying current configuration...")
        try:
            positions = exchange.fetch_positions([test_symbol])
            for pos in positions:
                if pos['symbol'] == test_symbol:
                    print(f"   Symbol: {pos['symbol']}")
                    print(f"   Margin mode: {pos.get('marginMode', 'unknown')}")
                    print(f"   Leverage: {pos.get('leverage', 'unknown')}")
                    break
        except Exception as e:
            print(f"   ⚠️  Could not verify: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_leverage_config()
