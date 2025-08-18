#!/usr/bin/env python3
"""
Standalone Trading Bot based on Freqtrade ElliotV5_SMA Strategy
Converts the strategy to work with CCXT and Binance Testnet
"""

import ccxt
import pandas as pd
import numpy as np
import talib.abstract as ta
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from functools import reduce
import asyncio
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Trade data structure"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    timestamp: datetime
    status: str  # 'open', 'closed'
    entry_signal: str
    exit_signal: Optional[str] = None
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None

@dataclass
class BotConfig:
    """Bot configuration"""
    # Strategy parameters from original Freqtrade strategy
    base_nb_candles_buy: int = 17
    base_nb_candles_sell: int = 49
    low_offset: float = 0.978
    high_offset: float = 1.019
    ewo_low: float = -17.457
    ewo_high: float = 3.34
    rsi_buy: int = 65
    fast_ewo: int = 50
    slow_ewo: int = 200
    stoploss: float = -0.189
    
    # Bot specific parameters
    initial_balance: float = 100.0
    max_trades: int = 5
    leverage: float = 10.0
    timeframe: str = '5m'
    symbols: List[str] = None
    
    # Volume filtering parameters
    max_symbols: int = 100
    min_24h_volume: float = 1000000
    filter_by_volume: bool = True
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                'XRP/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT'
            ]

def EWO(dataframe: pd.DataFrame, ema_length: int = 5, ema2_length: int = 35) -> pd.Series:
    """Elliott Wave Oscillator"""
    df = dataframe.copy()
    ema1 = ta.SMA(df, timeperiod=ema_length)
    ema2 = ta.SMA(df, timeperiod=ema2_length)
    emadif = (ema1 - ema2) / df['close'] * 100
    return emadif

