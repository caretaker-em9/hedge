#!/usr/bin/env python3
"""
Demo Script - Run the trading bot in demonstration mode
This script shows how the bot works without requiring real API keys
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from trading_bot import TradingBot, BotConfig, EWO
    import talib.abstract as ta
    print("✅ All dependencies loaded successfully")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

def generate_demo_data(symbol="BTC/USDT", days=30):
    """Generate realistic demo trading data"""
    print(f"Generating demo data for {symbol}...")
    
    # Generate timestamps for 5-minute intervals
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    periods = int((end_time - start_time).total_seconds() / 300)  # 5-minute intervals
    timestamps = pd.date_range(start=start_time, end=end_time, periods=periods)
    
    # Generate realistic price data using random walk
    initial_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 300
    
    # Create price series with trend and volatility
    returns = np.random.normal(0.0001, 0.02, len(timestamps))  # Small upward bias
    
    # Add some trend components
    trend = np.sin(np.arange(len(timestamps)) * 2 * np.pi / (24 * 12)) * 0.001  # Daily cycle
    weekly_trend = np.sin(np.arange(len(timestamps)) * 2 * np.pi / (24 * 12 * 7)) * 0.002  # Weekly cycle
    
    returns += trend + weekly_trend
    
    # Generate OHLCV data
    close_prices = initial_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    data = []
    for i, (timestamp, close) in enumerate(zip(timestamps, close_prices)):
        if i == 0:
            open_price = close
        else:
            open_price = close_prices[i-1]
        
        # Random high/low around open/close
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
        volume = abs(np.random.normal(1000, 500))
        
        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def analyze_demo_data():
    """Analyze demo data with the trading strategy"""
    print("\n" + "="*60)
    print("TRADING STRATEGY DEMO ANALYSIS")
    print("="*60)
    
    config = BotConfig()
    strategy = config  # Use config as strategy params
    
    # Generate demo data for multiple symbols
    symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    
    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}...")
        
        # Generate data
        df = generate_demo_data(symbol)
        
        # Calculate indicators (simplified version)
        df['ma_buy_17'] = ta.EMA(df, timeperiod=17)
        df['ma_sell_49'] = ta.EMA(df, timeperiod=49)
        df['EWO'] = EWO(df, 50, 200)
        df['rsi'] = ta.RSI(df, timeperiod=14)
        
        # Generate signals
        price_above_threshold = df['close'] > 0.5
        
        # Buy conditions
        buy_condition_1 = (
            (price_above_threshold) &
            (df['close'] < (df['ma_buy_17'] * 0.978)) &
            (df['EWO'] > 3.34) &
            (df['rsi'] < 65) &
            (df['volume'] > 0)
        )
        
        buy_condition_2 = (
            (price_above_threshold) &
            (df['close'] < (df['ma_buy_17'] * 0.978)) &
            (df['EWO'] < -17.457) &
            (df['volume'] > 0)
        )
        
        df['buy_signal'] = (buy_condition_1 | buy_condition_2).astype(int)
        
        # Sell condition
        sell_condition = (
            (df['close'] > (df['ma_sell_49'] * 1.019)) &
            (df['volume'] > 0)
        )
        
        df['sell_signal'] = sell_condition.astype(int)
        
        # Count signals
        total_buy_signals = df['buy_signal'].sum()
        total_sell_signals = df['sell_signal'].sum()
        
        # Latest values
        latest = df.iloc[-1]
        
        print(f"   Current Price: ${latest['close']:.2f}")
        print(f"   RSI: {latest['rsi']:.2f}")
        print(f"   EWO: {latest['EWO']:.2f}")
        print(f"   MA Buy (17): ${latest['ma_buy_17']:.2f}")
        print(f"   MA Sell (49): ${latest['ma_sell_49']:.2f}")
        print(f"   Buy Signals (30 days): {total_buy_signals}")
        print(f"   Sell Signals (30 days): {total_sell_signals}")
        
        # Check current signal
        if latest['buy_signal'] == 1:
            print(f"   🟢 BUY SIGNAL ACTIVE")
        elif latest['sell_signal'] == 1:
            print(f"   🔴 SELL SIGNAL ACTIVE")
        else:
            print(f"   ⚪ No signal")

def simulate_trading():
    """Simulate trading with the strategy"""
    print("\n" + "="*60)
    print("TRADING SIMULATION")
    print("="*60)
    
    initial_balance = 100.0
    balance = initial_balance
    max_trades = 5
    leverage = 10.0
    stop_loss = -0.189
    
    print(f"Initial Balance: ${initial_balance}")
    print(f"Max Trades: {max_trades}")
    print(f"Leverage: {leverage}x")
    print(f"Stop Loss: {stop_loss*100:.1f}%")
    
    # Simulate some trades
    trades = [
        {"symbol": "BTC/USDT", "entry": 52000, "exit": 53500, "signal": "EWO High"},
        {"symbol": "ETH/USDT", "entry": 3200, "exit": 3100, "signal": "EWO Low"},
        {"symbol": "BNB/USDT", "entry": 320, "exit": 335, "signal": "EWO High"},
        {"symbol": "BTC/USDT", "entry": 51800, "exit": 50200, "signal": "Stop Loss"},
        {"symbol": "ETH/USDT", "entry": 3150, "exit": 3280, "signal": "MA Sell"},
    ]
    
    print(f"\n📈 Trade History:")
    print("-" * 80)
    print(f"{'Symbol':<12} {'Entry':<8} {'Exit':<8} {'P&L':<8} {'P&L%':<8} {'Signal':<12}")
    print("-" * 80)
    
    total_pnl = 0
    position_size = (balance * 0.02) * leverage  # 2% risk per trade with leverage
    
    for trade in trades:
        price_change = (trade["exit"] - trade["entry"]) / trade["entry"]
        pnl = position_size * price_change
        pnl_pct = price_change * 100 * leverage
        
        total_pnl += pnl
        
        pnl_str = f"${pnl:.2f}"
        pnl_pct_str = f"{pnl_pct:.1f}%"
        
        if pnl > 0:
            pnl_str = f"+{pnl_str}"
            pnl_pct_str = f"+{pnl_pct_str}"
        
        print(f"{trade['symbol']:<12} ${trade['entry']:<7.0f} ${trade['exit']:<7.0f} {pnl_str:<8} {pnl_pct_str:<8} {trade['signal']:<12}")
    
    print("-" * 80)
    final_balance = balance + total_pnl
    total_return = (total_pnl / initial_balance) * 100
    
    print(f"Total P&L: ${total_pnl:.2f}")
    print(f"Final Balance: ${final_balance:.2f}")
    print(f"Total Return: {total_return:.1f}%")

def main():
    """Main demo function"""
    print("🤖 Trading Bot Demo")
    print("=" * 60)
    print("This demo shows how the converted Freqtrade strategy works")
    print("without requiring real API keys or live market data.")
    print("")
    
    try:
        # Run analysis
        analyze_demo_data()
        
        # Run trading simulation
        simulate_trading()
        
        print("\n" + "="*60)
        print("DEMO COMPLETE")
        print("="*60)
        print("To run the full bot with web interface:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Configure API keys in config.py")
        print("3. Run: python main.py")
        print("4. Open browser to http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
