#!/usr/bin/env python3
"""
Demo the hedging strategy with mock exchange
"""

import sys
import time
from datetime import datetime
from trading_bot import TradingBot, BotConfig, HedgePair, Trade

class MockExchange:
    """Mock exchange for testing"""
    def __init__(self):
        self.orders = []
        self.order_id = 1000
    
    def create_market_order(self, symbol, side, amount, params=None):
        order = {
            'id': str(self.order_id),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'params': params or {}
        }
        self.orders.append(order)
        self.order_id += 1
        return order
    
    def fetch_ticker(self, symbol):
        # Return mock prices based on symbol
        if symbol == 'ETH/USDT':
            return {'last': 100.0}  # Default price
        return {'last': 50.0}

def test_hedging_demo():
    """Demo the complete hedging strategy"""
    print("🚀 Hedging Strategy Demo")
    print("=" * 60)
    
    # Create configuration with hedging parameters
    config = BotConfig(
        initial_balance=100.0,
        max_trades=3,
        leverage=10.0,
        initial_trade_size=30.0,
        long_position_size=10.0,
        short_position_size=15.0,
        hedge_trigger_loss=-0.05,
        one_trade_per_pair=True,
        exit_when_hedged=True,
        min_hedge_profit_ratio=1.0
    )
    
    # Initialize bot with mock exchange
    bot = TradingBot(config)
    bot.exchange = MockExchange()  # Replace with mock
    
    print(f"💰 Initial Balance: ${config.initial_balance}")
    print(f"⚙️  Hedge Strategy Configuration:")
    print(f"   • Initial Trade Size: ${config.initial_trade_size}")
    print(f"   • Long Position Size: ${config.long_position_size}")
    print(f"   • Short Position Size: ${config.short_position_size}")
    print(f"   • Hedge Trigger: {config.hedge_trigger_loss:.1%}")
    print(f"   • Max Pairs: {config.max_trades}")
    print()
    
    # Step 1: Create initial long position
    print("📈 Step 1: Creating initial long position")
    analysis = {
        'signal': 'buy',
        'price': 100.0,
        'ewo': 5.0,
        'rsi': 60
    }
    
    bot.execute_trade('ETH/USDT', 'buy', analysis)
    
    if bot.hedge_pairs:
        pair = bot.hedge_pairs[0]
        print(f"   ✅ Hedge pair created for {pair.symbol}")
        print(f"   📊 Status: {pair.status}")
        print(f"   💵 Long position: ${pair.long_trade.price:.2f} × {pair.long_trade.amount/config.leverage:.1f} (${pair.long_size} with {config.leverage}x leverage)")
        print(f"   🆔 Pair ID: {pair.pair_id}")
    else:
        print("   ❌ No hedge pair created")
    print()
    
    # Step 2: Simulate price drop to trigger hedge
    print("📉 Step 2: Simulating 6% price drop to trigger hedge")
    print(f"   📊 Price drops from $100 to $94 (-6%)")
    print(f"   ⚠️  Trigger threshold: {config.hedge_trigger_loss:.1%}")
    
    if bot.hedge_pairs:
        pair = bot.hedge_pairs[0]
        
        # Mock current price for hedge trigger
        current_price = 94.0
        pnl_pct = (current_price - pair.long_trade.price) / pair.long_trade.price
        print(f"   📈 Long position P&L: {pnl_pct:.1%}")
        
        # Override get_current_price method
        def mock_get_price(symbol):
            return 94.0 if symbol == 'ETH/USDT' else 50.0
        
        bot._get_current_price = mock_get_price
        
        # Check hedge trigger
        bot.check_hedge_triggers()
        
        print(f"   🔄 Hedge pair status: {pair.status}")
        if pair.short_trade:
            print(f"   ✅ Short hedge position created!")
            print(f"   💵 Short position: ${pair.short_trade.price:.2f} × {pair.short_trade.amount/config.leverage:.1f} (${pair.short_size} with {config.leverage}x leverage)")
        else:
            print("   ❌ No short position created")
    print()
    
    # Step 3: Simulate profitable hedge exit
    print("📊 Step 3: Simulating profitable hedge scenario")
    print(f"   📉 Price continues to drop to $85")
    
    if bot.hedge_pairs and bot.hedge_pairs[0].status == 'hedged':
        pair = bot.hedge_pairs[0]
        
        # Mock price for hedge exit calculation
        exit_price = 85.0  # Larger drop for better hedge coverage
        
        def mock_get_price_exit(symbol):
            return 85.0 if symbol == 'ETH/USDT' else 50.0
        
        bot._get_current_price = mock_get_price_exit
        
        # Calculate P&L manually for display
        long_pnl = (exit_price - pair.long_trade.price) * pair.long_trade.amount
        short_pnl = (pair.short_trade.price - exit_price) * pair.short_trade.amount
        
        print(f"   📈 Long P&L: ${long_pnl:.2f} ({((exit_price - pair.long_trade.price) / pair.long_trade.price * 100):.1f}%)")
        print(f"   📈 Short P&L: ${short_pnl:.2f} ({((pair.short_trade.price - exit_price) / pair.short_trade.price * 100):.1f}%)")
        print(f"   📊 Net P&L: ${long_pnl + short_pnl:.2f}")
        
        if long_pnl < 0 and short_pnl > 0:
            hedge_coverage = short_pnl / abs(long_pnl)
            print(f"   🛡️  Hedge coverage: {hedge_coverage:.2f}x (target: {config.min_hedge_profit_ratio:.1f}x)")
            
            if hedge_coverage >= config.min_hedge_profit_ratio:
                print(f"   ✅ Hedge target achieved! Closing both positions...")
                bot.check_hedge_exits()
                print(f"   🔄 Hedge pair status: {pair.status}")
                print(f"   💰 Strategy preserved capital with minimal loss!")
            else:
                print(f"   ⏳ Waiting for better hedge coverage...")
        else:
            print(f"   ⏳ Hedge not yet profitable enough...")
    print()
    
    # Summary
    print("📋 Trading Summary:")
    print(f"   💼 Total trades executed: {len(bot.trades)}")
    print(f"   🔄 Total hedge pairs: {len(bot.hedge_pairs)}")
    print("   📊 Trade Details:")
    
    for i, trade in enumerate(bot.trades, 1):
        status_emoji = "🟢" if trade.status == "open" else "🔴"
        type_emoji = "📈" if trade.side == "buy" else "📉"
        trade_type_text = f"({trade.trade_type})" if trade.trade_type != "normal" else ""
        print(f"      {i}. {status_emoji} {type_emoji} {trade.side.upper()} {trade.symbol} @ ${trade.price:.2f} {trade_type_text}")
    
    if bot.hedge_pairs:
        print("   🛡️  Hedge Pair Status:")
        for i, pair in enumerate(bot.hedge_pairs, 1):
            status_emoji = {"long_only": "🟡", "hedged": "🔵", "closed": "🟢"}.get(pair.status, "⚪")
            print(f"      {i}. {status_emoji} {pair.symbol}: {pair.status}")
    
    print()
    print("🎉 Hedging strategy demo completed!")
    print()
    print("💡 Strategy Summary:")
    print("   1. Start with $10 long position")
    print("   2. If loss reaches -5%, add $15 short hedge")
    print("   3. Close both when hedge profit ≥ long loss")
    print("   4. Only one trade pair active at a time")

if __name__ == "__main__":
    test_hedging_demo()
