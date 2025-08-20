#!/usr/bin/env python3
"""
Test the hedging strategy implementation
"""

import sys
import time
from datetime import datetime
from trading_bot import TradingBot, BotConfig, HedgePair, Trade

def test_hedging_strategy():
    """Test the hedging strategy logic"""
    print("Testing Hedging Strategy Implementation")
    print("=" * 50)
    
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
    
    # Initialize bot
    bot = TradingBot(config)
    
    print(f"Initial Balance: ${config.initial_balance}")
    print(f"Hedge Strategy Configuration:")
    print(f"  - Initial Trade Size: ${config.initial_trade_size}")
    print(f"  - Long Position Size: ${config.long_position_size}")
    print(f"  - Short Position Size: ${config.short_position_size}")
    print(f"  - Hedge Trigger: {config.hedge_trigger_loss:.1%}")
    print(f"  - Max Pairs: {config.max_trades}")
    print()
    
    # Test 1: Create initial long position
    print("Test 1: Creating initial long position")
    analysis = {
        'signal': 'buy',
        'price': 100.0,
        'ewo': 5.0,
        'rsi': 60
    }
    
    bot.execute_trade('ETH/USDT', 'buy', analysis)
    
    print(f"Hedge pairs created: {len(bot.hedge_pairs)}")
    if bot.hedge_pairs:
        pair = bot.hedge_pairs[0]
        print(f"  Symbol: {pair.symbol}")
        print(f"  Status: {pair.status}")
        print(f"  Long trade price: ${pair.long_trade.price if pair.long_trade else 'None'}")
    print()
    
    # Test 2: Simulate price drop to trigger hedge
    print("Test 2: Simulating price drop to trigger hedge")
    if bot.hedge_pairs:
        pair = bot.hedge_pairs[0]
        
        # Mock the current price to simulate 6% loss
        original_get_price = bot._get_current_price
        def mock_get_price(symbol):
            if symbol == 'ETH/USDT':
                return 94.0  # 6% drop from 100
            return original_get_price(symbol)
        
        bot._get_current_price = mock_get_price
        
        # Check hedge trigger
        bot.check_hedge_triggers()
        
        print(f"Hedge pair status: {pair.status}")
        print(f"Short trade created: {'Yes' if pair.short_trade else 'No'}")
        if pair.short_trade:
            print(f"  Short trade price: ${pair.short_trade.price}")
    print()
    
    # Test 3: Simulate profitable hedge exit
    print("Test 3: Simulating profitable hedge for exit")
    if bot.hedge_pairs and bot.hedge_pairs[0].status == 'hedged':
        pair = bot.hedge_pairs[0]
        
        # Mock price recovery that makes hedge profitable
        def mock_get_price_recovery(symbol):
            if symbol == 'ETH/USDT':
                return 89.0  # Further drop makes short more profitable
            return original_get_price(symbol)
        
        bot._get_current_price = mock_get_price_recovery
        
        # Check hedge exit
        bot.check_hedge_exits()
        
        print(f"Hedge pair status: {pair.status}")
        print(f"Long trade status: {pair.long_trade.status if pair.long_trade else 'None'}")
        print(f"Short trade status: {pair.short_trade.status if pair.short_trade else 'None'}")
    print()
    
    # Summary
    print("Summary:")
    print(f"Total trades executed: {len(bot.trades)}")
    print(f"Total hedge pairs: {len(bot.hedge_pairs)}")
    for i, trade in enumerate(bot.trades, 1):
        print(f"  Trade {i}: {trade.trade_type} {trade.side} {trade.symbol} @ ${trade.price:.2f} - {trade.status}")
    
    print("\nHedging strategy test completed!")

if __name__ == "__main__":
    test_hedging_strategy()
