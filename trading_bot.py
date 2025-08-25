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
from dataclasses import dataclass, asdict, field
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

# Import telegram bot for notifications
try:
    from telegram_bot import telegram_bot, send_trade_entry_notification, send_trade_exit_notification, send_hedge_completion_notification, send_error_notification, send_bot_status_notification
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("Telegram bot module not available. Notifications will be disabled.")

# Import enhanced telegram bot for startup messages
try:
    from telegram_bot_enhanced import send_bot_ready_notification, send_bot_stopped_notification
    TELEGRAM_ENHANCED_AVAILABLE = True
except ImportError:
    TELEGRAM_ENHANCED_AVAILABLE = False

@dataclass
class Trade:
    """Trade data structure with detailed entry/exit reasons"""
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
    trade_type: str = 'normal'  # 'normal', 'long', 'hedge'
    pair_id: Optional[str] = None  # Links hedge trades together
    
    # Detailed reasons
    entry_reason: Optional[str] = None  # Detailed entry analysis
    exit_reason: Optional[str] = None   # Detailed exit analysis
    technical_indicators: Optional[Dict] = None  # Technical indicator values at entry
    market_conditions: Optional[str] = None  # Market condition description
    
    # Trailing stop data
    max_price: Optional[float] = None  # Highest price reached (for trailing stop)
    trailing_stop_price: Optional[float] = None  # Current trailing stop price

