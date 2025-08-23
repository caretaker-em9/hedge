#!/usr/bin/env python3
"""
Test script to verify leverage information functionality
"""

import json
from trading_bot import TradingBot, BotConfig, Trade
from datetime import datetime

def test_leverage_functionality():
    """Test the leverage functionality"""
    print("Testing leverage functionality...")
    
    # Create a mock trading bot
    try:
        config = BotConfig()
        bot = TradingBot(config)
        print("✅ Trading bot created successfully")
        
        # Test the get_position_leverage method
        test_symbol = "BTC/USDT"
        leverage = bot.get_position_leverage(test_symbol)
        print(f"✅ Leverage for {test_symbol}: {leverage}x")
        
        # Create a mock trade
        mock_trade = Trade(
            id="test_123",
            symbol=test_symbol,
            side="buy",
            amount=0.001,
            price=45000.0,
            timestamp=datetime.now(),
            status="open",
            entry_signal="Test signal"
        )
        
        # Test get_trade_leverage method
        trade_leverage = bot.get_trade_leverage(mock_trade)
        print(f"✅ Trade leverage: {trade_leverage}x")
        
        # Test with web interface API structure
        trade_dict = {
            'id': mock_trade.id,
            'symbol': mock_trade.symbol,
            'side': mock_trade.side,
            'amount': mock_trade.amount,
            'price': mock_trade.price,
            'timestamp': mock_trade.timestamp.isoformat(),
            'status': mock_trade.status,
            'leverage': trade_leverage,
        }
        
        print("✅ Trade dictionary with leverage:")
        print(json.dumps(trade_dict, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing leverage functionality: {e}")
        return False

if __name__ == "__main__":
    success = test_leverage_functionality()
    print(f"\n{'✅ All tests passed!' if success else '❌ Tests failed!'}")
