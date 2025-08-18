#!/usr/bin/env python3
"""
Multi-Symbol Trading Demo
Demonstrates the new volume-based symbol filtering functionality
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_symbol_filtering():
    """Demo the new symbol filtering functionality"""
    print("🚀 Multi-Symbol Trading Bot Demo")
    print("=" * 60)
    
    # Import after adding to path
    try:
        from trading_bot import TradingBot, BotConfig
        import config
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed")
        return
    
    # Create bot configuration with volume filtering
    bot_config = BotConfig(
        initial_balance=config.INITIAL_BALANCE,
        max_trades=config.MAX_TRADES,
        leverage=config.LEVERAGE,
        timeframe=config.TIMEFRAME,
        symbols=config.TRADING_SYMBOLS,
        max_symbols=getattr(config, 'MAX_SYMBOLS', 100),
        min_24h_volume=getattr(config, 'MIN_24H_VOLUME', 1000000),
        filter_by_volume=getattr(config, 'FILTER_BY_VOLUME', True),
        **config.STRATEGY_PARAMS
    )
    
    print(f"Initial Configuration:")
    print(f"  📊 Max Symbols: {bot_config.max_symbols}")
    print(f"  💰 Min Volume: ${bot_config.min_24h_volume:,.0f}")
    print(f"  🔍 Filter by Volume: {bot_config.filter_by_volume}")
    print(f"  📈 Initial Symbols: {len(bot_config.symbols)}")
    
    # Create bot instance
    bot = TradingBot(bot_config)
    
    print(f"\n🤖 Bot initialized with exchange: {type(bot.exchange).__name__}")
    
    # Test symbol filtering
    print(f"\n📋 Testing symbol filtering...")
    bot.update_symbol_list()
    
    print(f"\n✅ Symbol Update Complete:")
    print(f"  📊 Total Symbols: {len(bot.config.symbols)}")
    print(f"  🔝 Top 10 Symbols: {', '.join(bot.config.symbols[:10])}")
    
    if len(bot.config.symbols) > 10:
        print(f"  ➕ Plus {len(bot.config.symbols) - 10} more...")
    
    # Test volume data fetching
    print(f"\n📈 Testing volume data fetching...")
    if hasattr(bot.exchange, 'fetch_tickers'):
        try:
            tickers = bot.exchange.fetch_tickers()
            print(f"  ✅ Fetched tickers for {len(tickers)} symbols")
            
            # Show top symbols by volume
            volume_data = []
            for symbol in bot.config.symbols[:10]:
                if symbol in tickers:
                    volume_data.append({
                        'symbol': symbol,
                        'volume': tickers[symbol].get('quoteVolume', 0),
                        'price': tickers[symbol].get('last', 0)
                    })
            
            print(f"\n📊 Top Symbols by Volume:")
            print(f"{'Symbol':<12} {'Volume':<15} {'Price':<12}")
            print("-" * 40)
            
            for data in sorted(volume_data, key=lambda x: x['volume'], reverse=True):
                volume_str = f"${data['volume']/1000000:.1f}M"
                price_str = f"${data['price']:.4f}"
                print(f"{data['symbol']:<12} {volume_str:<15} {price_str:<12}")
                
        except Exception as e:
            print(f"  ⚠️ Error fetching volume data: {e}")
    
    # Test analysis on multiple symbols
    print(f"\n🔍 Testing analysis on multiple symbols...")
    signals_found = 0
    symbols_analyzed = 0
    
    for symbol in bot.config.symbols[:5]:  # Test first 5 symbols
        try:
            analysis = bot.analyze_symbol(symbol)
            symbols_analyzed += 1
            
            print(f"  📈 {symbol}:")
            print(f"    Current Price: ${analysis['price']:.4f}")
            print(f"    RSI: {analysis['rsi']:.2f}")
            print(f"    EWO: {analysis['ewo']:.2f}")
            
            if analysis['signal']:
                signals_found += 1
                print(f"    🚨 SIGNAL: {analysis['signal'].upper()}")
            else:
                print(f"    ⚪ No signal")
            
        except Exception as e:
            print(f"  ❌ Error analyzing {symbol}: {e}")
    
    print(f"\n📊 Analysis Summary:")
    print(f"  🔍 Symbols Analyzed: {symbols_analyzed}")
    print(f"  🚨 Signals Found: {signals_found}")
    print(f"  📈 Signal Rate: {(signals_found/symbols_analyzed*100) if symbols_analyzed > 0 else 0:.1f}%")
    
    # Calculate potential opportunities
    potential_daily_signals = (signals_found / symbols_analyzed) * len(bot.config.symbols) * (24 * 60 / 5) if symbols_analyzed > 0 else 0
    
    print(f"\n🎯 Opportunity Projection:")
    print(f"  📊 Total Symbols: {len(bot.config.symbols)}")
    print(f"  🕐 5-min intervals/day: {24 * 60 // 5}")
    print(f"  🚨 Estimated daily signals: {potential_daily_signals:.0f}")
    print(f"  📈 Max trades capacity: {bot_config.max_trades}")
    
    if potential_daily_signals > bot_config.max_trades * 10:
        print(f"  ✅ Excellent signal opportunity (high activity expected)")
    elif potential_daily_signals > bot_config.max_trades * 5:
        print(f"  ✅ Good signal opportunity (moderate activity expected)")
    else:
        print(f"  ⚠️ Limited signal opportunity (conservative activity expected)")
    
    return bot

def demo_trading_simulation():
    """Simulate trading with multiple symbols"""
    print(f"\n" + "=" * 60)
    print("MULTI-SYMBOL TRADING SIMULATION")
    print("=" * 60)
    
    # Simulate trading results with more symbols
    symbols = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
        'XRP/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LINK/USDT'
    ]
    
    initial_balance = 100.0
    max_trades = 5
    
    # Simulate more frequent trading opportunities
    trades = []
    for i in range(20):  # Simulate 20 trades over time
        symbol = np.random.choice(symbols)
        entry_price = 50000 + np.random.randn() * 5000 if 'BTC' in symbol else 3000 + np.random.randn() * 500
        
        # More realistic price movements
        price_change_pct = np.random.normal(0.02, 0.08)  # Average 2% gain with 8% volatility
        exit_price = entry_price * (1 + price_change_pct)
        
        signal_type = np.random.choice(['EWO High', 'EWO Low', 'MA Sell', 'Stop Loss'], p=[0.4, 0.3, 0.25, 0.05])
        
        trades.append({
            'symbol': symbol,
            'entry': entry_price,
            'exit': exit_price,
            'signal': signal_type,
            'change_pct': price_change_pct
        })
    
    print(f"💼 Portfolio: ${initial_balance}")
    print(f"🎯 Max Trades: {max_trades}")
    print(f"📊 Symbols: {len(symbols)}")
    print(f"📈 Simulated Trades: {len(trades)}")
    
    print(f"\n📋 Recent Trades:")
    print("-" * 80)
    print(f"{'Symbol':<12} {'Entry':<10} {'Exit':<10} {'P&L%':<8} {'Signal':<12}")
    print("-" * 80)
    
    total_return = 0
    winning_trades = 0
    
    for trade in trades[-10:]:  # Show last 10 trades
        pnl_pct = trade['change_pct'] * 100 * 10  # 10x leverage
        total_return += pnl_pct
        
        if pnl_pct > 0:
            winning_trades += 1
        
        pnl_str = f"{pnl_pct:+.1f}%"
        entry_str = f"${trade['entry']:.2f}"
        exit_str = f"${trade['exit']:.2f}"
        
        print(f"{trade['symbol']:<12} {entry_str:<10} {exit_str:<10} {pnl_str:<8} {trade['signal']:<12}")
    
    print("-" * 80)
    
    win_rate = (winning_trades / len(trades[-10:])) * 100
    avg_return = total_return / len(trades[-10:])
    
    print(f"📊 Performance Metrics (Last 10 Trades):")
    print(f"  🎯 Win Rate: {win_rate:.1f}%")
    print(f"  📈 Avg Return: {avg_return:+.1f}%")
    print(f"  💰 Total Return: {total_return:+.1f}%")
    
    final_balance = initial_balance * (1 + total_return/100)
    print(f"  💼 Final Balance: ${final_balance:.2f}")

def main():
    """Main demo function"""
    try:
        # Test symbol filtering and analysis
        bot = demo_symbol_filtering()
        
        # Run trading simulation
        demo_trading_simulation()
        
        print(f"\n" + "=" * 60)
        print("🚀 MULTI-SYMBOL DEMO COMPLETE")
        print("=" * 60)
        print("Key Benefits of Multi-Symbol Trading:")
        print("✅ Increased trading opportunities")
        print("✅ Better risk diversification")
        print("✅ Dynamic symbol selection by volume")
        print("✅ Automated filtering and rotation")
        print()
        print("To run the full bot:")
        print("📱 python3 main.py")
        print("🌐 Open http://localhost:5000")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
