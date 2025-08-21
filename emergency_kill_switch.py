#!/usr/bin/env python3
"""
Emergency Kill Switch for Binance Testnet
Simple and reliable version
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import json
from datetime import datetime

def print_header():
    """Print header"""
    print("\n" + "="*60)
    print("🚨 BINANCE TESTNET KILL SWITCH 🚨")
    print("="*60)

def get_exchange():
    """Initialize exchange connection"""
    try:
        import config
        
        exchange = ccxt.binance({
            'apiKey': config.BINANCE_TESTNET_API_KEY,
            'secret': config.BINANCE_TESTNET_SECRET,
            'sandbox': True,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
                'warnOnFetchOpenOrdersWithoutSymbol': False
            }
        })
        
        return exchange
    except Exception as e:
        print(f"❌ Failed to initialize exchange: {e}")
        return None

def check_status(exchange):
    """Check account status"""
    print("📊 Checking account status...")
    
    try:
        # Get balance
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('total', 0)
        print(f"💰 USDT Balance: ${usdt_balance:.2f}")
        
        # Get open orders
        orders = exchange.fetch_open_orders()
        print(f"📋 Open Orders: {len(orders)}")
        
        if orders:
            for order in orders:
                print(f"   • {order['symbol']}: {order['side']} {order['amount']} @ {order.get('price', 'Market')}")
        
        # Get positions - try different approaches
        positions_data = []
        
        try:
            # Method 1: fetch_positions()
            all_positions = exchange.fetch_positions()
            print(f"📈 Total position records: {len(all_positions)}")
            
            for pos in all_positions:
                # Check multiple size fields
                size = 0
                if 'size' in pos and pos['size']:
                    size = float(pos['size'])
                elif 'contracts' in pos and pos['contracts']:
                    size = float(pos['contracts'])
                elif 'amount' in pos and pos['amount']:
                    size = float(pos['amount'])
                
                if size > 0:
                    positions_data.append({
                        'symbol': pos.get('symbol', 'Unknown'),
                        'side': pos.get('side', 'Unknown'),
                        'size': size,
                        'unrealized_pnl': pos.get('unrealizedPnl', 0) or 0
                    })
            
        except Exception as e:
            print(f"   ⚠️ fetch_positions() failed: {e}")
            
            # Method 2: Try account info
            try:
                account = exchange.fetch_account()
                print("   Trying account info method...")
                # This method varies by exchange
            except Exception as e2:
                print(f"   ⚠️ fetch_account() also failed: {e2}")
        
        print(f"📈 Open Positions: {len(positions_data)}")
        
        total_pnl = 0
        if positions_data:
            for pos in positions_data:
                pnl = pos['unrealized_pnl']
                total_pnl += pnl
                print(f"   • {pos['symbol']}: {pos['side']} {pos['size']} (PnL: ${pnl:.2f})")
            
            print(f"💹 Total Unrealized PnL: ${total_pnl:.2f}")
        
        return {
            'balance': usdt_balance,
            'orders': orders,
            'positions': positions_data,
            'total_pnl': total_pnl
        }
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return None

def cancel_orders(exchange, orders):
    """Cancel all open orders"""
    if not orders:
        print("✅ No orders to cancel")
        return True
    
    print(f"\n🚫 Canceling {len(orders)} orders...")
    
    success_count = 0
    for order in orders:
        try:
            exchange.cancel_order(order['id'], order['symbol'])
            print(f"   ✅ Canceled {order['symbol']} order")
            success_count += 1
        except Exception as e:
            print(f"   ❌ Failed to cancel {order['symbol']}: {e}")
    
    print(f"📊 Canceled: {success_count}/{len(orders)}")
    return success_count == len(orders)

def close_positions(exchange, positions):
    """Close all open positions"""
    if not positions:
        print("✅ No positions to close")
        return True
    
    print(f"\n💥 Closing {len(positions)} positions...")
    
    success_count = 0
    for pos in positions:
        try:
            symbol = pos['symbol']
            size = abs(pos['size'])
            side = 'sell' if pos['side'] == 'long' else 'buy'
            
            print(f"   🎯 Closing {pos['side']} {size} {symbol}")
            
            order = exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=size,
                params={
                    'reduceOnly': True,
                    'marginMode': 'isolated'
                }
            )
            
            print(f"   ✅ Closed {symbol} position")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to close {symbol}: {e}")
    
    print(f"📊 Closed: {success_count}/{len(positions)}")
    return success_count == len(positions)

def main():
    """Main function"""
    print_header()
    
    # Parse arguments
    if len(sys.argv) > 1:
        if '--status' in sys.argv:
            mode = 'status'
        elif '--kill' in sys.argv:
            mode = 'kill'
        else:
            print("Usage:")
            print("  python emergency_kill_switch.py --status  # Check status only")
            print("  python emergency_kill_switch.py --kill    # Execute kill switch")
            return
    else:
        print("Available modes:")
        print("  --status : Check current positions and orders")
        print("  --kill   : Close all positions and cancel all orders")
        print()
        mode = input("Enter mode (status/kill): ").strip().lower()
        if mode not in ['status', 'kill']:
            print("❌ Invalid mode")
            return
    
    # Initialize exchange
    exchange = get_exchange()
    if not exchange:
        return
    
    print("✅ Connected to Binance Testnet")
    
    # Check status
    status = check_status(exchange)
    if not status:
        return
    
    if mode == 'status':
        print("\n✅ Status check complete!")
        return
    
    # Kill switch mode
    if len(status['orders']) == 0 and len(status['positions']) == 0:
        print("\n✅ No positions or orders to close!")
        return
    
    print(f"\n⚠️ About to close:")
    print(f"   • {len(status['orders'])} open orders")
    print(f"   • {len(status['positions'])} open positions")
    print(f"   • Total PnL: ${status['total_pnl']:.2f}")
    
    confirm = input("\nType 'KILL' to confirm: ").strip()
    if confirm != 'KILL':
        print("❌ Aborted by user")
        return
    
    print(f"\n🚨 EXECUTING KILL SWITCH - {datetime.now()}")
    print("="*60)
    
    # Execute kill switch
    orders_success = cancel_orders(exchange, status['orders'])
    positions_success = close_positions(exchange, status['positions'])
    
    # Final check
    print("\n📊 Verifying results...")
    import time
    time.sleep(2)
    final_status = check_status(exchange)
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'initial': {
            'orders': len(status['orders']),
            'positions': len(status['positions']),
            'pnl': status['total_pnl']
        },
        'final': {
            'orders': len(final_status['orders']) if final_status else 'unknown',
            'positions': len(final_status['positions']) if final_status else 'unknown'
        },
        'success': orders_success and positions_success
    }
    
    with open('kill_switch_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'✅' if report['success'] else '❌'} Kill switch completed")
    print("📋 Report saved to: kill_switch_report.json")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
