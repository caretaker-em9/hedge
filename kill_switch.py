#!/usr/bin/env python3
"""
Trading Bot Kill Switch
Emergency tool to close all open positions on Binance Testnet
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ccxt
import asyncio
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('kill_switch.log')
    ]
)
logger = logging.getLogger(__name__)

class KillSwitch:
    def __init__(self):
        """Initialize the kill switch"""
        try:
            import config
            self.config = config
            
            # Initialize exchange
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_TESTNET_API_KEY,
                'secret': config.BINANCE_TESTNET_SECRET,
                'sandbox': True,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future'
                }
            })
            
            logger.info("Kill switch initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize kill switch: {e}")
            raise
    
    async def get_all_positions(self):
        """Get all open positions"""
        try:
            positions = await self.exchange.fetch_positions()
            # Filter only positions with size > 0
            open_positions = [pos for pos in positions if pos['size'] > 0]
            return open_positions
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            return []
    
    async def get_all_orders(self):
        """Get all open orders"""
        try:
            orders = await self.exchange.fetch_open_orders()
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            return []
    
    async def cancel_all_orders(self):
        """Cancel all open orders"""
        logger.info("🚫 Canceling all open orders...")
        
        try:
            orders = await self.get_all_orders()
            if not orders:
                logger.info("   ✅ No open orders to cancel")
                return True
            
            logger.info(f"   Found {len(orders)} open orders")
            
            canceled_count = 0
            failed_count = 0
            
            for order in orders:
                try:
                    symbol = order['symbol']
                    order_id = order['id']
                    
                    await self.exchange.cancel_order(order_id, symbol)
                    logger.info(f"   ✅ Canceled order {order_id} for {symbol}")
                    canceled_count += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to cancel order {order_id}: {e}")
                    failed_count += 1
            
            logger.info(f"   📊 Orders canceled: {canceled_count}, Failed: {failed_count}")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False
    
    async def close_position(self, position):
        """Close a single position"""
        symbol = position['symbol']
        size = abs(position['size'])
        side = 'sell' if position['side'] == 'long' else 'buy'
        
        try:
            # Create market order to close position
            order = await self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=size,
                params={
                    'reduceOnly': True,  # This ensures we're closing, not opening
                    'marginMode': 'isolated'
                }
            )
            
            logger.info(f"   ✅ Closed {position['side']} position: {size} {symbol}")
            return True, order
            
        except Exception as e:
            logger.error(f"   ❌ Failed to close {symbol} position: {e}")
            return False, None
    
    async def close_all_positions(self):
        """Close all open positions"""
        logger.info("💥 Closing all open positions...")
        
        try:
            positions = await self.get_all_positions()
            if not positions:
                logger.info("   ✅ No open positions to close")
                return True
            
            logger.info(f"   Found {len(positions)} open positions")
            
            closed_count = 0
            failed_count = 0
            total_pnl = 0
            
            for position in positions:
                symbol = position['symbol']
                side = position['side']
                size = position['size']
                pnl = position.get('unrealizedPnl', 0) or 0
                
                logger.info(f"   🎯 Closing {side} {size} {symbol} (PnL: ${pnl:.2f})")
                
                success, order = await self.close_position(position)
                if success:
                    closed_count += 1
                    total_pnl += pnl
                else:
                    failed_count += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
            
            logger.info(f"   📊 Positions closed: {closed_count}, Failed: {failed_count}")
            logger.info(f"   💰 Total unrealized PnL closed: ${total_pnl:.2f}")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Failed to close positions: {e}")
            return False
    
    async def get_account_summary(self):
        """Get account summary before/after kill switch"""
        try:
            balance = await self.exchange.fetch_balance()
            positions = await self.get_all_positions()
            orders = await self.get_all_orders()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'balance': {
                    'total': balance.get('USDT', {}).get('total', 0),
                    'free': balance.get('USDT', {}).get('free', 0),
                    'used': balance.get('USDT', {}).get('used', 0)
                },
                'open_positions': len(positions),
                'open_orders': len(orders),
                'positions_detail': [
                    {
                        'symbol': pos['symbol'],
                        'side': pos['side'],
                        'size': pos['size'],
                        'unrealized_pnl': pos.get('unrealizedPnl', 0)
                    } for pos in positions
                ],
                'orders_detail': [
                    {
                        'symbol': order['symbol'],
                        'side': order['side'],
                        'amount': order['amount'],
                        'type': order['type'],
                        'status': order['status']
                    } for order in orders
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            return None
    
    async def execute_kill_switch(self, confirm=False):
        """Execute the kill switch - close all positions and orders"""
        
        if not confirm:
            print("\n" + "="*60)
            print("🚨 TRADING BOT KILL SWITCH 🚨")
            print("="*60)
            print("⚠️  WARNING: This will close ALL open positions and orders!")
            print("⚠️  This action cannot be undone!")
            print("="*60)
            
            response = input("\nType 'KILL' to confirm execution: ").strip()
            if response != 'KILL':
                print("❌ Kill switch aborted by user")
                return False
        
        logger.info("🚨 KILL SWITCH ACTIVATED")
        logger.info("="*60)
        
        # Get pre-execution summary
        logger.info("📊 Getting account status before kill switch...")
        pre_summary = await self.get_account_summary()
        
        if pre_summary:
            logger.info(f"   Balance: ${pre_summary['balance']['total']:.2f}")
            logger.info(f"   Open positions: {pre_summary['open_positions']}")
            logger.info(f"   Open orders: {pre_summary['open_orders']}")
            
            if pre_summary['open_positions'] == 0 and pre_summary['open_orders'] == 0:
                logger.info("✅ No open positions or orders found. Nothing to close.")
                return True
        
        # Step 1: Cancel all orders
        orders_success = await self.cancel_all_orders()
        
        # Step 2: Close all positions
        positions_success = await self.close_all_positions()
        
        # Step 3: Get post-execution summary
        logger.info("📊 Getting account status after kill switch...")
        await asyncio.sleep(2)  # Wait for orders to settle
        post_summary = await self.get_account_summary()
        
        if post_summary:
            logger.info(f"   Final balance: ${post_summary['balance']['total']:.2f}")
            logger.info(f"   Remaining positions: {post_summary['open_positions']}")
            logger.info(f"   Remaining orders: {post_summary['open_orders']}")
        
        # Save summary to file
        summary_data = {
            'execution_time': datetime.now().isoformat(),
            'pre_execution': pre_summary,
            'post_execution': post_summary,
            'orders_canceled': orders_success,
            'positions_closed': positions_success
        }
        
        with open('kill_switch_report.json', 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        success = orders_success and positions_success
        
        if success:
            logger.info("✅ KILL SWITCH COMPLETED SUCCESSFULLY")
            if post_summary and (post_summary['open_positions'] > 0 or post_summary['open_orders'] > 0):
                logger.warning("⚠️  Some positions/orders may still remain. Check manually.")
        else:
            logger.error("❌ KILL SWITCH COMPLETED WITH ERRORS")
            logger.error("⚠️  Some positions/orders may not have been closed. Check manually.")
        
        logger.info("📋 Detailed report saved to: kill_switch_report.json")
        
        return success

def main():
    """Main function"""
    print("\n🚨 Trading Bot Kill Switch")
    print("Emergency tool to close all open positions")
    print("-" * 50)
    
    # Check for command line arguments
    confirm = '--confirm' in sys.argv
    status_only = '--status' in sys.argv
    
    async def run():
        try:
            kill_switch = KillSwitch()
            
            if status_only:
                print("📊 Getting current account status...")
                summary = await kill_switch.get_account_summary()
                if summary:
                    print(f"\n💰 Balance: ${summary['balance']['total']:.2f}")
                    print(f"📈 Open Positions: {summary['open_positions']}")
                    print(f"📋 Open Orders: {summary['open_orders']}")
                    
                    if summary['positions_detail']:
                        print("\n🎯 Open Positions:")
                        for pos in summary['positions_detail']:
                            pnl = pos['unrealized_pnl']
                            pnl_str = f"${pnl:.2f}" if pnl else "N/A"
                            print(f"   {pos['symbol']}: {pos['side']} {pos['size']} (PnL: {pnl_str})")
                    
                    if summary['orders_detail']:
                        print("\n📋 Open Orders:")
                        for order in summary['orders_detail']:
                            print(f"   {order['symbol']}: {order['side']} {order['amount']} ({order['type']})")
                else:
                    print("❌ Failed to get account status")
            else:
                success = await kill_switch.execute_kill_switch(confirm=confirm)
                if success:
                    print("\n✅ Kill switch executed successfully!")
                else:
                    print("\n❌ Kill switch completed with errors!")
                    
        except KeyboardInterrupt:
            print("\n❌ Kill switch interrupted by user")
        except Exception as e:
            logger.error(f"Kill switch failed: {e}")
            print(f"\n❌ Kill switch failed: {e}")
    
    # Run the async function
    asyncio.run(run())

if __name__ == "__main__":
    print("\nUsage:")
    print("  python kill_switch.py          # Interactive mode")
    print("  python kill_switch.py --confirm # Auto-confirm execution")
    print("  python kill_switch.py --status  # Check status only")
    print()
    
    main()
