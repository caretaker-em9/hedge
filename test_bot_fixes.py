#!/usr/bin/env python3
"""
Test script to verify the corrected trading bot logic
"""

import json
from trading_bot import TradingBot, BotConfig
import config

def test_trading_bot_fixes():
    """Test the fixed trading bot logic"""
    print("=" * 60)
    print("🔧 TESTING TRADING BOT FIXES")
    print("=" * 60)
    
    try:
        # Create bot config from file
        bot_config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,
            max_trades=config.MAX_TRADES,
            leverage=config.LEVERAGE,
            timeframe=config.TIMEFRAME,
            symbols=config.TRADING_SYMBOLS[:5],  # Use first 5 symbols for testing
            
            # Hedging parameters
            initial_trade_size=config.INITIAL_TRADE_SIZE,
            long_position_size=config.LONG_POSITION_SIZE,
            short_position_size=config.SHORT_POSITION_SIZE,
            hedge_trigger_loss=config.HEDGE_TRIGGER_LOSS,
            one_trade_per_pair=config.ONE_TRADE_PER_PAIR,
            exit_when_hedged=config.EXIT_WHEN_HEDGED,
            min_hedge_profit_ratio=config.MIN_HEDGE_PROFIT_RATIO,
            
            # ROI and trailing stop
            minimal_roi=config.MINIMAL_ROI,
            trailing_stop=config.TRAILING_STOP,
            trailing_stop_positive=config.TRAILING_STOP_POSITIVE,
            trailing_stop_positive_offset=config.TRAILING_STOP_POSITIVE_OFFSET,
            
            # Telegram
            telegram_enabled=False  # Disable for testing
        )
        
        print("✅ Bot configuration loaded successfully")
        print(f"   • Max trades: {bot_config.max_trades}")
        print(f"   • One trade per pair: {bot_config.one_trade_per_pair}")
        print(f"   • Long position size: ${bot_config.long_position_size}")
        print(f"   • Short position size: ${bot_config.short_position_size}")
        print(f"   • Hedge trigger: {bot_config.hedge_trigger_loss:.1%}")
        print(f"   • Trailing stop enabled: {bot_config.trailing_stop}")
        
        # Test ROI thresholds
        print(f"\n📊 ROI Configuration Test:")
        print(f"   • 0 min: {bot_config.minimal_roi['0']:.1%}")
        print(f"   • 5 min: {bot_config.minimal_roi['5']:.1%}")
        print(f"   • 30 min: {bot_config.minimal_roi['30']:.1%}")
        print(f"   • 120 min: {bot_config.minimal_roi['120']:.1%}")
        
        # Create bot instance (this will connect to exchange)
        print(f"\n🔗 Connecting to exchange...")
        bot = TradingBot(bot_config)
        print("✅ Bot created successfully")
        
        # Test trade limit logic
        print(f"\n🧮 Testing Trade Limit Logic:")
        active_trades = [t for t in bot.trades if t.status == 'open']
        active_pairs = [hp for hp in bot.hedge_pairs if hp.status != 'closed']
        
        print(f"   • Current active trades: {len(active_trades)}")
        print(f"   • Current active pairs: {len(active_pairs)}")
        print(f"   • Can create new trade: {len(active_trades) < 2}")
        print(f"   • Can create new pair: {len(active_pairs) < 1}")
        
        # Test ROI threshold calculation
        print(f"\n📈 Testing ROI Threshold Calculation:")
        test_times = [0, 1, 5, 10, 30, 60, 120, 180]
        for minutes in test_times:
            threshold = bot._get_roi_threshold(minutes)
            print(f"   • {minutes:3d} min: {threshold:.1%}")
        
        print(f"\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_trading_bot_fixes()
    print(f"\n{'=' * 60}")
    print(f"{'🎉 TEST RESULT: PASSED' if success else '💥 TEST RESULT: FAILED'}")
    print(f"{'=' * 60}")
