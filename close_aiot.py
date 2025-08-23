#!/usr/bin/env python3
"""
Manual Position Closer
Close specific position with different order types
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import time

def close_aiot_position():
    """Close AIOT position manually"""
    print("🎯 Manual AIOT Position Closer")
    print("=" * 40)
    
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
        
        symbol = 'AIOT/USDT'
        
        # Get current position
        positions = exchange.fetch_positions([symbol])
        aiot_position = None
        
        for pos in positions:
            if pos['symbol'] == symbol and pos['size'] > 0:
                aiot_position = pos
                break
        
        if not aiot_position:
            print("✅ No AIOT position found - already closed")
            return
        
        print(f"📊 Current AIOT position:")
        print(f"   Size: {aiot_position['size']}")
        print(f"   Side: {aiot_position['side']}")
        print(f"   Entry Price: ${aiot_position.get('entryPrice', 0)}")
        print(f"   Mark Price: ${aiot_position.get('markPrice', 0)}")
        
        # Get current market price
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        print(f"   Current Price: ${current_price}")
        
        size = abs(aiot_position['size'])
        side = 'sell' if aiot_position['side'] == 'long' else 'buy'
        
        # Try different order types
        methods = [
            ('Market Order', lambda: exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=size,
                params={'reduceOnly': True, 'marginMode': 'isolated'}
            )),
            ('Limit Order at current price', lambda: exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=size,
                price=current_price * 0.98 if side == 'sell' else current_price * 1.02,  # Slightly better price
                params={'reduceOnly': True, 'marginMode': 'isolated'}
            )),
            ('Stop Market Order', lambda: exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=side,
                amount=size,
                params={
                    'stopPrice': current_price * 0.99 if side == 'sell' else current_price * 1.01,
                    'reduceOnly': True,
                    'marginMode': 'isolated'
                }
            ))
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"\n🔄 Trying {method_name}...")
                result = method_func()
                print(f"✅ {method_name} successful: {result['id']}")
                
                # Wait and check if position is closed
                time.sleep(2)
                positions = exchange.fetch_positions([symbol])
                remaining_position = None
                for pos in positions:
                    if pos['symbol'] == symbol and pos['size'] > 0:
                        remaining_position = pos
                        break
                
                if not remaining_position:
                    print("🎉 AIOT position successfully closed!")
                    return
                else:
                    print(f"⚠️  Position still open with size: {remaining_position['size']}")
                
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
        
        print("\n❌ All methods failed to close AIOT position")
        print("💡 You may need to close it manually through Binance interface")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    close_aiot_position()
