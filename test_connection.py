#!/usr/bin/env python3
"""
Test Binance Testnet Connection and Configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import logging
from trading_bot import TradingBot, BotConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_binance_connection():
    """Test connection to Binance testnet and configuration"""
    
    print("🔌 BINANCE TESTNET CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Load configuration
        import config
        
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
        
        print("📡 Testing Connection...")
        
        # Test basic connection
        try:
            balance = await exchange.fetch_balance()
            print(f"   ✅ Connected to Binance testnet successfully")
            print(f"   💰 USDT Balance: {balance.get('USDT', {}).get('free', 0):.2f}")
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            return
        
        # Test symbol info
        print("\n📊 Symbol Information:")
        test_symbols = ['BTC/USDT', 'ETH/USDT']
        
        for symbol in test_symbols:
            try:
                ticker = await exchange.fetch_ticker(symbol)
                market = exchange.market(symbol)
                
                print(f"   {symbol}:")
                print(f"     Current Price: ${ticker['last']:,.2f}")
                print(f"     Min Order Size: {market['limits']['amount']['min']}")
                print(f"     Price Precision: {market['precision']['price']}")
                print(f"     Amount Precision: {market['precision']['amount']}")
                
                # Calculate position sizes
                long_amount = config.LONG_POSITION_SIZE / ticker['last']
                hedge_amount = config.SHORT_POSITION_SIZE / ticker['last']
                
                print(f"     Long Position ({config.LONG_POSITION_SIZE}$): {long_amount:.8f}")
                print(f"     Hedge Position ({config.SHORT_POSITION_SIZE}$): {hedge_amount:.8f}")
                
                # Check if amounts meet minimum requirements
                if long_amount >= market['limits']['amount']['min']:
                    print(f"     ✅ Long position meets minimum size")
                else:
                    print(f"     ⚠️  Long position below minimum ({market['limits']['amount']['min']})")
                
                if hedge_amount >= market['limits']['amount']['min']:
                    print(f"     ✅ Hedge position meets minimum size")
                else:
                    print(f"     ⚠️  Hedge position below minimum ({market['limits']['amount']['min']})")
                
            except Exception as e:
                print(f"   ❌ Failed to get {symbol} info: {e}")
        
        # Test margin mode and leverage configuration
        print("\n⚙️  Testing Configuration Settings:")
        
        for symbol in test_symbols:
            try:
                # Try to set margin mode (this might fail if already set)
                try:
                    await exchange.set_margin_mode('isolated', symbol)
                    print(f"   ✅ {symbol}: Set to isolated margin")
                except Exception as e:
                    if 'No need to change margin type' in str(e):
                        print(f"   ✅ {symbol}: Already in isolated margin")
                    else:
                        print(f"   ⚠️  {symbol}: Margin mode issue: {e}")
                
                # Try to set leverage
                try:
                    await exchange.set_leverage(config.LEVERAGE, symbol)
                    print(f"   ✅ {symbol}: Leverage set to {config.LEVERAGE}x")
                except Exception as e:
                    print(f"   ⚠️  {symbol}: Leverage issue: {e}")
                
            except Exception as e:
                print(f"   ❌ {symbol}: Configuration failed: {e}")
        
        print("\n✅ CONNECTION TEST COMPLETE")
        print("\n🎯 Next Steps:")
        print("   1. If all tests passed, the bot should work correctly")
        print("   2. Start the bot and monitor the first few trades")
        print("   3. Check that positions use isolated margin and correct sizes")
        print("   4. Verify leverage is 10x, not 20x")
        
        await exchange.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

def run_test():
    """Run the async test"""
    import asyncio
    asyncio.run(test_binance_connection())

if __name__ == "__main__":
    run_test()
