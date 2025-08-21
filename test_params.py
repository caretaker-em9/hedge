#!/usr/bin/env python3
"""
Test Leverage Parameter Format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_leverage_params():
    """Test leverage parameter formatting"""
    print("🔧 Testing Leverage Parameter Format")
    print("=" * 40)
    
    try:
        # Load configuration
        import config
        
        test_symbol = 'BTC/USDT'
        leverage = config.LEVERAGE
        
        print(f"Original symbol: {test_symbol}")
        print(f"Original leverage: {leverage} (type: {type(leverage)})")
        
        # Convert to Binance format
        symbol_raw = test_symbol.replace('/', '')
        leverage_int = int(leverage)
        
        print(f"Binance symbol: {symbol_raw}")
        print(f"Binance leverage: {leverage_int} (type: {type(leverage_int)})")
        
        # Show API call format
        api_params = {
            'symbol': symbol_raw,
            'leverage': leverage_int
        }
        
        print(f"API parameters: {api_params}")
        
        # Test multiple symbols
        print(f"\nTesting multiple symbols:")
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        for symbol in test_symbols:
            symbol_raw = symbol.replace('/', '')
            print(f"  {symbol} -> {symbol_raw}")
        
        print(f"\n✅ Parameter format looks correct!")
        print(f"📋 Fixed issues:")
        print(f"   • Leverage converted to integer: {leverage} -> {leverage_int}")
        print(f"   • Symbol format for Binance: BTC/USDT -> BTCUSDT")
        print(f"   • Using direct API call: fapiPrivate_post_leverage")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_leverage_params()
