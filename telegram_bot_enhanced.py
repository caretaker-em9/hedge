#!/usr/bin/env python3

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import config
from telegram import Bot
from telegram.error import TelegramError
from telegram.constants import ParseMode

class TelegramBotNotifier:
    """
    Enhanced Telegram Bot for trading notifications using python-telegram-bot library
    Includes startup messages and bot status monitoring
    """
    
    def __init__(self):
        self.bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', '')
        self.chat_id = getattr(config, 'TELEGRAM_CHAT_ID', '')
        self.enabled = getattr(config, 'TELEGRAM_ENABLED', False)
        
        # Notification preferences
        self.send_entry_signals = getattr(config, 'TELEGRAM_SEND_ENTRY_SIGNALS', True)
        self.send_exit_signals = getattr(config, 'TELEGRAM_SEND_EXIT_SIGNALS', True)
        self.send_profits = getattr(config, 'TELEGRAM_SEND_PROFITS', True)
        self.send_errors = getattr(config, 'TELEGRAM_SEND_ERRORS', True)
        self.send_status_updates = getattr(config, 'TELEGRAM_SEND_STATUS_UPDATES', True)
        
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.is_bot_running = False
        self.last_message_time = None
        
        # Initialize bot if enabled
        if self.is_enabled():
            self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize the Telegram bot"""
        try:
            self.bot = Bot(token=self.bot_token)
            self.logger.info("Telegram bot initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram bot: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Telegram notifications are enabled and configured"""
        return self.enabled and self.bot_token and self.chat_id
    
    async def send_message(self, message: str, parse_mode: str = ParseMode.HTML) -> bool:
        """
        Send a message to Telegram using python-telegram-bot
        
        Args:
            message: Message text to send
            parse_mode: Telegram parse mode (HTML, Markdown, or None)
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.is_enabled() or not self.bot:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            self.last_message_time = datetime.now()
            self.logger.debug("Telegram message sent successfully")
            return True
            
        except TelegramError as e:
            self.logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_startup_message(self, trading_config: Dict[str, Any]) -> bool:
        """Send a comprehensive startup message when the trading bot starts"""
        
        startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""
🚀 <b>TRADING BOT STARTUP</b>

⏰ <b>Started:</b> {startup_time}
🤖 <b>Status:</b> INITIALIZING
💰 <b>Initial Balance:</b> ${trading_config.get('initial_balance', 0):.2f}
📊 <b>Max Trades:</b> {trading_config.get('max_trades', 0)}
⚡ <b>Leverage:</b> {trading_config.get('leverage', 1)}x
📈 <b>Timeframe:</b> {trading_config.get('timeframe', '5m')}

🎯 <b>Hedging Strategy Config:</b>
• Long Position: ${trading_config.get('long_position_size', 0):.1f}
• Short Position: ${trading_config.get('short_position_size', 0):.1f}
• Hedge Trigger: {trading_config.get('hedge_trigger_loss', -0.05)*100:.1f}%
• One Trade Per Pair: {'✅' if trading_config.get('one_trade_per_pair', False) else '❌'}

🎮 <b>Active Features:</b>
• Entry Signals: {'✅' if self.send_entry_signals else '❌'}
• Exit Signals: {'✅' if self.send_exit_signals else '❌'}
• Profit Updates: {'✅' if self.send_profits else '❌'}
• Error Alerts: {'✅' if self.send_errors else '❌'}
• Status Updates: {'✅' if self.send_status_updates else '❌'}

📡 <b>Telegram Bot:</b> CONNECTED
🌐 <b>Web Interface:</b> http://localhost:5000

<i>Bot initialization in progress...</i>
I'll notify you when trading starts! 📈
"""
        
        success = await self.send_message(message.strip())
        if success:
            self.is_bot_running = True
            self.logger.info("Startup message sent to Telegram")
        return success
    
    async def send_bot_ready_message(self, symbols_count: int, symbols_list: list) -> bool:
        """Send message when bot is fully initialized and ready to trade"""
        
        ready_time = datetime.now().strftime('%H:%M:%S')
        
        # Show first 10 symbols
        symbols_preview = ', '.join(symbols_list[:10])
        if len(symbols_list) > 10:
            symbols_preview += f' (+{len(symbols_list)-10} more)'
        
        message = f"""
✅ <b>TRADING BOT READY</b>

🕐 <b>Ready at:</b> {ready_time}
🎯 <b>Symbols loaded:</b> {symbols_count}
📊 <b>Trading:</b> {symbols_preview}

🟢 <b>Status:</b> ACTIVE & MONITORING
🔍 <b>Strategy:</b> ElliotV5_SMA Hedging

<i>Bot is now actively scanning for trading opportunities...</i>
📈 <b>Good luck trading!</b> 🚀
"""
        
        return await self.send_message(message.strip())
    
    async def send_bot_stopped_message(self, final_stats: Dict[str, Any]) -> bool:
        """Send message when bot is stopped with final statistics"""
        
        stop_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate session duration if we have startup time
        session_duration = "Unknown"
        if self.last_message_time:
            duration = datetime.now() - self.last_message_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            session_duration = f"{hours}h {minutes}m"
        
        total_pnl = final_stats.get('total_pnl', 0)
        pnl_emoji = "📈" if total_pnl > 0 else "📉" if total_pnl < 0 else "⚖️"
        
        message = f"""
🛑 <b>TRADING BOT STOPPED</b>

⏰ <b>Stopped:</b> {stop_time}
⏱️ <b>Session Duration:</b> {session_duration}

📊 <b>Final Statistics:</b>
• Total Trades: {final_stats.get('total_trades', 0)}
• Open Trades: {final_stats.get('open_trades', 0)}
• Closed Trades: {final_stats.get('closed_trades', 0)}
{pnl_emoji} Total P&L: ${total_pnl:.2f}
📈 Return: {final_stats.get('total_return_pct', 0):.2f}%

🔴 <b>Status:</b> OFFLINE

<i>Bot has been safely stopped. All positions logged.</i>
Thank you for using the hedging strategy! 💼
"""
        
        success = await self.send_message(message.strip())
        if success:
            self.is_bot_running = False
        return success
    
    async def send_health_check(self) -> bool:
        """Send a health check message to verify bot connectivity"""
        
        message = f"""
💓 <b>HEALTH CHECK</b>

🤖 <b>Bot Status:</b> {'🟢 RUNNING' if self.is_bot_running else '🔴 STOPPED'}
📡 <b>Connection:</b> ACTIVE
🕐 <b>Check Time:</b> {datetime.now().strftime('%H:%M:%S')}

✅ <i>Telegram notifications are working correctly!</i>
"""
        
        return await self.send_message(message.strip())
    
    async def send_error_with_context(self, error: str, context: str = "", severity: str = "ERROR") -> bool:
        """Send enhanced error message with context and severity"""
        
        severity_emoji = {
            "ERROR": "🚨",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "CRITICAL": "💥"
        }.get(severity, "🚨")
        
        message = f"""
{severity_emoji} <b>{severity}</b>

❌ <b>Error:</b> {error}
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if context:
            message += f"📍 <b>Context:</b> {context}\n"
        
        if severity == "CRITICAL":
            message += "\n🆘 <b>IMMEDIATE ATTENTION REQUIRED!</b>"
        
        return await self.send_message(message.strip())
    
    # Keep existing formatting methods but use new send_message
    def format_trade_entry(self, trade: Dict[str, Any]) -> str:
        """Format trade entry signal for Telegram"""
        
        # Determine if this is a long or hedge entry
        is_hedge = "hedge" in trade.get('entry_reason', '').lower()
        signal_type = "🔴 HEDGE ENTRY" if is_hedge else "🟢 LONG ENTRY"
        
        message = f"""
{signal_type} SIGNAL

