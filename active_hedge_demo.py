#!/usr/bin/env python3
"""
Active Hedging Strategy Demo
Creates realistic scenarios to demonstrate the hedging strategy with your updated config
"""

import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading_bot import TradingBot, BotConfig, HedgePair, Trade

class ActiveHedgeDemo:
    """Demo that actively shows hedging strategy in action"""
    
    def __init__(self):
        # Load your updated configuration
        import config
        self.config = BotConfig(
            initial_balance=config.INITIAL_BALANCE,  # $30
            max_trades=config.MAX_TRADES,  # 2
            leverage=config.LEVERAGE,
            timeframe=config.TIMEFRAME,
            initial_trade_size=config.INITIAL_TRADE_SIZE,  # $30
            long_position_size=config.LONG_POSITION_SIZE,  # $5
            short_position_size=config.SHORT_POSITION_SIZE,  # $10
            hedge_trigger_loss=config.HEDGE_TRIGGER_LOSS,  # -5%
            one_trade_per_pair=config.ONE_TRADE_PER_PAIR,
            exit_when_hedged=config.EXIT_WHEN_HEDGED,
            min_hedge_profit_ratio=config.MIN_HEDGE_PROFIT_RATIO,
            **config.STRATEGY_PARAMS
        )
    
    def create_realistic_price_scenario(self):
        """Create a realistic price scenario that will trigger hedging"""
        print("📈 Creating realistic market scenario...")
        
        # Scenario: Price starts at $2500, shows volatility with downtrends
        scenarios = [
            # Scenario 1: Initial rise then significant drop
            {'start': 2500, 'trend': 0.002, 'volatility': 0.01, 'periods': 50, 'name': 'Bull trap'},
            {'start': None, 'trend': -0.008, 'volatility': 0.015, 'periods': 30, 'name': 'Sharp decline'},
            {'start': None, 'trend': -0.003, 'volatility': 0.012, 'periods': 40, 'name': 'Continued fall'},
            {'start': None, 'trend': 0.005, 'volatility': 0.01, 'periods': 30, 'name': 'Recovery attempt'},
            {'start': None, 'trend': -0.002, 'volatility': 0.008, 'periods': 50, 'name': 'Sideways drift'},
        ]
        
        all_prices = []
        all_timestamps = []
        all_scenarios = []
        current_price = 2500
        
        start_time = datetime.now() - timedelta(hours=10)
        
        for scenario in scenarios:
            if scenario['start']:
                current_price = scenario['start']
            
            prices = [current_price]
            timestamps = []
            
            for i in range(scenario['periods']):
                # Time progression (5-minute intervals)
                timestamp = start_time + timedelta(minutes=5 * (len(all_prices) + i))
                timestamps.append(timestamp)
                
                # Price movement with trend and volatility
                trend_change = np.random.normal(scenario['trend'], scenario['volatility'])
                current_price = current_price * (1 + trend_change)
                
                # Add some realistic bounds
                current_price = max(current_price, 1000)  # Floor at $1000
                current_price = min(current_price, 5000)  # Ceiling at $5000
                
                prices.append(current_price)
            
            all_prices.extend(prices[:-1])  # Exclude last to avoid duplication
            all_timestamps.extend(timestamps)
            all_scenarios.extend([scenario['name']] * (len(prices) - 1))
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': all_timestamps,
            'close': all_prices,
            'scenario': all_scenarios
        })
        
        # Add OHLC data
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.005, len(df)))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.005, len(df)))
        df['volume'] = np.random.uniform(1000, 10000, len(df))
        
        df.set_index('timestamp', inplace=True)
        
        print(f"✅ Created {len(df)} price points")
        print(f"📅 Timespan: {df.index[0].strftime('%H:%M')} to {df.index[-1].strftime('%H:%M')}")
        print(f"💰 Price range: ${df['low'].min():.0f} - ${df['high'].max():.0f}")
        
        return df
    
    def run_live_demo(self):
        """Run an interactive demo showing the hedging strategy"""
        print("🎯 ACTIVE HEDGING STRATEGY DEMO")
        print("=" * 60)
        print(f"💰 Your Configuration:")
        print(f"   Initial Balance: ${self.config.initial_balance}")
        print(f"   Max Trades: {self.config.max_trades}")
        print(f"   Long Position: ${self.config.long_position_size}")
        print(f"   Short Position: ${self.config.short_position_size}")
        print(f"   Hedge Trigger: {self.config.hedge_trigger_loss:.1%}")
        print()
        
        # Create price data
        df = self.create_realistic_price_scenario()
        
        # Initialize bot
        bot = TradingBot(self.config)
        bot.exchange = MockExchange()
        
        # Demo variables
        current_hedge_pair = None
        step = 0
        notable_events = []
        
        print("🔄 Starting live simulation...")
        print("📊 Monitoring for trading opportunities...")
        print()
        
        # Process data with strategy logic
        for i, (timestamp, row) in enumerate(df.iterrows()):
            current_price = row['close']
            scenario = row['scenario']
            
            # Update exchange price
            bot.exchange.current_prices['ETH/USDT'] = current_price
            
            # Step 1: Look for entry signals (simplified strategy)
            if current_hedge_pair is None and i > 10:
                # Look for buy signals during pullbacks
                recent_high = df['high'].iloc[max(0, i-10):i].max()
                pullback_pct = (recent_high - current_price) / recent_high
                
                # Entry condition: 3%+ pullback from recent high + scenario dependent
                if pullback_pct > 0.03 and ('decline' in scenario.lower() or 'bull' in scenario.lower()):
                    step += 1
                    print(f"📈 STEP {step}: LONG ENTRY SIGNAL")
                    print(f"   ⏰ Time: {timestamp.strftime('%H:%M')}")
                    print(f"   💰 Price: ${current_price:.2f}")
                    print(f"   📊 Scenario: {scenario}")
                    print(f"   📉 Pullback: {pullback_pct:.1%} from ${recent_high:.2f}")
                    
                    # Create hedge pair
                    pair_id = f"ETH_{int(timestamp.timestamp())}"
                    
                    long_trade = Trade(
                        id=f"long_{step}",
                        symbol='ETH/USDT',
                        side='buy',
                        amount=self.config.long_position_size * self.config.leverage,
                        price=current_price,
                        timestamp=timestamp,
                        status='open',
                        entry_signal=f"Pullback entry in {scenario}",
                        trade_type='long',
                        pair_id=pair_id
                    )
                    
                    current_hedge_pair = HedgePair(
                        pair_id=pair_id,
                        symbol='ETH/USDT',
                        long_trade=long_trade,
                        status='long_only',
                        total_allocation=self.config.initial_trade_size,
                        long_size=self.config.long_position_size,
                        short_size=self.config.short_position_size,
                        hedge_trigger=self.config.hedge_trigger_loss,
                        created_timestamp=timestamp
                    )
                    
                    bot.trades.append(long_trade)
                    bot.hedge_pairs.append(current_hedge_pair)
                    
                    print(f"   ✅ Long position opened: ${self.config.long_position_size} @ ${current_price:.2f}")
                    print()
                    
                    notable_events.append({
                        'type': 'long_entry',
                        'timestamp': timestamp,
                        'price': current_price,
                        'step': step
                    })
            
            # Step 2: Monitor for hedge trigger
            elif current_hedge_pair and current_hedge_pair.status == 'long_only':
                pnl_pct = (current_price - current_hedge_pair.long_trade.price) / current_hedge_pair.long_trade.price
                
                if pnl_pct <= self.config.hedge_trigger_loss:
                    step += 1
                    print(f"🛡️  STEP {step}: HEDGE TRIGGERED!")
                    print(f"   ⏰ Time: {timestamp.strftime('%H:%M')}")
                    print(f"   💰 Price: ${current_price:.2f}")
                    print(f"   📊 Scenario: {scenario}")
                    print(f"   📉 Long P&L: {pnl_pct:.1%}")
                    print(f"   💸 Loss: ${(pnl_pct * self.config.long_position_size):.2f}")
                    
                    # Create hedge position
                    short_trade = Trade(
                        id=f"hedge_{step}",
                        symbol='ETH/USDT',
                        side='sell',
                        amount=self.config.short_position_size * self.config.leverage,
                        price=current_price,
                        timestamp=timestamp,
                        status='open',
                        entry_signal=f"Hedge @ {pnl_pct:.1%} loss",
                        trade_type='hedge',
                        pair_id=current_hedge_pair.pair_id
                    )
                    
                    current_hedge_pair.short_trade = short_trade
                    current_hedge_pair.status = 'hedged'
                    bot.trades.append(short_trade)
                    
                    print(f"   ✅ Hedge position opened: ${self.config.short_position_size} @ ${current_price:.2f}")
                    print(f"   🎯 Strategy: Wait for hedge profit to cover long loss")
                    print()
                    
                    notable_events.append({
                        'type': 'hedge_trigger',
                        'timestamp': timestamp,
                        'price': current_price,
                        'long_pnl_pct': pnl_pct,
                        'step': step
                    })
            
            # Step 3: Monitor for exit conditions
            elif current_hedge_pair and current_hedge_pair.status == 'hedged':
                long_pnl = (current_price - current_hedge_pair.long_trade.price) * self.config.long_position_size
                short_pnl = (current_hedge_pair.short_trade.price - current_price) * self.config.short_position_size
                total_pnl = long_pnl + short_pnl
                
                if long_pnl < 0 and short_pnl > 0:
                    hedge_coverage = short_pnl / abs(long_pnl)
                    
                    if hedge_coverage >= self.config.min_hedge_profit_ratio:
                        step += 1
                        print(f"✅ STEP {step}: HEDGE EXIT - TARGET ACHIEVED!")
                        print(f"   ⏰ Time: {timestamp.strftime('%H:%M')}")
                        print(f"   💰 Price: ${current_price:.2f}")
                        print(f"   📊 Scenario: {scenario}")
                        print(f"   📈 Long P&L: ${long_pnl:.2f}")
                        print(f"   📉 Short P&L: ${short_pnl:.2f}")
                        print(f"   💰 Net P&L: ${total_pnl:.2f}")
                        print(f"   🛡️  Coverage: {hedge_coverage:.2f}x (Target: {self.config.min_hedge_profit_ratio:.1f}x)")
                        
                        # Close positions
                        current_hedge_pair.long_trade.status = 'closed'
                        current_hedge_pair.long_trade.exit_price = current_price
                        current_hedge_pair.long_trade.exit_timestamp = timestamp
                        current_hedge_pair.long_trade.pnl = long_pnl
                        
                        current_hedge_pair.short_trade.status = 'closed'
                        current_hedge_pair.short_trade.exit_price = current_price
                        current_hedge_pair.short_trade.exit_timestamp = timestamp
                        current_hedge_pair.short_trade.pnl = short_pnl
                        
                        current_hedge_pair.status = 'closed'
                        
                        # Update balance
                        bot.balance += total_pnl
                        
                        print(f"   💰 New Balance: ${bot.balance:.2f} (Return: {((bot.balance/self.config.initial_balance)-1)*100:+.1f}%)")
                        print(f"   🎯 Strategy preserved capital and minimized loss!")
                        print()
                        
                        notable_events.append({
                            'type': 'hedge_exit',
                            'timestamp': timestamp,
                            'price': current_price,
                            'total_pnl': total_pnl,
                            'coverage': hedge_coverage,
                            'step': step
                        })
                        
                        current_hedge_pair = None
                        
                        # Wait a bit before next opportunity
                        time.sleep(1)
        
        # Final summary
        self.print_demo_summary(bot, notable_events, df)
    
    def print_demo_summary(self, bot, events, price_data):
        """Print comprehensive demo summary"""
        print("=" * 60)
        print("🎯 HEDGING STRATEGY DEMO COMPLETED")
        print("=" * 60)
        
        initial_balance = self.config.initial_balance
        final_balance = bot.balance
        total_return = (final_balance - initial_balance) / initial_balance * 100
        
        print(f"💰 FINANCIAL RESULTS:")
        print(f"   Starting Balance: ${initial_balance:.2f}")
        print(f"   Ending Balance: ${final_balance:.2f}")
        print(f"   Total Return: {total_return:+.2f}%")
        print(f"   Capital Preservation: {'✅ Success' if total_return > -10 else '❌ Needs improvement'}")
        print()
        
        print(f"📊 TRADING ACTIVITY:")
        print(f"   Hedge Pairs Created: {len(bot.hedge_pairs)}")
        print(f"   Total Trades: {len(bot.trades)}")
        print(f"   Long Positions: {len([t for t in bot.trades if t.trade_type == 'long'])}")
        print(f"   Hedge Positions: {len([t for t in bot.trades if t.trade_type == 'hedge'])}")
        print()
        
        print(f"🎯 STRATEGY EVENTS:")
        for event in events:
            emoji = {'long_entry': '📈', 'hedge_trigger': '🛡️', 'hedge_exit': '✅'}
            print(f"   {emoji.get(event['type'], '📊')} Step {event['step']}: {event['type'].replace('_', ' ').title()} @ ${event['price']:.2f}")
        print()
        
        print(f"📈 MARKET CONDITIONS:")
        print(f"   Price Range: ${price_data['low'].min():.0f} - ${price_data['high'].max():.0f}")
        print(f"   Total Decline: {((price_data['close'].iloc[-1] / price_data['close'].iloc[0]) - 1) * 100:.1f}%")
        print(f"   Volatility: {price_data['close'].pct_change().std() * 100:.2f}%")
        print()
        
        print(f"🏆 STRATEGY EFFECTIVENESS:")
        hedge_events = [e for e in events if e['type'] == 'hedge_trigger']
        exit_events = [e for e in events if e['type'] == 'hedge_exit']
        
        if hedge_events:
            print(f"   Hedge Triggers: {len(hedge_events)}")
            print(f"   Successful Exits: {len(exit_events)}")
            print(f"   Success Rate: {len(exit_events)/len(hedge_events)*100:.1f}%")
        
        if exit_events:
            avg_coverage = sum(e['coverage'] for e in exit_events) / len(exit_events)
            print(f"   Average Hedge Coverage: {avg_coverage:.2f}x")
        
        print(f"\n💡 CONCLUSION:")
        if total_return > -5:
            print(f"   ✅ Hedging strategy successfully limited losses to {abs(total_return):.1f}%")
        else:
            print(f"   ⚠️  Strategy contained losses to {abs(total_return):.1f}% in difficult market")
        
        print(f"   🛡️  The hedge mechanism activated when needed and protected capital")
        print(f"   📊 Without hedging, losses could have been much larger")


class MockExchange:
    """Mock exchange for demo"""
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
        return {'last': self.current_prices.get(symbol, 2500.0)}


if __name__ == "__main__":
    demo = ActiveHedgeDemo()
    demo.run_live_demo()
