#!/usr/bin/env python3
"""
Test script to debug candlestick chart display issues
and verify data structure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingBot, BotConfig
from config import STRATEGY_PARAMS, BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET
from web_interface import create_candlestick_chart
import pandas as pd
import numpy as np

def test_candlestick_data():
    """Test candlestick chart data and creation"""
    print("🧪 Testing Candlestick Chart Data...")
    
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
    
    # Test data fetch and analysis
    print("   Fetching and analyzing BTC/USDT...")
    analysis = bot.analyze_symbol('BTC/USDT')
    
    if not analysis or 'dataframe' not in analysis:
        print("   ❌ No analysis data received")
        return False
    
    df = analysis['dataframe']
    print(f"   ✅ Data shape: {df.shape}")
    print(f"   Available columns: {list(df.columns)}")
    
    # Check OHLCV data integrity
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"   ❌ Missing OHLCV columns: {missing_cols}")
        return False
    
    print("   ✅ All OHLCV columns present")
    
    # Check data quality
    print(f"   Price data:")
    print(f"      Open: ${df['open'].iloc[-1]:.2f}")
    print(f"      High: ${df['high'].iloc[-1]:.2f}")
    print(f"      Low: ${df['low'].iloc[-1]:.2f}")
    print(f"      Close: ${df['close'].iloc[-1]:.2f}")
    print(f"      Volume: {df['volume'].iloc[-1]:.0f}")
    
    # Check for data validity
    if (df['high'] < df['low']).any():
        print("   ❌ Invalid data: High < Low detected")
        return False
    
    if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
        print("   ❌ Invalid data: High < Open/Close detected")
        return False
    
    if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
        print("   ❌ Invalid data: Low > Open/Close detected")
        return False
    
    print("   ✅ OHLC data validation passed")
    
    # Check signals
    if 'enter_long' in df.columns:
        buy_signals = df['enter_long'].sum()
        print(f"   Buy signals: {buy_signals}")
    
    if 'exit_long' in df.columns:
        sell_signals = df['exit_long'].sum()
        print(f"   Sell signals: {sell_signals}")
    
    # Test chart creation
    print("   Testing chart creation...")
    try:
        # Mock the bot config for chart creation
        class MockBot:
            def __init__(self, config):
                self.config = config
        
        mock_bot = MockBot(config)
        
        # Create the chart
        chart_data = create_candlestick_chart(analysis)
        
        if chart_data:
            print("   ✅ Chart created successfully")
            
            # Check chart data structure
            chart_json = chart_data.to_json()
            if 'data' in chart_json:
                traces = len(chart_data.data)
                print(f"   Chart has {traces} traces")
                
                # Look for candlestick trace
                candlestick_found = False
                for i, trace in enumerate(chart_data.data):
                    if hasattr(trace, 'type') and trace.type == 'candlestick':
                        candlestick_found = True
                        print(f"   ✅ Candlestick trace found at index {i}")
                        
                        # Check candlestick data
                        if hasattr(trace, 'x') and len(trace.x) > 0:
                            print(f"      Data points: {len(trace.x)}")
                        if hasattr(trace, 'open') and len(trace.open) > 0:
                            print(f"      Open range: ${min(trace.open):.2f} - ${max(trace.open):.2f}")
                        if hasattr(trace, 'close') and len(trace.close) > 0:
                            print(f"      Close range: ${min(trace.close):.2f} - ${max(trace.close):.2f}")
                        break
                
                if not candlestick_found:
                    print("   ❌ No candlestick trace found in chart")
                    return False
            
            return True
        else:
            print("   ❌ Chart creation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error creating chart: {e}")
        return False

def test_mock_data():
    """Test with controlled mock data to isolate issues"""
    print("\n🧪 Testing with Controlled Mock Data...")
    
    # Create simple, known good data
    dates = pd.date_range('2024-01-01', periods=50, freq='5min')
    
    # Create realistic OHLC data
    base_price = 50000
    price_changes = np.random.randn(50) * 0.001
    price_changes[0] = 0
    cumulative_changes = np.cumsum(price_changes)
    close_prices = base_price * (1 + cumulative_changes)
    
    df = pd.DataFrame({
        'open': close_prices,
        'close': close_prices * (1 + np.random.randn(50) * 0.0005),
        'volume': np.random.uniform(100, 1000, 50),
    }, index=dates)
    
    # Ensure proper high/low
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.randn(50) * 0.0002))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.randn(50) * 0.0002))
    
    # Add some fake signals
    df['enter_long'] = 0
    df['exit_long'] = 0
    df.iloc[10, df.columns.get_loc('enter_long')] = 1
    df.iloc[30, df.columns.get_loc('exit_long')] = 1
    
    print(f"   Mock data shape: {df.shape}")
    print(f"   Mock data columns: {list(df.columns)}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Create mock analysis
    mock_analysis = {
        'symbol': 'TEST/USDT',
        'signal': 'buy',
        'price': df['close'].iloc[-1],
        'dataframe': df,
        'rsi': 50,
        'ewo': 5
    }
    
    print("   Testing chart with mock data...")
    try:
        chart = create_candlestick_chart(mock_analysis)
        if chart:
            print("   ✅ Mock chart created successfully")
            return True
        else:
            print("   ❌ Mock chart creation failed")
            return False
    except Exception as e:
        print(f"   ❌ Error creating mock chart: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Candlestick Chart Debug Test")
    print("=" * 60)
    
    # Test with real data
    real_test = test_candlestick_data()
    
    # Test with mock data
    mock_test = test_mock_data()
    
    print("\n📊 Test Summary:")
    print("=" * 60)
    
    if real_test:
        print("✅ Real data test passed")
    else:
        print("❌ Real data test failed")
    
    if mock_test:
        print("✅ Mock data test passed")
    else:
        print("❌ Mock data test failed")
    
    if real_test and mock_test:
        print("\n🎉 All tests passed! Charts should display correctly.")
    else:
        print("\n🔍 Issues detected. Check data structure and chart creation logic.")
