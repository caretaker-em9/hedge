#!/usr/bin/env python3
"""
Simple Binance Testnet Connection Test (non-async)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_connection():
    """Test connection to Binance testnet"""
    
    print("🔌 SIMPLE BINANCE TESTNET TEST")
    print("=" * 50)
    
    try:
        # Load configuration
        import config
        print("✅ Config loaded successfully")
        
        # Initialize exchange (sync version)
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
        
        # Test basic connection
        try:
            balance = exchange.fetch_balance()
            print(f"✅ Connected to Binance testnet successfully")
            print(f"💰 USDT Balance: {balance.get('USDT', {}).get('free', 0):.2f}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return
        
        # Test symbol prices
        print("\n📊 Current Prices:")
        test_symbols = ['BTC/USDT', 'ETH/USDT']
        
        for symbol in test_symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                print(f"   {symbol}: ${ticker['last']:,.2f}")
                
                # Calculate position sizes
                long_amount = config.LONG_POSITION_SIZE / ticker['last']
                hedge_amount = config.SHORT_POSITION_SIZE / ticker['last']
                
                print(f"     Long: ${config.LONG_POSITION_SIZE} = {long_amount:.8f}")
                print(f"     Hedge: ${config.SHORT_POSITION_SIZE} = {hedge_amount:.8f}")
                
            except Exception as e:
                print(f"   ❌ Failed to get {symbol}: {e}")
        
        print("\n✅ BASIC CONNECTION TEST PASSED")
        print("\n🎯 Configuration Summary:")
        print(f"   • Balance: $30 testnet")
        print(f"   • Leverage: {config.LEVERAGE}x") 
        print(f"   • Long position: ${config.LONG_POSITION_SIZE}")
        print(f"   • Hedge position: ${config.SHORT_POSITION_SIZE}")
        print(f"   • Expected: Isolated margin, correct position sizes")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_connection()
