#!/usr/bin/env python3
"""
Test script to verify that moving averages are calculated correctly
and not showing as straight lines.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingStrategy, TradingBot, BotConfig
from config import STRATEGY_PARAMS, BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET
import pandas as pd
import numpy as np

def test_indicators():
    """Test indicator calculation with real and mock data"""
    print("🧪 Testing Indicator Calculations...")
    
    # Create config
    config = BotConfig(
        base_nb_candles_buy=STRATEGY_PARAMS['base_nb_candles_buy'],
        base_nb_candles_sell=STRATEGY_PARAMS['base_nb_candles_sell'],
        low_offset=STRATEGY_PARAMS['low_offset'],
        high_offset=STRATEGY_PARAMS['high_offset'],
        ewo_low=STRATEGY_PARAMS['ewo_low'],
        ewo_high=STRATEGY_PARAMS['ewo_high'],
        rsi_buy=STRATEGY_PARAMS['rsi_buy'],
        fast_ewo=STRATEGY_PARAMS['fast_ewo'],
        slow_ewo=STRATEGY_PARAMS['slow_ewo'],
        stoploss=STRATEGY_PARAMS['stoploss']
    )
    
    strategy = TradingStrategy(config)
    
    # Test with realistic mock data (not straight line)
    print("   Creating realistic test data...")
    dates = pd.date_range('2024-01-01', periods=200, freq='5T')
    
    # Create realistic price movement (random walk with trend)
    base_price = 50000
    price_changes = np.random.randn(200) * 0.001  # 0.1% random changes
    price_changes[0] = 0
    cumulative_changes = np.cumsum(price_changes)
    prices = base_price * (1 + cumulative_changes)
    
    # Add some trend and volatility
    trend = np.linspace(0, 0.05, 200)  # 5% upward trend over period
    prices = prices * (1 + trend)
    
    # Create OHLC data with realistic spread
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'close': prices * (1 + np.random.randn(200) * 0.0005),  # Small random close
        'volume': np.random.uniform(100, 1000, 200)
    })
    
    # Calculate high/low from open/close
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.randn(200) * 0.0002))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.randn(200) * 0.0002))
    
    df.set_index('timestamp', inplace=True)
    
    print(f"   Test data shape: {df.shape}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"   Price variation: {((df['close'].max() - df['close'].min()) / df['close'].mean() * 100):.2f}%")
    
    # Populate indicators
    print("   Calculating indicators...")
    df_with_indicators = strategy.populate_indicators(df.copy())
    
    # Check what columns were created
    ma_buy_col = f'ma_buy_{config.base_nb_candles_buy}'
    ma_sell_col = f'ma_sell_{config.base_nb_candles_sell}'
    
    print(f"   Expected MA Buy column: {ma_buy_col}")
    print(f"   Expected MA Sell column: {ma_sell_col}")
    print(f"   Available columns: {list(df_with_indicators.columns)}")
    
    # Verify moving averages
    if ma_buy_col in df_with_indicators.columns:
        ma_buy = df_with_indicators[ma_buy_col]
        print(f"   ✅ MA Buy ({config.base_nb_candles_buy}) calculated")
        print(f"      Range: ${ma_buy.min():.2f} - ${ma_buy.max():.2f}")
        print(f"      Variation: {((ma_buy.max() - ma_buy.min()) / ma_buy.mean() * 100):.2f}%")
        
        # Check if it's a straight line (variation < 0.1%)
        variation = (ma_buy.max() - ma_buy.min()) / ma_buy.mean() * 100
        if variation < 0.1:
            print(f"      ❌ WARNING: MA Buy appears to be a straight line (variation: {variation:.4f}%)")
        else:
            print(f"      ✅ MA Buy shows proper variation")
    else:
        print(f"   ❌ MA Buy column missing!")
    
    if ma_sell_col in df_with_indicators.columns:
        ma_sell = df_with_indicators[ma_sell_col]
        print(f"   ✅ MA Sell ({config.base_nb_candles_sell}) calculated")
        print(f"      Range: ${ma_sell.min():.2f} - ${ma_sell.max():.2f}")
        print(f"      Variation: {((ma_sell.max() - ma_sell.min()) / ma_sell.mean() * 100):.2f}%")
        
        # Check if it's a straight line
        variation = (ma_sell.max() - ma_sell.min()) / ma_sell.mean() * 100
        if variation < 0.1:
            print(f"      ❌ WARNING: MA Sell appears to be a straight line (variation: {variation:.4f}%)")
        else:
            print(f"      ✅ MA Sell shows proper variation")
    else:
        print(f"   ❌ MA Sell column missing!")
    
    # Check other indicators
    if 'rsi' in df_with_indicators.columns:
        rsi = df_with_indicators['rsi']
        print(f"   ✅ RSI calculated")
        print(f"      Range: {rsi.min():.2f} - {rsi.max():.2f}")
    
    if 'EWO' in df_with_indicators.columns:
        ewo = df_with_indicators['EWO']
        print(f"   ✅ EWO calculated")
        print(f"      Range: {ewo.min():.2f} - {ewo.max():.2f}")
    
    # Test signals
    print("   Testing signal generation...")
    df_with_signals = strategy.populate_entry_signals(df_with_indicators.copy())
    df_final = strategy.populate_exit_signals(df_with_signals.copy())
    
    if 'enter_long' in df_final.columns:
        entry_signals = df_final['enter_long'].sum()
        print(f"   ✅ Entry signals: {entry_signals}")
    
    if 'exit_long' in df_final.columns:
        exit_signals = df_final['exit_long'].sum()
        print(f"   ✅ Exit signals: {exit_signals}")
    
    return df_final

def test_with_real_data():
    """Test with real data from exchange"""
    print("\n🌐 Testing with Real Exchange Data...")
    
    try:
        # Create bot config
        config = BotConfig(
            base_nb_candles_buy=STRATEGY_PARAMS['base_nb_candles_buy'],
            base_nb_candles_sell=STRATEGY_PARAMS['base_nb_candles_sell'],
            low_offset=STRATEGY_PARAMS['low_offset'],
            high_offset=STRATEGY_PARAMS['high_offset'],
            ewo_low=STRATEGY_PARAMS['ewo_low'],
            ewo_high=STRATEGY_PARAMS['ewo_high'],
            rsi_buy=STRATEGY_PARAMS['rsi_buy'],
            fast_ewo=STRATEGY_PARAMS['fast_ewo'],
            slow_ewo=STRATEGY_PARAMS['slow_ewo'],
            stoploss=STRATEGY_PARAMS['stoploss']
        )
        
        # Create bot instance
        bot = TradingBot(config)
        
        # Test data fetch
        print("   Fetching BTC/USDT data...")
        df = bot.get_historical_data('BTC/USDT', limit=100)
        
        if df.empty:
            print("   ❌ No data received from exchange")
            return None
        
        print(f"   ✅ Received {len(df)} candles")
        print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
        
        # Test analysis
        print("   Running full analysis...")
        analysis = bot.analyze_symbol('BTC/USDT')
        
        if analysis and 'dataframe' in analysis:
            df_analyzed = analysis['dataframe']
            
            ma_buy_col = f'ma_buy_{config.base_nb_candles_buy}'
            ma_sell_col = f'ma_sell_{config.base_nb_candles_sell}'
            
            if ma_buy_col in df_analyzed.columns:
                ma_buy = df_analyzed[ma_buy_col]
                variation = (ma_buy.max() - ma_buy.min()) / ma_buy.mean() * 100
                print(f"   ✅ Real MA Buy variation: {variation:.2f}%")
                
                if variation < 0.1:
                    print(f"   ❌ WARNING: Real MA Buy appears to be a straight line!")
                else:
                    print(f"   ✅ Real MA Buy shows proper variation")
            
            if ma_sell_col in df_analyzed.columns:
                ma_sell = df_analyzed[ma_sell_col]
                variation = (ma_sell.max() - ma_sell.min()) / ma_sell.mean() * 100
                print(f"   ✅ Real MA Sell variation: {variation:.2f}%")
                
                if variation < 0.1:
                    print(f"   ❌ WARNING: Real MA Sell appears to be a straight line!")
                else:
                    print(f"   ✅ Real MA Sell shows proper variation")
            
            print(f"   Current Analysis:")
            print(f"      Signal: {analysis.get('signal', 'None')}")
            print(f"      Price: ${analysis.get('price', 0):.2f}")
            print(f"      RSI: {analysis.get('rsi', 0):.2f}")
            print(f"      EWO: {analysis.get('ewo', 0):.2f}")
            
            return df_analyzed
    
    except Exception as e:
        print(f"   ❌ Error testing with real data: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Trading Bot Indicator Test")
    print("=" * 60)
    
    # Test with mock data
    df_mock = test_indicators()
    
    # Test with real data
    df_real = test_with_real_data()
    
    print("\n📊 Test Summary:")
    print("=" * 60)
    
    if df_mock is not None:
        print("✅ Mock data test completed")
    else:
        print("❌ Mock data test failed")
    
    if df_real is not None:
        print("✅ Real data test completed")
    else:
        print("❌ Real data test failed")
    
    print("\n💡 If moving averages appear as straight lines:")
    print("   1. Check if sufficient data points are available")
    print("   2. Verify price data has actual variation")
    print("   3. Check TA-Lib installation")
    print("   4. Ensure proper timeframe is being used")
