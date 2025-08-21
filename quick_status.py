#!/usr/bin/env python3
"""
Quick Kill Switch Test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt

def test_status():
    """Quick status test"""
    try:
        # Import config
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
        
        # Get balance
        balance = exchange.fetch_balance()
        usdt = balance.get('USDT', {})
        print(f"💰 USDT Balance: ${usdt.get('total', 0):.2f}")
        
        # Get positions (simplified)
        print("📊 Checking positions...")
        try:
            positions = exchange.fetch_positions()
            print(f"   Total position records: {len(positions)}")
            
            # Count non-zero positions
            open_count = 0
            for pos in positions:
                size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                if size and float(size) > 0:
                    open_count += 1
                    print(f"   Open: {pos.get('symbol')} {pos.get('side')} {size}")
            
            print(f"   Open positions: {open_count}")
            
        except Exception as e:
            print(f"   ❌ Position error: {e}")
        
        # Get orders
        print("📋 Checking orders...")
        try:
            orders = exchange.fetch_open_orders()
            print(f"   Open orders: {len(orders)}")
            
            for order in orders:
                print(f"   Order: {order.get('symbol')} {order.get('side')} {order.get('amount')}")
                
        except Exception as e:
            print(f"   ❌ Orders error: {e}")
        
        print("✅ Status check complete")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status()
