#!/usr/bin/env python3
"""
Test script to verify that DataFrame operations are optimized
and no performance warnings are generated.
"""

import warnings
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingStrategy, TradingBot
import pandas as pd
import numpy as np

def test_strategy_performance():
    """Test the trading strategy for performance warnings"""
    print("🧪 Testing Trading Strategy Performance...")
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Create demo data
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(45000, 55000, 100),
            'high': np.random.uniform(45000, 55000, 100),
            'low': np.random.uniform(45000, 55000, 100),
            'close': np.random.uniform(45000, 55000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        })
        
        # Fix high/low values
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        # Test strategy
        from config import STRATEGY_PARAMS
        
        class Config:
            def __init__(self, params):
                for key, value in params.items():
                    setattr(self, key, value)
        
        config = Config(STRATEGY_PARAMS)
        strategy = TradingStrategy(config)
        
        print("   Testing populate_indicators...")
        df_with_indicators = strategy.populate_indicators(df.copy())
        
        print("   Testing populate_entry_signals...")
        df_with_entry = strategy.populate_entry_signals(df_with_indicators.copy())
        
        print("   Testing populate_exit_signals...")
        df_final = strategy.populate_exit_signals(df_with_entry.copy())
        
        # Check for performance warnings
        performance_warnings = [warning for warning in w 
                              if "PerformanceWarning" in str(warning.category)]
        
        if performance_warnings:
            print("❌ Performance warnings detected:")
            for warning in performance_warnings:
                print(f"   {warning.message}")
            return False
        else:
            print("✅ No performance warnings detected!")
            
        # Verify that all expected columns are present
        expected_columns = [
            'rsi', 'EWO', 'ma_buy_17', 'ma_sell_49', 'enter_long', 'exit_long'
        ]
        
        missing_columns = [col for col in expected_columns if col not in df_final.columns]
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All expected columns present!")
            
        return True

def test_multi_symbol_analysis():
    """Test multi-symbol analysis for performance"""
    print("\n🧪 Testing Multi-Symbol Analysis Performance...")
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Mock bot for testing
        from config import STRATEGY_PARAMS
        
        class Config:
            def __init__(self, params):
                for key, value in params.items():
                    setattr(self, key, value)
        
        class MockBot:
            def __init__(self):
                config = Config(STRATEGY_PARAMS)
                self.strategy = TradingStrategy(config)
                
            def get_historical_data(self, symbol):
                """Generate mock data"""
                dates = pd.date_range('2024-01-01', periods=50, freq='1H')
                df = pd.DataFrame({
                    'timestamp': dates,
                    'open': np.random.uniform(45000, 55000, 50),
                    'high': np.random.uniform(45000, 55000, 50),
                    'low': np.random.uniform(45000, 55000, 50),
                    'close': np.random.uniform(45000, 55000, 50),
                    'volume': np.random.uniform(100, 1000, 50)
                })
                df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
                df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
                return df
                
            def analyze_symbol(self, symbol):
                """Analyze a symbol"""
                df = self.get_historical_data(symbol)
                if df.empty:
                    return {'symbol': symbol, 'signal': None, 'price': None}
                
                # Populate indicators and signals
                df = self.strategy.populate_indicators(df)
                df = self.strategy.populate_entry_signals(df)
                df = self.strategy.populate_exit_signals(df)
                
                # Create a defragmented copy for better performance if needed
                df = df.copy()
                
                # Get latest signals
                latest = df.iloc[-1]
                current_price = latest['close']
                
                signal = None
                if latest['enter_long'] == 1:
                    signal = 'buy'
                elif latest['exit_long'] == 1:
                    signal = 'sell'
                
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'price': current_price,
                    'dataframe': df,
                    'rsi': latest['rsi'],
                    'ewo': latest['EWO']
                }
        
        bot = MockBot()
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        for symbol in test_symbols:
            print(f"   Analyzing {symbol}...")
            result = bot.analyze_symbol(symbol)
            
        # Check for performance warnings
        performance_warnings = [warning for warning in w 
                              if "PerformanceWarning" in str(warning.category)]
        
        if performance_warnings:
            print("❌ Performance warnings in multi-symbol analysis:")
            for warning in performance_warnings:
                print(f"   {warning.message}")
            return False
        else:
            print("✅ Multi-symbol analysis completed without performance warnings!")
            return True

if __name__ == "__main__":
    print("🚀 Trading Bot Performance Test")
    print("=" * 60)
    
    strategy_ok = test_strategy_performance()
    multi_symbol_ok = test_multi_symbol_analysis()
    
    print("\n📊 Test Results:")
    print("=" * 60)
    
    if strategy_ok and multi_symbol_ok:
        print("✅ ALL TESTS PASSED - No performance warnings detected!")
        print("✅ DataFrame operations are optimized!")
        sys.exit(0)
    else:
        print("❌ Some tests failed - performance issues detected")
        sys.exit(1)
