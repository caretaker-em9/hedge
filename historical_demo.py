#!/usr/bin/env python3
"""
Historical Data Demo for Hedging Strategy
Uses real historical data from Binance testnet to demonstrate the hedging strategy
"""

import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading_bot import TradingBot, BotConfig, HedgePair, Trade
import ccxt

class HistoricalDataDemo:
    """Demo using historical market data"""
    
    def __init__(self):
        # Load updated configuration
        import config
        self.config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,
            max_trades=config.MAX_TRADES,
            leverage=config.LEVERAGE,
            timeframe=config.TIMEFRAME,
            initial_trade_size=config.INITIAL_TRADE_SIZE,
            long_position_size=config.LONG_POSITION_SIZE,
            short_position_size=config.SHORT_POSITION_SIZE,
            hedge_trigger_loss=config.HEDGE_TRIGGER_LOSS,
            one_trade_per_pair=config.ONE_TRADE_PER_PAIR,
            exit_when_hedged=config.EXIT_WHEN_HEDGED,
            min_hedge_profit_ratio=config.MIN_HEDGE_PROFIT_RATIO,
            **config.STRATEGY_PARAMS
        )
        
        # Initialize exchange for data fetching
        try:
            self.exchange = ccxt.binance({
                'apiKey': config.BINANCE_TESTNET_API_KEY,
                'secret': config.BINANCE_TESTNET_SECRET,
                'sandbox': True,
                'enableRateLimit': True,
            })
        except Exception as e:
            print(f"⚠️  Exchange connection failed: {e}")
            self.exchange = None
    
    def fetch_historical_data(self, symbol='ETH/USDT', timeframe='5m', limit=500):
        """Fetch historical OHLCV data"""
        try:
            if not self.exchange:
                # Return mock data if exchange unavailable
                return self.generate_mock_data(limit)
            
            print(f"📊 Fetching {limit} candles of {timeframe} data for {symbol}...")
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            print(f"✅ Successfully fetched {len(df)} candles")
            print(f"📅 Date range: {df.index[0]} to {df.index[-1]}")
            print(f"💰 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return self.generate_mock_data(limit)
    
    def generate_mock_data(self, limit=500):
        """Generate realistic mock price data with volatility"""
        print("📈 Generating mock historical data...")
        
        # Start from a recent time
        start_time = datetime.now() - timedelta(hours=limit * 5 / 60)  # 5min intervals
        timestamps = [start_time + timedelta(minutes=5*i) for i in range(limit)]
        
        # Generate realistic price movement
        base_price = 2000.0  # Starting price
        prices = [base_price]
        
        for i in range(1, limit):
            # Random walk with some trend and volatility
            change_pct = np.random.normal(0, 0.002)  # 0.2% average volatility
            # Add some trend reversals
            if i % 50 == 0:
                change_pct += np.random.choice([-0.02, 0.02])  # Occasional 2% moves
            
            new_price = prices[-1] * (1 + change_pct)
            prices.append(max(new_price, 100))  # Don't let price go below $100
        
        # Create OHLCV data
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
            # Create realistic OHLC from close price
            volatility = close * 0.001  # 0.1% intrabar volatility
            high = close + np.random.uniform(0, volatility)
            low = close - np.random.uniform(0, volatility)
            open_price = close + np.random.uniform(-volatility/2, volatility/2)
            volume = np.random.uniform(1000, 10000)
            
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
        
        print(f"✅ Generated {len(df)} mock candles")
        return df
    
    def run_backtest(self, symbol='ETH/USDT', show_details=True):
        """Run hedging strategy backtest on historical data"""
        print("🚀 Historical Data Hedging Strategy Demo")
        print("=" * 60)
        
        print(f"⚙️  Configuration:")
        print(f"   💰 Initial Balance: ${self.config.initial_balance}")
        print(f"   📊 Max Trades: {self.config.max_trades}")
        print(f"   📈 Long Position: ${self.config.long_position_size}")
        print(f"   📉 Short Position: ${self.config.short_position_size}")
        print(f"   ⚠️  Hedge Trigger: {self.config.hedge_trigger_loss:.1%}")
        print()
        
        # Fetch historical data
        df = self.fetch_historical_data(symbol)
        
        # Initialize bot with mock exchange
        bot = TradingBot(self.config)
        bot.exchange = MockExchange()
        
        # Variables for tracking
        balance_history = []
        trade_signals = []
        hedge_events = []
        current_hedge_pair = None
        
        print(f"🔄 Running backtest on {len(df)} candles...")
        print()
        
        # Process each candle
        for i, (timestamp, row) in enumerate(df.iterrows()):
            current_price = row['close']
            
            # Update mock exchange price
            bot.exchange.current_prices[symbol] = current_price
            
            # Check existing hedge pair
            if current_hedge_pair and current_hedge_pair.status != 'closed':
                # Update hedge monitoring
                if current_hedge_pair.status == 'long_only' and current_hedge_pair.long_trade:
                    # Check for hedge trigger
                    pnl_pct = (current_price - current_hedge_pair.long_trade.price) / current_hedge_pair.long_trade.price
                    if pnl_pct <= self.config.hedge_trigger_loss:
                        # Trigger hedge
                        short_trade = Trade(
                            id=f"hedge_{int(time.time())}",
                            symbol=symbol,
                            side='sell',
                            amount=self.config.short_position_size * self.config.leverage,
                            price=current_price,
                            timestamp=timestamp,
                            status='open',
                            entry_signal=f"Hedge trigger at {pnl_pct:.1%}",
                            trade_type='hedge',
                            pair_id=current_hedge_pair.pair_id
                        )
                        
                        current_hedge_pair.short_trade = short_trade
                        current_hedge_pair.status = 'hedged'
                        bot.trades.append(short_trade)
                        
                        hedge_events.append({
                            'timestamp': timestamp,
                            'type': 'hedge_triggered',
                            'price': current_price,
                            'long_pnl_pct': pnl_pct,
                            'pair_id': current_hedge_pair.pair_id
                        })
                        
                        if show_details:
                            print(f"🛡️  {timestamp.strftime('%H:%M')} - Hedge triggered at ${current_price:.2f} ({pnl_pct:.1%} loss)")
                
                elif current_hedge_pair.status == 'hedged':
                    # Check for exit conditions
                    long_pnl = (current_price - current_hedge_pair.long_trade.price) * current_hedge_pair.long_trade.amount
                    short_pnl = (current_hedge_pair.short_trade.price - current_price) * current_hedge_pair.short_trade.amount
                    
                    if long_pnl < 0 and short_pnl > 0:
                        hedge_coverage = short_pnl / abs(long_pnl)
                        if hedge_coverage >= self.config.min_hedge_profit_ratio:
                            # Close both positions
                            current_hedge_pair.long_trade.status = 'closed'
                            current_hedge_pair.long_trade.exit_price = current_price
                            current_hedge_pair.long_trade.exit_timestamp = timestamp
                            current_hedge_pair.long_trade.pnl = long_pnl
                            
                            current_hedge_pair.short_trade.status = 'closed'
                            current_hedge_pair.short_trade.exit_price = current_price
                            current_hedge_pair.short_trade.exit_timestamp = timestamp
                            current_hedge_pair.short_trade.pnl = short_pnl
                            
                            current_hedge_pair.status = 'closed'
                            
                            total_pnl = long_pnl + short_pnl
                            bot.balance += total_pnl / self.config.leverage  # Adjust for leverage
                            
                            hedge_events.append({
                                'timestamp': timestamp,
                                'type': 'hedge_closed',
                                'price': current_price,
                                'total_pnl': total_pnl,
                                'coverage': hedge_coverage,
                                'pair_id': current_hedge_pair.pair_id
                            })
                            
                            if show_details:
                                print(f"✅ {timestamp.strftime('%H:%M')} - Hedge closed at ${current_price:.2f} (Coverage: {hedge_coverage:.2f}x, P&L: ${total_pnl/self.config.leverage:.2f})")
                            
                            current_hedge_pair = None
            
            # Generate signals every 10 candles (simulate strategy analysis)
            if i % 10 == 0 and current_hedge_pair is None:
                # Simple signal generation based on price movement
                if i > 20:  # Need some history
                    price_change = (current_price - df.iloc[i-10]['close']) / df.iloc[i-10]['close']
                    rsi_sim = 50 + (price_change * 1000) % 50  # Simulate RSI
                    
                    # Generate buy signal occasionally
                    if price_change < -0.02 and rsi_sim < 40:  # Oversold condition
                        # Create new hedge pair
                        pair_id = f"{symbol}_{int(timestamp.timestamp())}"
                        
                        long_trade = Trade(
                            id=f"long_{int(time.time())}",
                            symbol=symbol,
                            side='buy',
                            amount=self.config.long_position_size * self.config.leverage,
                            price=current_price,
                            timestamp=timestamp,
                            status='open',
                            entry_signal=f"Buy signal (RSI: {rsi_sim:.1f})",
                            trade_type='long',
                            pair_id=pair_id
                        )
                        
                        current_hedge_pair = HedgePair(
                            pair_id=pair_id,
                            symbol=symbol,
                            long_trade=long_trade,
                            total_allocation=self.config.initial_trade_size,
                            long_size=self.config.long_position_size,
                            short_size=self.config.short_position_size,
                            hedge_trigger=self.config.hedge_trigger_loss,
                            created_timestamp=timestamp
                        )
                        
                        bot.trades.append(long_trade)
                        bot.hedge_pairs.append(current_hedge_pair)
                        
                        trade_signals.append({
                            'timestamp': timestamp,
                            'type': 'buy_signal',
                            'price': current_price,
                            'rsi': rsi_sim,
                            'pair_id': pair_id
                        })
                        
                        if show_details:
                            print(f"📈 {timestamp.strftime('%H:%M')} - Long opened at ${current_price:.2f} (RSI: {rsi_sim:.1f})")
            
            # Track balance
            balance_history.append({
                'timestamp': timestamp,
                'balance': bot.balance,
                'price': current_price
            })
        
        # Generate summary
        self.print_backtest_summary(bot, balance_history, hedge_events, df)
        
        return bot, balance_history, hedge_events
    
    def print_backtest_summary(self, bot, balance_history, hedge_events, price_data):
        """Print detailed backtest summary"""
        print("\n" + "="*60)
        print("📊 BACKTEST SUMMARY")
        print("="*60)
        
        initial_balance = self.config.initial_balance
        final_balance = bot.balance
        total_return = (final_balance - initial_balance) / initial_balance * 100
        
        print(f"💰 Financial Performance:")
        print(f"   Initial Balance: ${initial_balance:.2f}")
        print(f"   Final Balance: ${final_balance:.2f}")
        print(f"   Total Return: {total_return:+.2f}%")
        print()
        
        print(f"📈 Trading Activity:")
        print(f"   Total Trades: {len(bot.trades)}")
        print(f"   Hedge Pairs Created: {len(bot.hedge_pairs)}")
        print(f"   Hedge Triggers: {len([e for e in hedge_events if e['type'] == 'hedge_triggered'])}")
        print(f"   Hedge Closures: {len([e for e in hedge_events if e['type'] == 'hedge_closed'])}")
        print()
        
        # Trade details
        if bot.trades:
            print(f"🔍 Trade Details:")
            for i, trade in enumerate(bot.trades[-6:], 1):  # Show last 6 trades
                status_emoji = "🟢" if trade.status == "open" else "🔴"
                type_emoji = "📈" if trade.side == "buy" else "📉"
                pnl_text = f"(P&L: ${trade.pnl/self.config.leverage:.2f})" if trade.pnl else ""
                print(f"   {status_emoji} {type_emoji} {trade.side.upper()} @ ${trade.price:.2f} {pnl_text}")
        
        # Price statistics
        print(f"\n📊 Market Data:")
        print(f"   Price Range: ${price_data['low'].min():.2f} - ${price_data['high'].max():.2f}")
        print(f"   Price Volatility: {price_data['close'].pct_change().std()*100:.2f}%")
        print(f"   Total Candles: {len(price_data)}")
        
        # Risk metrics
        if len(balance_history) > 1:
            balance_series = pd.Series([b['balance'] for b in balance_history])
            max_balance = balance_series.max()
            min_balance = balance_series.min()
            max_drawdown = (max_balance - min_balance) / max_balance * 100
            
            print(f"\n⚠️  Risk Metrics:")
            print(f"   Max Drawdown: {max_drawdown:.2f}%")
            print(f"   Balance Range: ${min_balance:.2f} - ${max_balance:.2f}")


class MockExchange:
    """Enhanced mock exchange for backtesting"""
    def __init__(self):
        self.orders = []
        self.order_id = 1000
        self.current_prices = {}
    
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
        return {'last': self.current_prices.get(symbol, 2000.0)}


if __name__ == "__main__":
    demo = HistoricalDataDemo()
    
    print("🎯 Choose demo type:")
    print("1. ETH/USDT Historical Data")
    print("2. BTC/USDT Historical Data") 
    print("3. Quick Mock Data Demo")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        demo.run_backtest('ETH/USDT')
    elif choice == "2":
        demo.run_backtest('BTC/USDT')
    else:
        demo.run_backtest('ETH/USDT')  # Will use mock data if exchange fails