🎯 <b>Symbol:</b> {trade['symbol']}
💰 <b>Side:</b> {trade['side'].upper()}
📊 <b>Amount:</b> {trade['amount']:.6f}
💵 <b>Entry Price:</b> ${trade['price']:.4f}
🕐 <b>Time:</b> {datetime.fromtimestamp(trade['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}

📈 <b>Entry Reason:</b>
{trade.get('entry_reason', 'N/A')}

🔍 <b>Technical Indicators:</b>
"""
        
        # Add technical indicators if available
        tech_indicators = trade.get('technical_indicators', {})
        if tech_indicators:
            if 'rsi' in tech_indicators:
                message += f"• RSI: {tech_indicators['rsi']:.1f}\n"
            if 'sma_fast' in tech_indicators:
                message += f"• SMA Fast: ${tech_indicators['sma_fast']:.4f}\n"
            if 'sma_slow' in tech_indicators:
                message += f"• SMA Slow: ${tech_indicators['sma_slow']:.4f}\n"
            if 'macd_signal' in tech_indicators:
                message += f"• MACD: {tech_indicators['macd_signal']}\n"
        else:
            message += "• No indicators available\n"
        
        # Add market conditions
        market_conditions = trade.get('market_conditions', {})
        if market_conditions:
            message += f"\n🌍 <b>Market Conditions:</b>\n"
            if 'trend' in market_conditions:
                message += f"• Trend: {market_conditions['trend']}\n"
            if 'volatility' in market_conditions:
                message += f"• Volatility: {market_conditions['volatility']}\n"
            if 'volume_profile' in market_conditions:
                message += f"• Volume: {market_conditions['volume_profile']}\n"
        
        return message.strip()
    
    async def send_trade_entry(self, trade: Dict[str, Any]) -> bool:
        """Send trade entry notification"""
        if not self.send_entry_signals:
            return False
        
        message = self.format_trade_entry(trade)
        return await self.send_message(message)
    
    async def test_connection_with_feedback(self) -> bool:
        """Test connection and provide detailed feedback"""
        
        if not self.is_enabled():
            self.logger.error("Telegram bot is not enabled or configured")
            return False
        
        try:
            # Test with a simple message
            test_message = f"""
🧪 <b>CONNECTION TEST</b>

✅ <b>Status:</b> SUCCESS
🤖 <b>Bot:</b> Connected
📡 <b>API:</b> Responsive
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Telegram integration is working perfectly!</i> 🎉
"""
            
            success = await self.send_message(test_message.strip())
            if success:
                self.logger.info("✅ Telegram connection test successful")
            else:
                self.logger.error("❌ Telegram connection test failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Telegram connection test error: {e}")
            return False

# Global instance
telegram_notifier = TelegramBotNotifier()

# Convenience functions for easy integration
async def send_startup_notification(trading_config: Dict[str, Any]) -> bool:
    """Send startup notification"""
    return await telegram_notifier.send_startup_message(trading_config)

async def send_bot_ready_notification(symbols_count: int, symbols_list: list) -> bool:
    """Send bot ready notification"""
    return await telegram_notifier.send_bot_ready_message(symbols_count, symbols_list)

async def send_bot_stopped_notification(final_stats: Dict[str, Any]) -> bool:
    """Send bot stopped notification"""
    return await telegram_notifier.send_bot_stopped_message(final_stats)

async def send_health_check_notification() -> bool:
    """Send health check notification"""
    return await telegram_notifier.send_health_check()

async def send_error_notification_enhanced(error: str, context: str = "", severity: str = "ERROR") -> bool:
    """Send enhanced error notification"""
    return await telegram_notifier.send_error_with_context(error, context, severity)

if __name__ == "__main__":
    """Test the enhanced Telegram bot functionality"""
    
    async def test_enhanced_telegram_bot():
        print("🧪 Testing Enhanced Telegram Bot...")
        print("=" * 50)
        
        if not telegram_notifier.is_enabled():
            print("❌ Telegram bot is not enabled or configured")
            print("Please check your config.py settings")
            return
        
        # Test connection
        print("📡 Testing connection...")
        if await telegram_notifier.test_connection_with_feedback():
            print("✅ Connection test passed!")
        else:
            print("❌ Connection test failed!")
            return
        
        # Test startup message
        print("🚀 Testing startup message...")
        test_config = {
            'initial_balance': 30.0,
            'max_trades': 2,
            'leverage': 10,
            'timeframe': '5m',
            'long_position_size': 5.0,
            'short_position_size': 10.0,
            'hedge_trigger_loss': -0.05,
            'one_trade_per_pair': True
        }
        
        if await telegram_notifier.send_startup_message(test_config):
            print("✅ Startup message sent!")
        
        await asyncio.sleep(2)
        
        # Test ready message
        print("✅ Testing ready message...")
        test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT']
        if await telegram_notifier.send_bot_ready_message(len(test_symbols), test_symbols):
            print("✅ Ready message sent!")
        
        await asyncio.sleep(2)
        
        # Test health check
        print("💓 Testing health check...")
        if await telegram_notifier.send_health_check():
            print("✅ Health check sent!")
        
        await asyncio.sleep(2)
        
        # Test enhanced error
        print("🚨 Testing enhanced error notification...")
        if await telegram_notifier.send_error_with_context("Test error", "Testing context", "WARNING"):
            print("✅ Enhanced error sent!")
        
        await asyncio.sleep(2)
        
        # Test stop message
        print("🛑 Testing stop message...")
        test_stats = {
            'total_trades': 5,
            'open_trades': 0,
            'closed_trades': 5,
            'total_pnl': 15.75,
            'total_return_pct': 52.5
        }
        
        if await telegram_notifier.send_bot_stopped_message(test_stats):
            print("✅ Stop message sent!")
        
        print("\n🎉 Enhanced Telegram bot testing completed!")
    
    # Run the test
    asyncio.run(test_enhanced_telegram_bot())