class TradingStrategy:
    """Trading strategy based on Freqtrade ElliotV5_SMA"""
    
    def __init__(self, config: BotConfig):
        self.config = config
    
    def populate_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Populate technical indicators"""
        # Create all moving averages at once to avoid DataFrame fragmentation
        ma_columns = {}
        
        # Calculate all buy moving averages
        for val in range(5, 81):  # Range similar to original IntParameter
            ma_columns[f'ma_buy_{val}'] = ta.EMA(dataframe, timeperiod=val)
        
        # Calculate all sell moving averages
        for val in range(5, 81):
            ma_columns[f'ma_sell_{val}'] = ta.EMA(dataframe, timeperiod=val)
        
        # Calculate other indicators
        ma_columns['EWO'] = EWO(dataframe, self.config.fast_ewo, self.config.slow_ewo)
        ma_columns['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Combine all columns at once using pd.concat to avoid fragmentation
        ma_df = pd.DataFrame(ma_columns, index=dataframe.index)
        dataframe = pd.concat([dataframe, ma_df], axis=1)
        
        return dataframe
    
    def populate_entry_signals(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Generate entry signals"""
        conditions = []
        price_above_threshold = dataframe['close'] > 0.5
        
        # Condition 1: EWO high
        conditions.append(
            (price_above_threshold) &
            (dataframe['close'] < (dataframe[f'ma_buy_{self.config.base_nb_candles_buy}'] * self.config.low_offset)) &
            (dataframe['EWO'] > self.config.ewo_high) &
            (dataframe['rsi'] < self.config.rsi_buy) &
            (dataframe['volume'] > 0)
        )
        
        # Condition 2: EWO low
        conditions.append(
            (price_above_threshold) &
            (dataframe['close'] < (dataframe[f'ma_buy_{self.config.base_nb_candles_buy}'] * self.config.low_offset)) &
            (dataframe['EWO'] < self.config.ewo_low) &
            (dataframe['volume'] > 0)
        )
        
        # Create signal column efficiently
        enter_long = pd.Series(0, index=dataframe.index, name='enter_long')
        if conditions:
            enter_long.loc[reduce(lambda x, y: x | y, conditions)] = 1
        
        # Add signal column using concat to avoid fragmentation
        dataframe = pd.concat([dataframe, enter_long], axis=1)
        
        return dataframe
    
    def populate_exit_signals(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Generate exit signals"""
        conditions = []
        
        conditions.append(
            (dataframe['close'] > (dataframe[f'ma_sell_{self.config.base_nb_candles_sell}'] * self.config.high_offset)) &
            (dataframe['volume'] > 0)
        )
        
        # Create signal column efficiently
        exit_long = pd.Series(0, index=dataframe.index, name='exit_long')
        if conditions:
            exit_long.loc[reduce(lambda x, y: x | y, conditions)] = 1
        
        # Add signal column using concat to avoid fragmentation
        dataframe = pd.concat([dataframe, exit_long], axis=1)
        
        return dataframe

class TradingBot:
    """Main trading bot class"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.strategy = TradingStrategy(config)
        self.exchange = None
        self.trades: List[Trade] = []
        self.balance = config.initial_balance
        self.is_running = False
        self.data_cache = {}
        
        # Initialize exchange
        self._init_exchange()
    
    def _init_exchange(self):
        """Initialize CCXT exchange connection"""
        try:
            # Try to load API keys from config
            try:
                import config
                api_key = config.BINANCE_TESTNET_API_KEY
                secret = config.BINANCE_TESTNET_SECRET
            except (ImportError, AttributeError):
                api_key = 'your_testnet_api_key'
                secret = 'your_testnet_secret'
            
            # Check if we have valid API keys
            if api_key == 'your_testnet_api_key' or secret == 'your_testnet_secret':
                logger.warning("No valid API keys found, using mock exchange")
                self.exchange = self._create_mock_exchange()
                return
            
            # Binance Testnet configuration
            self.exchange = ccxt.binance({
                'apiKey': api_key,
                'secret': secret,
                'sandbox': True,  # Enable testnet/sandbox mode
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # Use futures
                }
            })
            
            # Test connection
            balance = self.exchange.fetch_balance()
            logger.info("Successfully connected to Binance Testnet")
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            # For demo purposes, create a mock exchange
            self.exchange = self._create_mock_exchange()
    
    def get_top_volume_symbols(self, limit: int = 100) -> List[str]:
        """Get top trading pairs by 24h volume"""
        try:
            # Fetch all tickers
            tickers = self.exchange.fetch_tickers()
            
            # Filter USDT pairs only
            usdt_pairs = {}
            for symbol, ticker in tickers.items():
                if '/USDT' in symbol and ticker['quoteVolume']:
                    usdt_pairs[symbol] = ticker['quoteVolume']
            
            # Sort by volume and get top pairs
            sorted_pairs = sorted(usdt_pairs.items(), key=lambda x: x[1], reverse=True)
            top_symbols = [pair[0] for pair in sorted_pairs[:limit]]
            
            logger.info(f"Found {len(top_symbols)} top volume USDT pairs")
            return top_symbols
            
        except Exception as e:
            logger.error(f"Error fetching symbols by volume: {e}")
            # Fallback to default symbols
            return [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                'XRP/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT',
                'LINK/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'MATIC/USDT',
                'ALGO/USDT', 'VET/USDT', 'FTT/USDT', 'ICP/USDT', 'THETA/USDT'
            ]
    
    def update_symbol_list(self):
        """Update the trading symbol list based on volume"""
        try:
            if not self.config.filter_by_volume:
                logger.info("Volume filtering disabled, keeping current symbols")
                return
            
            # Get top symbols by volume
            top_symbols = self.get_top_volume_symbols(self.config.max_symbols)
            
            # Filter symbols by minimum volume if exchange is real
            if hasattr(self.exchange, 'fetch_tickers'):
                try:
                    tickers = self.exchange.fetch_tickers()
                    filtered_symbols = []
                    
                    for symbol in top_symbols:
                        if symbol in tickers and tickers[symbol]['quoteVolume'] >= self.config.min_24h_volume:
                            filtered_symbols.append(symbol)
                    
                    self.config.symbols = filtered_symbols[:self.config.max_symbols]
                    logger.info(f"Updated symbol list: {len(self.config.symbols)} symbols with volume >= ${self.config.min_24h_volume:,.0f}")
                    
                except Exception as e:
                    logger.error(f"Error filtering symbols by volume: {e}")
                    self.config.symbols = top_symbols[:20]  # Fallback to top 20
            else:
                # Using mock exchange, use predefined list
                self.config.symbols = top_symbols[:20]
                
        except Exception as e:
            logger.error(f"Error updating symbol list: {e}")
            # Keep existing symbols if update fails
    
    def _create_mock_exchange(self):
        """Create a mock exchange for demonstration"""
        class MockExchange:
            def __init__(self):
                # Generate mock symbols with volumes
                self.mock_symbols = [
                    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                    'XRP/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT',
                    'LINK/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'MATIC/USDT',
                    'ALGO/USDT', 'VET/USDT', 'ATOM/USDT', 'ICP/USDT', 'THETA/USDT',
                    'FIL/USDT', 'TRX/USDT', 'ETC/USDT', 'XLM/USDT', 'MANA/USDT',
                    'SAND/USDT', 'CRO/USDT', 'NEAR/USDT', 'GALA/USDT', 'SHIB/USDT'
                ]
            
            def fetch_tickers(self):
                """Mock ticker data with volumes"""
                tickers = {}
                base_volumes = [5000000, 3000000, 2000000, 1500000, 1200000]  # Different volume tiers
                
                for i, symbol in enumerate(self.mock_symbols):
                    volume_tier = i % len(base_volumes)
                    volume = base_volumes[volume_tier] * (1 + np.random.random())
                    
                    tickers[symbol] = {
                        'symbol': symbol,
                        'quoteVolume': volume,
                        'last': 50000 + np.random.randn() * 10000 if 'BTC' in symbol else 3000 + np.random.randn() * 1000,
                        'percentage': np.random.randn() * 5
                    }
                return tickers
            
            def fetch_ohlcv(self, symbol, timeframe, limit=100):
                # Generate mock data based on symbol
                now = datetime.now()
                data = []
                
                # Different base prices for different symbols
                if 'BTC' in symbol:
                    base_price = 50000
                elif 'ETH' in symbol:
                    base_price = 3000
                elif 'BNB' in symbol:
                    base_price = 300
                else:
                    base_price = 100 + np.random.random() * 500
                
                for i in range(limit):
                    timestamp = int((now - timedelta(minutes=5*i)).timestamp() * 1000)
                    # Mock OHLCV data with more realistic price movements
                    open_price = base_price * (1 + np.random.randn() * 0.02)
                    close_price = open_price * (1 + np.random.randn() * 0.01)
                    high_price = max(open_price, close_price) * (1 + abs(np.random.randn() * 0.005))
                    low_price = min(open_price, close_price) * (1 - abs(np.random.randn() * 0.005))
                    volume = abs(np.random.randn() * 1000)
                    data.append([timestamp, open_price, high_price, low_price, close_price, volume])
                return list(reversed(data))
            
            def create_market_order(self, symbol, side, amount, params={}):
                return {
                    'id': f'mock_{int(time.time())}',
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': 50000 + np.random.randn() * 1000,
                    'timestamp': int(time.time() * 1000)
                }
            
            def fetch_balance(self):
                return {'USDT': {'total': 1000, 'free': 1000, 'used': 0}}
        
        logger.info("Using mock exchange for demonstration")
        return MockExchange()
    
    def get_historical_data(self, symbol: str, timeframe: str = '5m', limit: int = 200) -> pd.DataFrame:
        """Fetch historical OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """Analyze a symbol and return signals"""
        df = self.get_historical_data(symbol)
        if df.empty:
            return {'symbol': symbol, 'signal': None, 'price': None}
        
        # Populate indicators and signals
        df = self.strategy.populate_indicators(df)
        df = self.strategy.populate_entry_signals(df)
        df = self.strategy.populate_exit_signals(df)
        
        # Create a defragmented copy for better performance if needed
        # This is only done once per analysis, not during indicator calculation
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
    
    def execute_trade(self, symbol: str, side: str, analysis: Dict):
        """Execute a trade"""
        try:
            # Check if we have available trades
            open_trades = [t for t in self.trades if t.status == 'open']
            if side == 'buy' and len(open_trades) >= self.config.max_trades:
                logger.info(f"Maximum trades ({self.config.max_trades}) already open")
                return
            
            # Calculate position size (risk per trade)
            risk_per_trade = self.balance * 0.02  # 2% risk per trade
            position_size = risk_per_trade / abs(self.config.stoploss)
            
            # Apply leverage
            position_size *= self.config.leverage
            
            if side == 'buy':
                # Place buy order
                order = self.exchange.create_market_order(
                    symbol, 'buy', position_size,
                    params={'leverage': self.config.leverage}
                )
                
                trade = Trade(
                    id=order['id'],
                    symbol=symbol,
                    side=side,
                    amount=position_size,
                    price=analysis['price'],
                    timestamp=datetime.now(),
                    status='open',
                    entry_signal=f"EWO: {analysis['ewo']:.2f}, RSI: {analysis['rsi']:.2f}"
                )
                
                self.trades.append(trade)
                logger.info(f"Opened long position: {symbol} at {analysis['price']:.2f}")
                
            elif side == 'sell':
                # Find open position to close
                open_position = next((t for t in open_trades if t.symbol == symbol), None)
                if open_position:
                    order = self.exchange.create_market_order(
                        symbol, 'sell', open_position.amount,
                        params={'leverage': self.config.leverage}
                    )
                    
                    # Update trade
                    open_position.status = 'closed'
                    open_position.exit_price = analysis['price']
                    open_position.exit_timestamp = datetime.now()
                    open_position.exit_signal = f"MA Sell Signal"
                    
                    # Calculate PnL
                    price_diff = open_position.exit_price - open_position.price
                    open_position.pnl = price_diff * open_position.amount
                    open_position.pnl_percentage = (price_diff / open_position.price) * 100 * self.config.leverage
                    
                    # Update balance
                    self.balance += open_position.pnl
                    
                    logger.info(f"Closed position: {symbol} at {analysis['price']:.2f}, PnL: {open_position.pnl:.2f}")
        
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
    
    def check_stop_loss(self):
        """Check and execute stop loss for open positions"""
        open_trades = [t for t in self.trades if t.status == 'open']
        
        for trade in open_trades:
            try:
                current_data = self.analyze_symbol(trade.symbol)
                current_price = current_data['price']
                
                # Calculate stop loss price
                stop_loss_price = trade.price * (1 + self.config.stoploss)
                
                if current_price <= stop_loss_price:
                    # Execute stop loss
                    trade.status = 'closed'
                    trade.exit_price = current_price
                    trade.exit_timestamp = datetime.now()
                    trade.exit_signal = "Stop Loss"
                    
                    price_diff = trade.exit_price - trade.price
                    trade.pnl = price_diff * trade.amount
                    trade.pnl_percentage = (price_diff / trade.price) * 100 * self.config.leverage
                    
                    self.balance += trade.pnl
                    
                    logger.info(f"Stop loss triggered: {trade.symbol} at {current_price:.2f}")
                    
            except Exception as e:
                logger.error(f"Error checking stop loss for {trade.symbol}: {e}")
    
    def run_strategy(self):
        """Main strategy execution loop"""
        symbol_batch_size = 10  # Process symbols in batches to avoid overwhelming
        symbol_rotation = 0
        
        while self.is_running:
            try:
                logger.info("Running strategy analysis...")
                
                # Check stop losses first
                self.check_stop_loss()
                
                # Process symbols in batches to manage load
                total_symbols = len(self.config.symbols)
                start_idx = (symbol_rotation * symbol_batch_size) % total_symbols
                end_idx = min(start_idx + symbol_batch_size, total_symbols)
                
                if start_idx >= end_idx:
                    start_idx = 0
                    end_idx = min(symbol_batch_size, total_symbols)
                
                current_batch = self.config.symbols[start_idx:end_idx]
                logger.info(f"Analyzing batch {symbol_rotation + 1}: {len(current_batch)} symbols ({start_idx}-{end_idx})")
                
                signals_found = 0
                for symbol in current_batch:
                    try:
                        analysis = self.analyze_symbol(symbol)
                        
                        # Always cache analysis for web interface
                        self.data_cache[symbol] = analysis
                        
                        if analysis['signal']:
                            signals_found += 1
                            logger.info(f"Signal detected: {symbol} - {analysis['signal']}")
                            self.execute_trade(symbol, analysis['signal'], analysis)
                            
                    except Exception as e:
                        logger.error(f"Error analyzing {symbol}: {e}")
                        continue
                
                logger.info(f"Batch complete. Signals found: {signals_found}")
                
                # Rotate to next batch
                symbol_rotation += 1
                
                # Update symbol list every hour (when we complete a full cycle)
                if symbol_rotation % (total_symbols // symbol_batch_size + 1) == 0:
                    logger.info("Updating symbol list based on current volume...")
                    self.update_symbol_list()
                    symbol_rotation = 0
                
                # Wait for next iteration
                time.sleep(30)  # Check every 30 seconds for better responsiveness
                
            except Exception as e:
                logger.error(f"Error in strategy execution: {e}")
                time.sleep(30)
    
    def start(self):
        """Start the trading bot"""
        self.is_running = True
        logger.info("Starting trading bot...")
        
        # Update symbol list based on volume before starting
        logger.info("Updating symbol list based on volume...")
        self.update_symbol_list()
        logger.info(f"Trading {len(self.config.symbols)} symbols: {', '.join(self.config.symbols[:10])}{'...' if len(self.config.symbols) > 10 else ''}")
        
        # Run strategy in separate thread
        strategy_thread = threading.Thread(target=self.run_strategy)
        strategy_thread.daemon = True
        strategy_thread.start()
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        logger.info("Stopping trading bot...")
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        open_trades = [t for t in self.trades if t.status == 'open']
        closed_trades = [t for t in self.trades if t.status == 'closed']
        
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        total_return = (total_pnl / self.config.initial_balance) * 100 if total_pnl else 0
        
        return {
            'initial_balance': self.config.initial_balance,
            'current_balance': self.balance,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_trades': len(self.trades)
        }

if __name__ == "__main__":
    # Initialize bot configuration
    config = BotConfig()
    
    # Create and start bot
    bot = TradingBot(config)
    bot.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        bot.stop()
