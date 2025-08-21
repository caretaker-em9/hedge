#!/usr/bin/env python3
"""
Debug Entry Signals
Check why no entry signals are being generated
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import ccxt
from datetime import datetime

def debug_entry_signals():
    """Debug entry signal generation"""
    print("🔍 DEBUG: Entry Signal Generation")
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
        
        # Check current positions
        try:
            positions = exchange.fetch_positions()
            open_positions = []
            for pos in positions:
                size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                if size and float(size) > 0:
                    open_positions.append(pos)
            
            print(f"📈 Current open positions: {len(open_positions)}")
            if open_positions:
                for pos in open_positions:
                    size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                    print(f"   • {pos.get('symbol')}: {pos.get('side')} {size}")
            
        except Exception as e:
            print(f"⚠️ Could not check positions: {e}")
        
        # Check trading configuration
        print(f"\n📋 Trading Configuration:")
        print(f"   MAX_TRADES: {config.MAX_TRADES}")
        print(f"   ONE_TRADE_PER_PAIR: {config.ONE_TRADE_PER_PAIR}")
        print(f"   LONG_POSITION_SIZE: ${config.LONG_POSITION_SIZE}")
        print(f"   FILTER_BY_VOLUME: {config.FILTER_BY_VOLUME}")
        print(f"   MIN_24H_VOLUME: ${config.MIN_24H_VOLUME:,}")
        
        # Test getting symbol data
        print(f"\n📊 Testing symbol data...")
        test_symbol = 'BTC/USDT'
        
        try:
            # Get current ticker
            ticker = exchange.fetch_ticker(test_symbol)
            print(f"   {test_symbol} Price: ${ticker['last']:,.2f}")
            print(f"   24h Volume: ${ticker.get('quoteVolume', 0):,.0f}")
            
            # Get OHLCV data
            ohlcv = exchange.fetch_ohlcv(test_symbol, config.TIMEFRAME, limit=100)
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                print(f"   OHLCV data: {len(df)} candles")
                print(f"   Latest close: ${df['close'].iloc[-1]:,.2f}")
                print(f"   Latest timestamp: {df['timestamp'].iloc[-1]}")
                
                # Check if volume meets minimum
                latest_volume = ticker.get('quoteVolume', 0)
                if latest_volume >= config.MIN_24H_VOLUME:
                    print(f"   ✅ Volume meets minimum requirement")
                else:
                    print(f"   ❌ Volume below minimum ({latest_volume:,.0f} < {config.MIN_24H_VOLUME:,})")
                    
            else:
                print("   ❌ No OHLCV data received")
                
        except Exception as e:
            print(f"   ❌ Error getting {test_symbol} data: {e}")
        
        # Check strategy parameters
        print(f"\n⚙️ Strategy Parameters:")
        params = config.STRATEGY_PARAMS
        for key, value in params.items():
            print(f"   {key}: {value}")
        
        # Suggestion
        print(f"\n💡 Possible reasons for no signals:")
        print(f"   1. Market conditions don't meet entry criteria")
        print(f"   2. Already at max trades ({config.MAX_TRADES})")
        print(f"   3. Symbols don't meet volume requirements")
        print(f"   4. Technical indicators don't align")
        print(f"   5. ONE_TRADE_PER_PAIR=True limits new entries")
        
        print(f"\n🎯 To test entry signals:")
        print(f"   1. Lower MIN_24H_VOLUME temporarily")
        print(f"   2. Adjust strategy parameters to be less strict")
        print(f"   3. Close existing positions to allow new entries")
        print(f"   4. Check if specific symbols are being filtered out")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_entry_signals()