@dataclass
class HedgePair:
    """Hedge trade pair structure"""
    pair_id: str
    symbol: str
    long_trade: Optional[Trade] = None
    short_trade: Optional[Trade] = None
    status: str = 'long_only'  # 'long_only', 'hedged', 'closed'
    total_allocation: float = 30.0  # Total money allocated to this pair
    long_size: float = 10.0  # Size of long position
    short_size: float = 15.0  # Size of short hedge position
    hedge_trigger: float = -0.05  # -5% loss triggers hedge
    created_timestamp: Optional[datetime] = None

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
    
    # Telegram configuration
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Hedging strategy parameters
    initial_trade_size: float = 30.0
    long_position_size: float = 10.0
    short_position_size: float = 15.0
    hedge_trigger_loss: float = -0.05
    one_trade_per_pair: bool = True
    exit_when_hedged: bool = True
    min_hedge_profit_ratio: float = 1.0
    
    # ROI configuration
    minimal_roi: Dict[str, float] = None
    
    # Trailing stop configuration
    trailing_stop: bool = False
    trailing_stop_positive: float = 0.005
    trailing_stop_positive_offset: float = 0.03
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
                'XRP/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT', 'LUNA/USDT'
            ]
        
        # Set default ROI if not provided
        if self.minimal_roi is None:
            self.minimal_roi = {
                "0": 0.70,    # 70% ROI (exit immediately if profit hits 70%)
                "1": 0.65,    # 65% ROI after 1 minute
                "2": 0.60,    # 60% ROI after 2 minutes
                "3": 0.55,    # 55% ROI after 3 minutes
                "4": 0.50,    # 50% ROI after 4 minutes
                "5": 0.45,    # 45% ROI after 5 minutes
                "6": 0.40,    # 40% ROI after 6 minutes
                "7": 0.35,    # 35% ROI after 7 minutes
                "8": 0.30,    # 30% ROI after 8 minutes
                "9": 0.25,    # 25% ROI after 9 minutes
                "10": 0.20,   # 20% ROI after 10 minutes
                "15": 0.15,   # 15% ROI after 15 minutes
                "20": 0.10,   # 10% ROI after 20 minutes
                "30": 0.07,   # 7% ROI after 30 minutes
                "45": 0.05,   # 5% ROI after 45 minutes
                "60": 0.03,   # 3% ROI after 60 minutes
                "90": 0.01,   # 1% ROI after 90 minutes
                "120": 0      # Exit after 120 minutes (2 hours)
            }

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
        # Create only the specific moving averages needed by the strategy
        ma_columns = {}
        
        # Calculate only the specific buy and sell moving averages from config
        ma_columns[f'ma_buy_{self.config.base_nb_candles_buy}'] = ta.EMA(dataframe, timeperiod=self.config.base_nb_candles_buy)
        ma_columns[f'ma_sell_{self.config.base_nb_candles_sell}'] = ta.EMA(dataframe, timeperiod=self.config.base_nb_candles_sell)
        
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
    """Main trading bot class with hedging strategy"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.strategy = TradingStrategy(config)
        self.exchange = None
        self.trades: List[Trade] = []
        self.hedge_pairs: List[HedgePair] = []
        self.balance = config.initial_balance
        self.is_running = False
        self.data_cache = {}
        self.telegram_enabled = TELEGRAM_AVAILABLE and getattr(config, 'TELEGRAM_ENABLED', False)
        
        # Initialize exchange
        self._init_exchange()
    
    def _run_async_telegram_task(self, coro):
        """Helper function to run async Telegram tasks safely"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the task
                asyncio.create_task(coro)
            else:
                # If no loop is running, create new one
                loop.run_until_complete(coro)
        except RuntimeError:
            # If no event loop, create a new one
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(coro)
                new_loop.close()
            except Exception as e:
                logger.error(f"Error running async Telegram task: {e}")
    
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
            
            # Configure margin mode and leverage for trading symbols
            self._configure_margin_and_leverage()
            
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            # For demo purposes, create a mock exchange
            self.exchange = self._create_mock_exchange()
    
    def _configure_margin_and_leverage(self):
        """Configure isolated margin mode and leverage for all trading symbols"""
        try:
            for symbol in self.config.symbols[:10]:  # Configure first 10 symbols to avoid rate limits
                try:
                    # Set margin mode to ISOLATED
                    self.exchange.set_margin_mode('isolated', symbol)
                    logger.info(f"Set {symbol} to isolated margin mode")
                    
                    # Set leverage using Binance futures API format
                    symbol_raw = symbol.replace('/', '')  # Remove slash for Binance API
                    try:
                        leverage_result = self.exchange.fapiPrivate_post_leverage({
                            'symbol': symbol_raw,
                            'leverage': int(self.config.leverage)
                        })
                        logger.info(f"Set {symbol} leverage to {self.config.leverage}x: {leverage_result}")
                    except Exception as leverage_error:
                        # Fallback to CCXT method
                        logger.warning(f"Direct API failed for {symbol}, trying CCXT method: {leverage_error}")
                        try:
                            self.exchange.set_leverage(int(self.config.leverage), symbol)
                            logger.info(f"Set {symbol} leverage to {self.config.leverage}x via CCXT")
                        except Exception as ccxt_error:
                            logger.error(f"Both leverage methods failed for {symbol}: {ccxt_error}")
                            raise ccxt_error
                    
                except Exception as e:
                    logger.warning(f"Could not configure {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error configuring margin and leverage: {e}")
    
    def verify_symbol_configuration(self, symbol: str) -> bool:
        """Verify that a symbol is properly configured with isolated margin and correct leverage"""
        try:
            # Check current leverage setting
            positions = self.exchange.fetch_positions([symbol])
            for position in positions:
                if position['symbol'] == symbol:
                    current_leverage = position.get('leverage', 0)
                    margin_mode = position.get('marginMode', 'unknown')
                    
                    logger.info(f"{symbol} - Leverage: {current_leverage}x, Margin: {margin_mode}")
                    
                    if current_leverage != self.config.leverage:
                        logger.warning(f"{symbol} leverage mismatch: expected {self.config.leverage}x, got {current_leverage}x")
                        return False
                        
                    if margin_mode.lower() != 'isolated':
                        logger.warning(f"{symbol} margin mode mismatch: expected isolated, got {margin_mode}")
                        return False
                        
                    return True
            
            # If no position found, try to configure it
            self.exchange.set_margin_mode('isolated', symbol)
            # Set leverage using Binance futures API format
            symbol_raw = symbol.replace('/', '')  # Remove slash for Binance API
            try:
                leverage_result = self.exchange.fapiPrivate_post_leverage({
                    'symbol': symbol_raw,
                    'leverage': int(self.config.leverage)
                })
                logger.info(f"Configured {symbol}: {self.config.leverage}x isolated margin via direct API")
            except Exception as leverage_error:
                # Fallback to CCXT method
                logger.warning(f"Direct API failed for {symbol}, trying CCXT method: {leverage_error}")
                self.exchange.set_leverage(int(self.config.leverage), symbol)
                logger.info(f"Configured {symbol}: {self.config.leverage}x isolated margin via CCXT")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying {symbol} configuration: {e}")
            return False
            
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
        """Execute a trade using hedging strategy with strict trade limits"""
        try:
            # For hedging strategy, we only process 'buy' signals to start new hedge pairs
            if side != 'buy':
                return

            # Check total active trades (should never exceed 2: 1 buy + 1 hedge)
            active_trades = [t for t in self.trades if t.status == 'open']
            if len(active_trades) >= 2:
                logger.info(f"Maximum trades reached ({len(active_trades)}/2). Cannot open new position.")
                return

            # Check if we already have a hedge pair for this symbol (ONE_TRADE_PER_PAIR enforcement)
            if self.config.one_trade_per_pair:
                existing_pair = self.get_hedge_pair_by_symbol(symbol)
                if existing_pair and existing_pair.status != 'closed':
                    logger.info(f"Hedge pair already exists for {symbol}, skipping (ONE_TRADE_PER_PAIR)")
                    return

            # Check if we can start a new hedge pair (should only allow 1 pair total)
            active_pairs = [hp for hp in self.hedge_pairs if hp.status != 'closed']
            if len(active_pairs) >= 1:  # Only 1 hedge pair allowed (1 buy + 1 hedge max)
                logger.info(f"Maximum hedge pairs (1) already active. Current pairs: {len(active_pairs)}")
                return
            
            # Create new hedge pair and execute initial long position
            pair_id = f"{symbol}_{int(time.time())}"
            hedge_pair = HedgePair(
                pair_id=pair_id,
                symbol=symbol,
                total_allocation=self.config.initial_trade_size,
                long_size=self.config.long_position_size,
                short_size=self.config.short_position_size,
                hedge_trigger=self.config.hedge_trigger_loss,
                created_timestamp=datetime.now()
            )
            
            # Execute long position
            long_trade = self._execute_position(
                symbol=symbol,
                side='buy',
                size=self.config.long_position_size,
                analysis=analysis,
                trade_type='long',
                pair_id=pair_id
            )
            
            if long_trade:
                hedge_pair.long_trade = long_trade
                hedge_pair.status = 'long_only'
                self.hedge_pairs.append(hedge_pair)
                logger.info(f"Started new hedge pair for {symbol}: Long ${self.config.long_position_size}")
            
        except Exception as e:
            logger.error(f"Error executing hedge trade for {symbol}: {e}")
    
    def _execute_position(self, symbol: str, side: str, size: float, analysis: Dict, 
                         trade_type: str = 'normal', pair_id: Optional[str] = None) -> Optional[Trade]:
        """Execute a single position (long or short) with detailed reasons"""
        try:
            # Ensure margin mode and leverage are set for this symbol
            if not self.verify_symbol_configuration(symbol):
                logger.error(f"Failed to configure {symbol} properly")
                return None
            
            # Calculate position size correctly:
            # size = USD amount we want to trade (e.g., $6 for long, $10 for hedge)
            # We need to convert this to the base currency amount WITHOUT multiplying by leverage
            # The leverage will be applied automatically by the exchange
            current_price = analysis['price']
            position_size = size / current_price  # Convert USD to base currency amount
            
            # For futures with leverage, this gives us the notional size
            # The exchange will apply leverage automatically
            
            logger.info(f"Executing {trade_type} {side} position:")
            logger.info(f"  Symbol: {symbol}")
            logger.info(f"  USD Size: ${size}")
            logger.info(f"  Price: ${current_price}")
            logger.info(f"  Base Currency Amount: {position_size}")
            logger.info(f"  Leverage: {self.config.leverage}x (isolated)")
            
            # Create detailed entry reason based on trade type
            if trade_type == 'long':
                entry_reason = self._generate_long_entry_reason(analysis)
                market_conditions = self._assess_market_conditions(symbol, analysis)
            elif trade_type == 'hedge':
                entry_reason = self._generate_hedge_entry_reason(analysis, pair_id)
                market_conditions = "Defensive hedge position due to long position loss"
            else:
                entry_reason = "Standard entry based on strategy signals"
                market_conditions = "Normal market conditions"
            
            # Create order with isolated margin and correct leverage
            order = self.exchange.create_market_order(
                symbol, side, position_size,
                params={
                    'leverage': self.config.leverage,
                    'marginMode': 'isolated'
                }
            )
            
            logger.info(f"Order executed: {order['id']} - {side} {position_size} {symbol} at ${current_price}")
            
            trade = Trade(
                id=order['id'],
                symbol=symbol,
                side=side,
                amount=position_size,
                price=current_price,
                timestamp=datetime.now(),
                status='open',
                entry_signal=f"EWO: {analysis['ewo']:.2f}, RSI: {analysis['rsi']:.2f}",
                trade_type=trade_type,
                pair_id=pair_id,
                entry_reason=entry_reason,
                technical_indicators={
                    'ewo': analysis.get('ewo', 0),
                    'rsi': analysis.get('rsi', 50),
                    'price': analysis['price'],
                    'volume': analysis.get('volume', 0)
                },
                market_conditions=market_conditions
            )
            
            self.trades.append(trade)
            logger.info(f"Opened {trade_type} position: {side} {symbol} at {analysis['price']:.2f}, size: ${size}")
            logger.info(f"Entry reason: {entry_reason}")
            
            # Send Telegram notification for trade entry
            if self.telegram_enabled:
                try:
                    # Convert trade to dict for telegram notification
                    trade_dict = asdict(trade)
                    # Convert datetime to timestamp for JSON serialization
                    trade_dict['timestamp'] = trade.timestamp.timestamp()
                    trade_dict['market_conditions'] = {'description': market_conditions}
                    
                    # Send notification using helper function
                    self._run_async_telegram_task(send_trade_entry_notification(trade_dict))
                    
                    # Also log the entry signal for debugging
                    logger.info(f"📱 ENTRY SIGNAL: {trade.symbol} {trade.side} ${trade.amount:.2f} @ ${trade.price:.4f} - {entry_reason}")
                    
                except Exception as e:
                    logger.error(f"Error sending Telegram entry notification: {e}")
                    # Log entry signal even if Telegram fails
                    logger.warning(f"📱 ENTRY SIGNAL (Telegram failed): {trade.symbol} {trade.side} ${trade.amount:.2f} @ ${trade.price:.4f} - {entry_reason}")
            else:
                # Log entry signal when Telegram is disabled
                logger.info(f"📱 ENTRY SIGNAL (Telegram disabled): {trade.symbol} {trade.side} ${trade.amount:.2f} @ ${trade.price:.4f} - {entry_reason}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing {side} position for {symbol}: {e}")
            return None
    
    def _generate_long_entry_reason(self, analysis: Dict) -> str:
        """Generate detailed reason for long entry"""
        reasons = []
        
        # EWO analysis
        ewo = analysis.get('ewo', 0)
        if ewo > self.config.ewo_high:
            reasons.append(f"EWO bullish signal ({ewo:.2f} > {self.config.ewo_high})")
        elif ewo < self.config.ewo_low:
            reasons.append(f"EWO oversold signal ({ewo:.2f} < {self.config.ewo_low})")
        
        # RSI analysis
        rsi = analysis.get('rsi', 50)
        if rsi < self.config.rsi_buy:
            reasons.append(f"RSI favorable ({rsi:.1f} < {self.config.rsi_buy})")
        
        # Price action
        reasons.append("Price below moving average threshold (pullback opportunity)")
        
        # Volume confirmation
        if analysis.get('volume', 0) > 0:
            reasons.append("Volume confirmation present")
        
        return "; ".join(reasons)
    
    def _generate_hedge_entry_reason(self, analysis: Dict, pair_id: str) -> str:
        """Generate detailed reason for hedge entry"""
        return f"Risk management hedge activated for pair {pair_id} due to -5% loss threshold breach. Short position to offset long exposure and limit downside risk."
    
    def _assess_market_conditions(self, symbol: str, analysis: Dict) -> str:
        """Assess current market conditions"""
        conditions = []
        
        ewo = analysis.get('ewo', 0)
        rsi = analysis.get('rsi', 50)
        
        # Trend assessment
        if ewo > 0:
            conditions.append("Bullish momentum")
        else:
            conditions.append("Bearish momentum")
        
        # Oversold/overbought
        if rsi < 30:
            conditions.append("Oversold conditions")
        elif rsi > 70:
            conditions.append("Overbought conditions")
        else:
            conditions.append("Neutral RSI")
        
        # Volatility assessment
        conditions.append("Active trading session")
        
        return "; ".join(conditions)
    
    def get_hedge_pair_by_symbol(self, symbol: str) -> Optional[HedgePair]:
        """Get hedge pair by symbol"""
        for pair in self.hedge_pairs:
            if pair.symbol == symbol:
                return pair
        return None
    
    def check_hedge_triggers(self):
        """Check if any long positions need hedging when loss >= -5%"""
        for hedge_pair in self.hedge_pairs:
            if hedge_pair.status == 'long_only' and hedge_pair.long_trade:
                # Calculate current P&L percentage of long position
                current_price = self._get_current_price(hedge_pair.symbol)
                if current_price:
                    # Calculate loss percentage (negative value indicates loss)
                    loss_pct = (current_price - hedge_pair.long_trade.price) / hedge_pair.long_trade.price
                    
                    # Trigger hedge when loss is >= -5% (i.e., loss_pct <= -0.05)
                    hedge_trigger_threshold = -0.05  # -5%
                    if loss_pct <= hedge_trigger_threshold:
                        logger.info(f"🚨 HEDGE TRIGGER ACTIVATED for {hedge_pair.symbol}:")
                        logger.info(f"   • Current loss: {loss_pct:.2%}")
                        logger.info(f"   • Trigger threshold: {hedge_trigger_threshold:.1%}")
                        logger.info(f"   • Entry price: ${hedge_pair.long_trade.price:.4f}")
                        logger.info(f"   • Current price: ${current_price:.4f}")
                        self._execute_hedge(hedge_pair, current_price)
                    else:
                        # Log current status for monitoring
                        if loss_pct < 0:  # Only log when in loss
                            logger.debug(f"Monitoring {hedge_pair.symbol}: {loss_pct:.2%} loss (hedge at {hedge_trigger_threshold:.1%})")
    
    def _execute_hedge(self, hedge_pair: HedgePair, current_price: float):
        """Execute hedge (short) position"""
        try:
            logger.info(f"🛡️ EXECUTING HEDGE for {hedge_pair.symbol}:")
            logger.info(f"   • Hedge size: ${hedge_pair.short_size}")
            logger.info(f"   • Current price: ${current_price:.4f}")
            
            analysis = {'price': current_price, 'ewo': 0, 'rsi': 50}  # Dummy analysis for hedge
            
            short_trade = self._execute_position(
                symbol=hedge_pair.symbol,
                side='sell',
                size=hedge_pair.short_size,
                analysis=analysis,
                trade_type='hedge',
                pair_id=hedge_pair.pair_id
            )
            
            if short_trade:
                hedge_pair.short_trade = short_trade
                hedge_pair.status = 'hedged'
                logger.info(f"✅ HEDGE EXECUTED for {hedge_pair.symbol}: Short ${hedge_pair.short_size}")
                
                # Send Telegram notification for hedge execution
                if self.telegram_enabled:
                    try:
                        hedge_dict = asdict(short_trade)
                        hedge_dict['timestamp'] = short_trade.timestamp.timestamp()
                        hedge_dict['hedge_reason'] = f"Hedge triggered at {current_price:.4f} due to -5% loss protection"
                        self._run_async_telegram_task(send_trade_entry_notification(hedge_dict))
                    except Exception as e:
                        logger.error(f"Error sending Telegram hedge notification: {e}")
            else:
                logger.error(f"❌ HEDGE FAILED for {hedge_pair.symbol}")
        
        except Exception as e:
            logger.error(f"Error executing hedge for {hedge_pair.symbol}: {e}")
    
    def check_hedge_exits(self):
        """Check if hedged positions should be closed when loss is covered by 1% profit"""
        for hedge_pair in self.hedge_pairs:
            if hedge_pair.status == 'hedged' and hedge_pair.long_trade and hedge_pair.short_trade:
                current_price = self._get_current_price(hedge_pair.symbol)
                if current_price:
                    # Calculate P&L for both positions
                    long_pnl = (current_price - hedge_pair.long_trade.price) * hedge_pair.long_trade.amount
                    short_pnl = (hedge_pair.short_trade.price - current_price) * hedge_pair.short_trade.amount
                    total_pnl = long_pnl + short_pnl
                    
                    # Calculate total investment (total capital used)
                    total_invested = (hedge_pair.long_trade.price * hedge_pair.long_trade.amount + 
                                    hedge_pair.short_trade.price * hedge_pair.short_trade.amount)
                    
                    # Calculate ROI percentage
                    total_roi_pct = total_pnl / total_invested if total_invested > 0 else 0
                    
                    # Exit condition: 1% profit (ROI >= 1%)
                    exit_threshold = 0.01  # 1% profit
                    if total_roi_pct >= exit_threshold:
                        logger.info(f"🎯 HEDGE EXIT TRIGGERED for {hedge_pair.symbol}:")
                        logger.info(f"   • Total ROI: {total_roi_pct:.2%} >= {exit_threshold:.1%}")
                        logger.info(f"   • Long P&L: ${long_pnl:.2f}")
                        logger.info(f"   • Short P&L: ${short_pnl:.2f}")
                        logger.info(f"   • Total P&L: ${total_pnl:.2f}")
                        logger.info(f"   • Loss covered with 1% profit achieved!")
                        self._close_hedge_pair(hedge_pair, current_price, total_roi_pct)
                    else:
                        # Log current hedge status for monitoring
                        logger.debug(f"Hedge monitoring {hedge_pair.symbol}: ROI {total_roi_pct:.2%} (exit at {exit_threshold:.1%})")
    
    def _close_hedge_pair(self, hedge_pair: HedgePair, current_price: float, total_roi_pct: float):
        """Close both positions in a hedge pair when 1% profit is achieved"""
        try:
            # Calculate final P&L for exit reasons
            long_pnl = (current_price - hedge_pair.long_trade.price) * hedge_pair.long_trade.amount if hedge_pair.long_trade else 0
            short_pnl = (hedge_pair.short_trade.price - current_price) * hedge_pair.short_trade.amount if hedge_pair.short_trade else 0
            total_pnl = long_pnl + short_pnl
            
            # Generate detailed exit reasons
            exit_reason = f"Hedge pair closed: 1% profit achieved ({total_roi_pct:.2%}). Loss covered by hedge strategy. Long P&L: ${long_pnl:.2f}, Short P&L: ${short_pnl:.2f}, Total: ${total_pnl:.2f}"
            
            logger.info(f"🏁 CLOSING HEDGE PAIR for {hedge_pair.symbol}:")
            logger.info(f"   • Reason: {exit_reason}")
            
            # Close long position
            if hedge_pair.long_trade and hedge_pair.long_trade.status == 'open':
                try:
                    close_order = self.exchange.create_market_order(
                        hedge_pair.symbol, 'sell', hedge_pair.long_trade.amount,
                        params={'reduceOnly': True}
                    )
                    logger.info(f"✅ Closed long position: {close_order['id']}")
                    
                    hedge_pair.long_trade.status = 'closed'
                    hedge_pair.long_trade.exit_price = current_price
                    hedge_pair.long_trade.exit_timestamp = datetime.now()
                    hedge_pair.long_trade.exit_reason = f"Hedge pair closure: Long position closed at ${current_price:.2f}. Loss covered by hedge with 1% profit."
                    hedge_pair.long_trade.pnl = long_pnl
                    hedge_pair.long_trade.pnl_percentage = (long_pnl / (hedge_pair.long_trade.price * hedge_pair.long_trade.amount)) * 100
                except Exception as e:
                    logger.error(f"Failed to close long position for {hedge_pair.symbol}: {e}")
            
            # Close short position
            if hedge_pair.short_trade and hedge_pair.short_trade.status == 'open':
                try:
                    close_order = self.exchange.create_market_order(
                        hedge_pair.symbol, 'buy', hedge_pair.short_trade.amount,
                        params={'reduceOnly': True}
                    )
                    logger.info(f"✅ Closed short position: {close_order['id']}")
                    
                    hedge_pair.short_trade.status = 'closed'
                    hedge_pair.short_trade.exit_price = current_price
                    hedge_pair.short_trade.exit_timestamp = datetime.now()
                    hedge_pair.short_trade.exit_reason = f"Hedge pair closure: Short hedge closed at ${current_price:.2f}. 1% profit target achieved."
                    hedge_pair.short_trade.pnl = short_pnl
                    hedge_pair.short_trade.pnl_percentage = (short_pnl / (hedge_pair.short_trade.price * hedge_pair.short_trade.amount)) * 100
                except Exception as e:
                    logger.error(f"Failed to close short position for {hedge_pair.symbol}: {e}")
            
            hedge_pair.status = 'closed'
            logger.info(f"🎉 HEDGE PAIR CLOSED for {hedge_pair.symbol} with 1% profit!")
            
            # Send Telegram notifications for hedge completion
            if self.telegram_enabled:
                try:
                    # Send hedge completion notification
                    hedge_summary = {
                        'symbol': hedge_pair.symbol,
                        'total_pnl': total_pnl,
                        'roi_percentage': total_roi_pct * 100,
                        'long_pnl': long_pnl,
                        'short_pnl': short_pnl,
                        'exit_reason': exit_reason
                    }
                    self._run_async_telegram_task(send_hedge_completion_notification(hedge_summary))
                    
                    # Send individual exit notifications
                    if hedge_pair.long_trade:
                        long_dict = asdict(hedge_pair.long_trade)
                        long_dict['timestamp'] = hedge_pair.long_trade.timestamp.timestamp()
                        if hedge_pair.long_trade.exit_timestamp:
                            long_dict['exit_timestamp'] = hedge_pair.long_trade.exit_timestamp.timestamp()
                        self._run_async_telegram_task(send_trade_exit_notification(long_dict))
                    
                    if hedge_pair.short_trade:
                        short_dict = asdict(hedge_pair.short_trade)
                        short_dict['timestamp'] = hedge_pair.short_trade.timestamp.timestamp()
                        if hedge_pair.short_trade.exit_timestamp:
                            short_dict['exit_timestamp'] = hedge_pair.short_trade.exit_timestamp.timestamp()
                        self._run_async_telegram_task(send_trade_exit_notification(short_dict))
                        
                except Exception as e:
                    logger.error(f"Error sending Telegram notifications: {e}")
            
        except Exception as e:
            logger.error(f"Error closing hedge pair for {hedge_pair.symbol}: {e}")
    
    def _close_hedge_pair(self, hedge_pair: HedgePair, current_price: float, total_roi_pct: float):
        """Close both positions in a hedge pair with detailed exit reasons"""
        try:
            # Calculate final P&L for exit reasons
            long_pnl = (current_price - hedge_pair.long_trade.price) * hedge_pair.long_trade.amount if hedge_pair.long_trade else 0
            short_pnl = (hedge_pair.short_trade.price - current_price) * hedge_pair.short_trade.amount if hedge_pair.short_trade else 0
            total_pnl = long_pnl + short_pnl
            
            # Generate detailed exit reasons
            exit_reason = f"Hedge pair closed: Total ROI {total_roi_pct:.2%} exceeded -5% threshold. Long P&L: ${long_pnl:.2f}, Short P&L: ${short_pnl:.2f}, Total: ${total_pnl:.2f}"
            
            # Close long position
            if hedge_pair.long_trade and hedge_pair.long_trade.status == 'open':
                try:
                    close_order = self.exchange.create_market_order(
                        hedge_pair.symbol, 'sell', hedge_pair.long_trade.amount,
                        params={'reduceOnly': True}
                    )
                    logger.info(f"Closed long position: {close_order['id']}")
                    
                    hedge_pair.long_trade.status = 'closed'
                    hedge_pair.long_trade.exit_price = current_price
                    hedge_pair.long_trade.exit_timestamp = datetime.now()
                    hedge_pair.long_trade.exit_reason = f"Hedge pair closure: Long position closed at ${current_price:.2f}. Total ROI {total_roi_pct:.2%}"
                    hedge_pair.long_trade.pnl = long_pnl
                    hedge_pair.long_trade.pnl_percentage = (long_pnl / (hedge_pair.long_trade.price * hedge_pair.long_trade.amount)) * 100
                except Exception as e:
                    logger.error(f"Failed to close long position for {hedge_pair.symbol}: {e}")
            
            # Close short position
            if hedge_pair.short_trade and hedge_pair.short_trade.status == 'open':
                try:
                    close_order = self.exchange.create_market_order(
                        hedge_pair.symbol, 'buy', hedge_pair.short_trade.amount,
                        params={'reduceOnly': True}
                    )
                    logger.info(f"Closed short position: {close_order['id']}")
                    
                    hedge_pair.short_trade.status = 'closed'
                    hedge_pair.short_trade.exit_price = current_price
                    hedge_pair.short_trade.exit_timestamp = datetime.now()
                    hedge_pair.short_trade.exit_reason = f"Hedge pair closure: Short hedge closed at ${current_price:.2f}. Total ROI {total_roi_pct:.2%}"
                    hedge_pair.short_trade.pnl = short_pnl
                    hedge_pair.short_trade.pnl_percentage = (short_pnl / (hedge_pair.short_trade.price * hedge_pair.short_trade.amount)) * 100
                except Exception as e:
                    logger.error(f"Failed to close short position for {hedge_pair.symbol}: {e}")
            
            hedge_pair.status = 'closed'
            logger.info(f"Closed hedge pair for {hedge_pair.symbol}")
            logger.info(f"Exit reason: {exit_reason}")
            
            # Send Telegram notifications for trade exits and hedge completion
            if self.telegram_enabled:
                try:
                    # Send hedge completion notification
                    hedge_summary = {
                        'symbol': hedge_pair.symbol,
                        'total_pnl': total_pnl,
                        'roi_percentage': total_roi_pct * 100,
                        'long_pnl': long_pnl,
                        'short_pnl': short_pnl,
                        'exit_reason': exit_reason
                    }
                    self._run_async_telegram_task(send_hedge_completion_notification(hedge_summary))
                    
                    # Send individual exit notifications
                    if hedge_pair.long_trade:
                        long_dict = asdict(hedge_pair.long_trade)
                        long_dict['timestamp'] = hedge_pair.long_trade.timestamp.timestamp()
                        if hedge_pair.long_trade.exit_timestamp:
                            long_dict['exit_timestamp'] = hedge_pair.long_trade.exit_timestamp.timestamp()
                        self._run_async_telegram_task(send_trade_exit_notification(long_dict))
                    
                    if hedge_pair.short_trade:
                        short_dict = asdict(hedge_pair.short_trade)
                        short_dict['timestamp'] = hedge_pair.short_trade.timestamp.timestamp()
                        if hedge_pair.short_trade.exit_timestamp:
                            short_dict['exit_timestamp'] = hedge_pair.short_trade.exit_timestamp.timestamp()
                        self._run_async_telegram_task(send_trade_exit_notification(short_dict))
                        
                except Exception as e:
                    logger.error(f"Error sending Telegram notifications: {e}")
            
        except Exception as e:
            logger.error(f"Error closing hedge pair for {hedge_pair.symbol}: {e}")

    def check_stop_loss(self):
        """Check and execute stop loss for open positions"""
        open_trades = [t for t in self.trades if t.status == 'open']
        
        for trade in open_trades:
            try:
                current_data = self.analyze_symbol(trade.symbol)
                current_price = current_data['price']
                
                # Calculate current loss percentage
                if trade.side == 'buy':
                    loss_pct = (current_price - trade.price) / trade.price
                else:  # sell/short
                    loss_pct = (trade.price - current_price) / trade.price
                
                # Check if stop loss should trigger
                if loss_pct <= self.config.stoploss:
                    logger.info(f"Stop loss triggered for {trade.symbol}: {loss_pct:.2%} <= {self.config.stoploss:.2%}")
                    
                    # Execute actual closing order on exchange
                    try:
                        if trade.side == 'buy':
                            close_order = self.exchange.create_market_order(
                                trade.symbol, 'sell', trade.amount,
                                params={'reduceOnly': True}
                            )
                        else:
                            close_order = self.exchange.create_market_order(
                                trade.symbol, 'buy', trade.amount,
                                params={'reduceOnly': True}
                            )
                        
                        logger.info(f"Stop loss order executed: {close_order['id']}")
                        
                        # Update trade status
                        trade.status = 'closed'
                        trade.exit_price = current_price
                        trade.exit_timestamp = datetime.now()
                        trade.exit_signal = f"Stop Loss ({loss_pct:.1%})"
                        
                        price_diff = trade.exit_price - trade.price if trade.side == 'buy' else trade.price - trade.exit_price
                        trade.pnl = price_diff * trade.amount
                        trade.pnl_percentage = (price_diff / trade.price) * 100 * self.get_trade_leverage(trade)
                        
                        logger.info(f"Stop loss completed: {trade.symbol} P&L: ${trade.pnl:.2f}")
                        
                    except Exception as order_error:
                        logger.error(f"Failed to execute stop loss order for {trade.symbol}: {order_error}")
                    
            except Exception as e:
                logger.error(f"Error checking stop loss for {trade.symbol}: {e}")

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def check_stop_loss(self):
        """Check and execute stop loss for open non-hedge positions"""
        # Only check stop loss for trades that are not part of hedge pairs
        open_trades = [t for t in self.trades if t.status == 'open' and t.trade_type == 'normal']
        
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
    
    def check_roi_exit(self):
        """Check and execute ROI exits for open positions"""
        # Check ROI for all open trades
        open_trades = [t for t in self.trades if t.status == 'open']
        
        for trade in open_trades:
            try:
                current_data = self.analyze_symbol(trade.symbol)
                current_price = current_data['price']
                
                # Calculate current profit percentage
                if trade.side == 'buy':
                    profit_pct = (current_price - trade.price) / trade.price
                else:  # sell/short
                    profit_pct = (trade.price - current_price) / trade.price
                
                # Calculate time since entry (in minutes)
                time_diff = (datetime.now() - trade.timestamp).total_seconds() / 60
                
                # Check ROI table
                roi_threshold = self._get_roi_threshold(time_diff)
                
                if profit_pct >= roi_threshold:
                    logger.info(f"ROI exit triggered for {trade.symbol}: {profit_pct:.1%} >= {roi_threshold:.1%}")
                    
                    # Execute actual closing order on exchange
                    try:
                        if trade.side == 'buy':
                            # Close long position with market sell
                            close_order = self.exchange.create_market_order(
                                trade.symbol, 'sell', trade.amount,
                                params={'reduceOnly': True}
                            )
                        else:
                            # Close short position with market buy
                            close_order = self.exchange.create_market_order(
                                trade.symbol, 'buy', trade.amount,
                                params={'reduceOnly': True}
                            )
                        
                        logger.info(f"ROI exit order executed: {close_order['id']}")
                        
                        # Update trade status
                        trade.status = 'closed'
                        trade.exit_price = current_price
                        trade.exit_timestamp = datetime.now()
                        trade.exit_signal = f"ROI ({profit_pct:.1%} >= {roi_threshold:.1%})"
                        
                        price_diff = trade.exit_price - trade.price if trade.side == 'buy' else trade.price - trade.exit_price
                        trade.pnl = price_diff * trade.amount
                        trade.pnl_percentage = (price_diff / trade.price) * 100 * self.get_trade_leverage(trade)
                        
                        logger.info(f"ROI exit completed: {trade.symbol} P&L: ${trade.pnl:.2f}")
                        
                        # Send Telegram notification
                        if self.telegram_enabled:
                            try:
                                trade_dict = asdict(trade)
                                trade_dict['timestamp'] = trade.timestamp.timestamp()
                                trade_dict['exit_timestamp'] = trade.exit_timestamp.timestamp()
                                self._run_async_telegram_task(send_trade_exit_notification(trade_dict))
                            except Exception as e:
                                logger.error(f"Error sending ROI exit notification: {e}")
                        
                    except Exception as order_error:
                        logger.error(f"Failed to execute ROI exit order for {trade.symbol}: {order_error}")
                    
            except Exception as e:
                logger.error(f"Error checking ROI for {trade.symbol}: {e}")
                    
            except Exception as e:
                logger.error(f"Error checking ROI for {trade.symbol}: {e}")
    
    def _get_roi_threshold(self, time_minutes: float) -> float:
        """Get ROI threshold for given time"""
        # Convert ROI table keys to integers and sort
        roi_times = sorted([int(k) for k in self.config.minimal_roi.keys()])
        
        # Find the appropriate ROI threshold
        for roi_time in roi_times:
            if time_minutes >= roi_time:
                roi_threshold = self.config.minimal_roi[str(roi_time)]
            else:
                break
        else:
            # If we've exceeded all time thresholds, use the last one
            roi_threshold = self.config.minimal_roi[str(roi_times[-1])]
        
        return roi_threshold
    
    def check_trailing_stop(self):
        """Check and execute trailing stop for open positions"""
        if not self.config.trailing_stop:
            return
            
        # Check trailing stop for all open trades
        open_trades = [t for t in self.trades if t.status == 'open']
        
        for trade in open_trades:
            try:
                current_data = self.analyze_symbol(trade.symbol)
                current_price = current_data['price']
                
                # Only apply trailing stop to long positions
                if trade.side != 'buy':
                    continue
                
                # Initialize max_price if not set
                if trade.max_price is None:
                    trade.max_price = max(trade.price, current_price)
                
                # Update max_price if current price is higher
                if current_price > trade.max_price:
                    trade.max_price = current_price
                    
                    # Calculate new trailing stop price
                    if trade.max_price > trade.price * (1 + self.config.trailing_stop_positive_offset):
                        # Only activate trailing stop when profit exceeds offset
                        trade.trailing_stop_price = trade.max_price * (1 - self.config.trailing_stop_positive)
                        logger.debug(f"Updated trailing stop for {trade.symbol}: ${trade.trailing_stop_price:.4f}")
                
                # Check if trailing stop should trigger
                if trade.trailing_stop_price and current_price <= trade.trailing_stop_price:
                    logger.info(f"Trailing stop triggered for {trade.symbol}: ${current_price:.4f} <= ${trade.trailing_stop_price:.4f}")
                    
                    # Execute actual closing order on exchange
                    try:
                        close_order = self.exchange.create_market_order(
                            trade.symbol, 'sell', trade.amount,
                            params={'reduceOnly': True}
                        )
                        
                        logger.info(f"Trailing stop order executed: {close_order['id']}")
                        
                        # Update trade status
                        trade.status = 'closed'
                        trade.exit_price = current_price
                        trade.exit_timestamp = datetime.now()
                        trade.exit_signal = f"Trailing Stop (Max: ${trade.max_price:.2f})"
                        
                        price_diff = trade.exit_price - trade.price
                        trade.pnl = price_diff * trade.amount
                        trade.pnl_percentage = (price_diff / trade.price) * 100 * self.get_trade_leverage(trade)
                        
                        logger.info(f"Trailing stop completed: {trade.symbol} P&L: ${trade.pnl:.2f}")
                        
                        # Send Telegram notification
                        if self.telegram_enabled:
                            try:
                                trade_dict = asdict(trade)
                                trade_dict['timestamp'] = trade.timestamp.timestamp()
                                trade_dict['exit_timestamp'] = trade.exit_timestamp.timestamp()
                                self._run_async_telegram_task(send_trade_exit_notification(trade_dict))
                            except Exception as e:
                                logger.error(f"Error sending trailing stop exit notification: {e}")
                        
                    except Exception as order_error:
                        logger.error(f"Failed to execute trailing stop order for {trade.symbol}: {order_error}")
                    
            except Exception as e:
                logger.error(f"Error checking trailing stop for {trade.symbol}: {e}")
                    
            except Exception as e:
                logger.error(f"Error checking trailing stop for {trade.symbol}: {e}")
    
    def run_strategy(self):
        """Main strategy execution loop with hedging"""
        symbol_batch_size = 10  # Process symbols in batches to avoid overwhelming
        symbol_rotation = 0
        
        while self.is_running:
            try:
                logger.info("Running strategy analysis...")
                
                # Check hedge triggers and exits first
                self.check_hedge_triggers()
                self.check_hedge_exits()
                
                # Check ROI exits for profitable trades
                self.check_roi_exit()
                
                # Check trailing stops if enabled
                self.check_trailing_stop()
                
                # Check stop losses for any remaining non-hedge trades
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
                
                # Log hedge pair status
                active_pairs = [hp for hp in self.hedge_pairs if hp.status != 'closed']
                if active_pairs:
                    logger.info(f"Active hedge pairs: {len(active_pairs)}")
                    for pair in active_pairs:
                        logger.info(f"  {pair.symbol}: {pair.status}")
                
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
        
        # Send Telegram bot ready notification with symbol information
        if self.telegram_enabled and TELEGRAM_ENHANCED_AVAILABLE:
            try:
                self._run_async_telegram_task(send_bot_ready_notification(len(self.config.symbols), self.config.symbols))
                logger.info("Telegram bot ready notification sent")
            except Exception as e:
                logger.error(f"Error sending Telegram bot ready notification: {e}")
        elif self.telegram_enabled:
            # Fallback to basic status notification
            try:
                open_trades = len([t for t in self.trades if t.status == 'open'])
                total_pnl = sum(t.pnl for t in self.trades if t.pnl and t.status == 'closed')
                self._run_async_telegram_task(send_bot_status_notification("running", self.balance, open_trades, total_pnl))
            except Exception as e:
                logger.error(f"Error sending Telegram start notification: {e}")
        
        # Run strategy in separate thread
        strategy_thread = threading.Thread(target=self.run_strategy)
        strategy_thread.daemon = True
        strategy_thread.start()
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        logger.info("Stopping trading bot...")
        
        # Send enhanced Telegram stop notification with final statistics
        if self.telegram_enabled and TELEGRAM_ENHANCED_AVAILABLE:
            try:
                # Prepare final statistics
                open_trades = [t for t in self.trades if t.status == 'open']
                closed_trades = [t for t in self.trades if t.status == 'closed']
                total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
                total_return = (total_pnl / self.config.initial_balance) * 100 if total_pnl else 0
                
                final_stats = {
                    'total_trades': len(self.trades),
                    'open_trades': len(open_trades),
                    'closed_trades': len(closed_trades),
                    'total_pnl': total_pnl,
                    'total_return_pct': total_return
                }
                
                self._run_async_telegram_task(send_bot_stopped_notification(final_stats))
                logger.info("Telegram bot stopped notification sent")
            except Exception as e:
                logger.error(f"Error sending Telegram stop notification: {e}")
        elif self.telegram_enabled:
            # Fallback to basic status notification
            try:
                open_trades = len([t for t in self.trades if t.status == 'open'])
                total_pnl = sum(t.pnl for t in self.trades if t.pnl and t.status == 'closed')
                self._run_async_telegram_task(send_bot_status_notification("stopped", self.balance, open_trades, total_pnl))
            except Exception as e:
                logger.error(f"Error sending Telegram stop notification: {e}")
    
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
    
    def get_position_leverage(self, symbol: str) -> Optional[float]:
        """Get the actual leverage setting for a symbol from the exchange"""
        try:
            positions = self.exchange.fetch_positions([symbol])
            for position in positions:
                if position['symbol'] == symbol and float(position.get('contracts', 0)) != 0:
                    leverage = position.get('leverage', None)
                    if leverage:
                        return float(leverage)
            
            # If no active position, get leverage from account info or symbol info
            try:
                # Try to get leverage from symbol info
                markets = self.exchange.load_markets()
                if symbol in markets:
                    market_info = markets[symbol]
                    # Some exchanges store leverage info in market info
                    if 'leverage' in market_info.get('info', {}):
                        return float(market_info['info']['leverage'])
                        
                # Fallback: get leverage settings from account info
                symbol_raw = symbol.replace('/', '')  # Remove slash for Binance API
                leverage_info = self.exchange.fapiPrivate_get_leveragebracket({'symbol': symbol_raw})
                if leverage_info and len(leverage_info) > 0:
                    initial_leverage = leverage_info[0].get('initialLeverage', None)
                    if initial_leverage:
                        return float(initial_leverage)
                        
            except Exception as fallback_error:
                logger.debug(f"Fallback leverage lookup failed for {symbol}: {fallback_error}")
                
            # Final fallback: return configured leverage
            return float(self.config.leverage)
            
        except Exception as e:
            logger.error(f"Error getting leverage for {symbol}: {e}")
            return float(self.config.leverage)  # Fallback to config value

    def get_trade_leverage(self, trade: Trade) -> float:
        """Get the actual leverage used for a specific trade"""
        try:
            # First try to get from active position
            leverage = self.get_position_leverage(trade.symbol)
            if leverage:
                return leverage
                
            # If trade is closed or no position, return configured leverage as fallback
            return float(self.config.leverage)
            
        except Exception as e:
            logger.error(f"Error getting leverage for trade {trade.id}: {e}")
            return float(self.config.leverage)
