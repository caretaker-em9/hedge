#!/usr/bin/env python3
"""
Trading Bot Diagnostics
Check configuration and exchange settings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingBot, BotConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_diagnostics():
    """Run comprehensive diagnostics"""
    print("🔍 TRADING BOT DIAGNOSTICS")
    print("=" * 60)
    
    try:
        # Load configuration
        import config
        
        print("📋 Configuration Check:")
        print(f"   Initial Balance: ${config.INITIAL_BALANCE}")
        print(f"   Max Trades: {config.MAX_TRADES}")
        print(f"   Leverage: {config.LEVERAGE}x")
        print(f"   Long Position Size: ${config.LONG_POSITION_SIZE}")
        print(f"   Short Position Size: ${config.SHORT_POSITION_SIZE}")
        print(f"   Hedge Trigger: {config.HEDGE_TRIGGER_LOSS*100}%")
        print(f"   Trailing Stop: {config.TRAILING_STOP}")
        print()
        
        # Create bot configuration
        bot_config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,
            max_trades=config.MAX_TRADES,
            leverage=config.LEVERAGE,
            long_position_size=config.LONG_POSITION_SIZE,
            short_position_size=config.SHORT_POSITION_SIZE,
            hedge_trigger_loss=config.HEDGE_TRIGGER_LOSS,
            trailing_stop=config.TRAILING_STOP,
            trailing_stop_positive=config.TRAILING_STOP_POSITIVE,
            trailing_stop_positive_offset=config.TRAILING_STOP_POSITIVE_OFFSET,
            minimal_roi=config.MINIMAL_ROI,
            symbols=['BTC/USDT', 'ETH/USDT']  # Test symbols
        )
        
        print("🔧 Bot Configuration:")
        print(f"   ✅ Configuration loaded successfully")
        print(f"   ✅ ROI table: {len(bot_config.minimal_roi)} time points")
        print(f"   ✅ Trading symbols: {len(bot_config.symbols)} pairs")
        print()
        
        # Test position sizing calculations
        print("💰 Position Sizing Verification:")
        test_price = 50000.0  # Example BTC price
        
        long_usd = bot_config.long_position_size
        long_base = long_usd / test_price
        long_notional = long_base * test_price * bot_config.leverage
        
        hedge_usd = bot_config.short_position_size
        hedge_base = hedge_usd / test_price
        hedge_notional = hedge_base * test_price * bot_config.leverage
        
        print(f"   Long Position:")
        print(f"     USD Amount: ${long_usd}")
        print(f"     Base Amount: {long_base:.8f} BTC")
        print(f"     Notional Value: ${long_notional}")
        print()
        print(f"   Hedge Position:")
        print(f"     USD Amount: ${hedge_usd}")
        print(f"     Base Amount: {hedge_base:.8f} BTC")
        print(f"     Notional Value: ${hedge_notional}")
        print()
        
        # Check if values are reasonable
        if long_notional > config.INITIAL_BALANCE * 2:
            print("   ⚠️  WARNING: Long notional value is very high relative to balance")
        else:
            print("   ✅ Long position size looks reasonable")
            
        if hedge_notional > config.INITIAL_BALANCE * 3:
            print("   ⚠️  WARNING: Hedge notional value is very high relative to balance")
        else:
            print("   ✅ Hedge position size looks reasonable")
        print()
        
        # Test exchange configuration (mock)
        print("🔄 Exchange Configuration Test:")
        print("   The bot will attempt to:")
        print(f"     1. Set margin mode to 'isolated' for each symbol")
        print(f"     2. Set leverage to {bot_config.leverage}x for each symbol")
        print(f"     3. Include marginMode: 'isolated' in order parameters")
        print(f"     4. Use position size = USD_AMOUNT / PRICE")
        print()
        
        # ROI Configuration
        print("📈 ROI Configuration:")
        roi_times = sorted([int(k) for k in bot_config.minimal_roi.keys()])
        print(f"   Time points: {len(roi_times)} (0 to {max(roi_times)} minutes)")
        print(f"   Initial ROI threshold: {bot_config.minimal_roi['0']*100}%")
        print(f"   Final ROI threshold: {bot_config.minimal_roi[str(max(roi_times))]*100}%")
        print()
        
        print("✅ DIAGNOSTICS COMPLETE")
        print()
        print("🎯 Expected Testnet Behavior:")
        print(f"   • Margin Mode: ISOLATED (not cross)")
        print(f"   • Leverage: {bot_config.leverage}x (not 20x)")
        print(f"   • Long trades: ~${long_usd} USD notional")
        print(f"   • Hedge trades: ~${hedge_usd} USD notional")
        print(f"   • Position sizes calculated as: USD / PRICE")
        print()
        print("🚨 If you still see issues:")
        print("   1. Check Binance Testnet futures account settings")
        print("   2. Verify API key has futures trading permissions") 
        print("   3. Check if symbols need manual configuration")
        print("   4. Monitor bot logs for configuration errors")
        
    except ImportError as e:
        print(f"❌ Configuration import error: {e}")
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")

if __name__ == "__main__":
    run_diagnostics()
