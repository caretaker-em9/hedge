#!/usr/bin/env python3
"""
Simple Kill Switch (Synchronous)
Emergency tool to close all open positions on Binance Testnet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import logging
from datetime import datetime
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleKillSwitch:
    def __init__(self):
        """Initialize the kill switch"""
        try:
            import config
            self.config = config
            
            # Initialize exchange (sync version)
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_TESTNET_API_KEY,
                'secret': config.BINANCE_TESTNET_SECRET,
                'sandbox': True,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future'
                }
            })
            
            print("✅ Kill switch initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize kill switch: {e}")
            raise
    
    def get_account_status(self):
        """Get current account status"""
        try:
            print("📊 Getting account status...")
            
            # Get balance
            balance = self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {})
            
            # Get positions
            positions = self.exchange.fetch_positions()
            open_positions = []
            for pos in positions:
                # Handle different size field names
                size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                if size > 0:
                    open_positions.append(pos)
            
            # Get orders  
            open_orders = self.exchange.fetch_open_orders()
            
            print(f"\n💰 USDT Balance:")
            print(f"   Total: ${usdt_balance.get('total', 0):.2f}")
            print(f"   Free: ${usdt_balance.get('free', 0):.2f}")
            print(f"   Used: ${usdt_balance.get('used', 0):.2f}")
            
            print(f"\n📈 Open Positions: {len(open_positions)}")
            total_unrealized_pnl = 0
            
            if open_positions:
                for pos in open_positions:
                    pnl = pos.get('unrealizedPnl', 0) or 0
                    total_unrealized_pnl += pnl
                    
                    size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                    
                    print(f"   {pos['symbol']}: {pos.get('side', 'unknown')} {size}")
                    print(f"      Entry: ${pos.get('entryPrice', 0):.4f}")
                    print(f"      Mark: ${pos.get('markPrice', 0):.4f}")
                    print(f"      PnL: ${pnl:.2f}")
                
                print(f"\n💹 Total Unrealized PnL: ${total_unrealized_pnl:.2f}")
            
            print(f"\n📋 Open Orders: {len(open_orders)}")
            if open_orders:
                for order in open_orders:
                    print(f"   {order['symbol']}: {order['side']} {order['amount']} @ ${order.get('price', 'Market')}")
            
            return {
                'balance': usdt_balance,
                'positions': open_positions,
                'orders': open_orders,
                'total_pnl': total_unrealized_pnl
            }
            
        except Exception as e:
            print(f"❌ Failed to get account status: {e}")
            return None
    
    def cancel_all_orders(self):
        """Cancel all open orders"""
        print("\n🚫 Canceling all open orders...")
        
        try:
            orders = self.exchange.fetch_open_orders()
            if not orders:
                print("   ✅ No open orders to cancel")
                return True
            
            print(f"   Found {len(orders)} open orders")
            
            canceled_count = 0
            failed_count = 0
            
            for order in orders:
                try:
                    symbol = order['symbol']
                    order_id = order['id']
                    
                    self.exchange.cancel_order(order_id, symbol)
                    print(f"   ✅ Canceled {symbol} order {order_id}")
                    canceled_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to cancel order {order_id}: {e}")
                    failed_count += 1
                
                time.sleep(0.1)  # Small delay
            
            print(f"   📊 Result: {canceled_count} canceled, {failed_count} failed")
            return failed_count == 0
            
        except Exception as e:
            print(f"❌ Failed to cancel orders: {e}")
            return False
    
    def close_all_positions(self):
        """Close all open positions"""
        print("\n💥 Closing all open positions...")
        
        try:
            positions = self.exchange.fetch_positions()
            open_positions = []
            for pos in positions:
                # Handle different size field names
                size = pos.get('size', 0) or pos.get('contracts', 0) or 0
                if size > 0:
                    open_positions.append(pos)
            
            if not open_positions:
                print("   ✅ No open positions to close")
                return True
            
            print(f"   Found {len(open_positions)} open positions")
            
            closed_count = 0
            failed_count = 0
            
            for position in open_positions:
                try:
                    symbol = position['symbol']
                    size = position.get('size', 0) or position.get('contracts', 0) or 0
                    size = abs(size)
                    side = 'sell' if position.get('side') == 'long' else 'buy'
                    
                    print(f"   🎯 Closing {position.get('side', 'unknown')} {size} {symbol}")
                    
                    # Create market order to close position
                    order = self.exchange.create_market_order(
                        symbol=symbol,
                        side=side,
                        amount=size,
                        params={
                            'reduceOnly': True,
                            'marginMode': 'isolated'
                        }
                    )
                    
                    print(f"   ✅ Closed {symbol} position")
                    closed_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to close {symbol}: {e}")
                    failed_count += 1
                
                time.sleep(0.2)  # Small delay
            
            print(f"   📊 Result: {closed_count} closed, {failed_count} failed")
            return failed_count == 0
            
        except Exception as e:
            print(f"❌ Failed to close positions: {e}")
            return False
    
    def execute_kill_switch(self, confirm=False):
        """Execute the kill switch"""
        
        print("\n" + "="*60)
        print("🚨 TRADING BOT KILL SWITCH 🚨")
        print("="*60)
        
        # Get initial status
        print("📊 Current account status:")
        initial_status = self.get_account_status()
        
        if not initial_status:
            print("❌ Cannot get account status. Aborting.")
            return False
        
        # Check if there's anything to close
        if len(initial_status['positions']) == 0 and len(initial_status['orders']) == 0:
            print("\n✅ No open positions or orders found. Nothing to close.")
            return True
        
        # Confirmation
        if not confirm:
            print("\n⚠️  WARNING: This will close ALL open positions and orders!")
            print("⚠️  This action cannot be undone!")
            print("="*60)
            
            response = input("\nType 'KILL' to confirm execution: ").strip()
            if response != 'KILL':
                print("❌ Kill switch aborted by user")
                return False
        
        print(f"\n🚨 EXECUTING KILL SWITCH at {datetime.now()}")
        print("="*60)
        
        # Step 1: Cancel all orders
        orders_success = self.cancel_all_orders()
        
        # Step 2: Close all positions  
        positions_success = self.close_all_positions()
        
        # Step 3: Final status
        print("\n📊 Final account status:")
        time.sleep(2)  # Wait for orders to settle
        final_status = self.get_account_status()
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'initial_status': {
                'positions': len(initial_status['positions']),
                'orders': len(initial_status['orders']),
                'total_pnl': initial_status['total_pnl']
            },
            'final_status': {
                'positions': len(final_status['positions']) if final_status else 'unknown',
                'orders': len(final_status['orders']) if final_status else 'unknown'
            },
            'success': {
                'orders_canceled': orders_success,
                'positions_closed': positions_success
            }
        }
        
        with open('kill_switch_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        success = orders_success and positions_success
        
        print("\n" + "="*60)
        if success:
            print("✅ KILL SWITCH COMPLETED SUCCESSFULLY")
        else:
            print("❌ KILL SWITCH COMPLETED WITH ERRORS")
            print("⚠️  Some positions/orders may not have been closed!")
        
        print("📋 Detailed report saved to: kill_switch_report.json")
        print("="*60)
        
        return success

def main():
    """Main function"""
    print("🚨 Trading Bot Kill Switch")
    print("Emergency tool to close all open positions")
    print("-" * 50)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if '--status' in sys.argv:
            try:
                kill_switch = SimpleKillSwitch()
                kill_switch.get_account_status()
            except Exception as e:
                print(f"❌ Error: {e}")
            return
        elif '--confirm' in sys.argv:
            confirm = True
        else:
            print("Usage:")
            print("  python simple_kill_switch.py          # Interactive mode")
            print("  python simple_kill_switch.py --status # Check status only") 
            print("  python simple_kill_switch.py --confirm # Auto-confirm")
            return
    else:
        confirm = False
    
    try:
        kill_switch = SimpleKillSwitch()
        success = kill_switch.execute_kill_switch(confirm=confirm)
        
        if success:
            print("\n🎉 All done! Check the report for details.")
        else:
            print("\n⚠️  Please check manually for any remaining positions.")
            
    except KeyboardInterrupt:
        print("\n❌ Kill switch interrupted by user")
    except Exception as e:
        print(f"\n❌ Kill switch failed: {e}")

if __name__ == "__main__":
    main()
