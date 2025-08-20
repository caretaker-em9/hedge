#!/usr/bin/env python3

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import config

class TelegramBot:
    """
    Telegram Bot for sending trading notifications, signals, and alerts
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
        
        # Validate configuration
        if self.enabled and (not self.bot_token or not self.chat_id):
            self.logger.warning("Telegram bot is enabled but token or chat_id is missing")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Telegram notifications are enabled and configured"""
        return self.enabled and self.bot_token and self.chat_id
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram
        
        Args:
            message: Message text to send
            parse_mode: Telegram parse mode (HTML, Markdown, or None)
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.is_enabled():
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.debug("Telegram message sent successfully")
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(f"Failed to send Telegram message: {response.status} - {response_text}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
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
    
    def format_trade_exit(self, trade: Dict[str, Any]) -> str:
        """Format trade exit signal for Telegram"""
        
        # Determine profit/loss status
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_percentage', 0)
        
        if pnl > 0:
            status_emoji = "✅ PROFIT"
            pnl_emoji = "💰"
        elif pnl < 0:
            status_emoji = "❌ LOSS"
            pnl_emoji = "📉"
        else:
            status_emoji = "➖ BREAKEVEN"
            pnl_emoji = "⚖️"
        
        message = f"""
🚪 TRADE EXIT - {status_emoji}

🎯 <b>Symbol:</b> {trade['symbol']}
💰 <b>Side:</b> {trade['side'].upper()}
📊 <b>Amount:</b> {trade['amount']:.6f}
💵 <b>Entry Price:</b> ${trade['price']:.4f}
💸 <b>Exit Price:</b> ${trade.get('exit_price', 0):.4f}
🕐 <b>Exit Time:</b> {datetime.fromtimestamp(trade.get('exit_timestamp', trade['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')}

{pnl_emoji} <b>P&L:</b> ${pnl:.2f} ({pnl_pct:.2f}%)

📝 <b>Exit Reason:</b>
{trade.get('exit_reason', 'N/A')}
"""
        
        return message.strip()
    
    def format_hedge_completion(self, long_trade: Dict[str, Any], short_trade: Dict[str, Any], total_pnl: float) -> str:
        """Format hedge pair completion message"""
        
        if total_pnl > 0:
            status_emoji = "✅ SUCCESSFUL HEDGE"
            pnl_emoji = "🎉"
        else:
            status_emoji = "⚠️ HEDGE COMPLETED"
            pnl_emoji = "📊"
        
        message = f"""
{pnl_emoji} {status_emoji}

🎯 <b>Symbol:</b> {long_trade['symbol']}

📈 <b>Long Position:</b>
• Entry: ${long_trade['price']:.4f}
• Exit: ${long_trade.get('exit_price', 0):.4f}
• P&L: ${long_trade.get('pnl', 0):.2f}

📉 <b>Short Position:</b>
• Entry: ${short_trade['price']:.4f}
• Exit: ${short_trade.get('exit_price', 0):.4f}
• P&L: ${short_trade.get('pnl', 0):.2f}

💰 <b>Total P&L:</b> ${total_pnl:.2f}
📊 <b>Coverage Ratio:</b> {abs(short_trade.get('pnl', 0) / long_trade.get('pnl', -1)) if long_trade.get('pnl', 0) != 0 else 0:.2f}x

🕐 <b>Completed:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return message.strip()
    
    def format_error_message(self, error: str, context: str = "") -> str:
        """Format error message for Telegram"""
        
        message = f"""
🚨 <b>TRADING BOT ERROR</b>

❌ <b>Error:</b> {error}

🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if context:
            message += f"\n📍 <b>Context:</b> {context}"
        
        return message.strip()
    
    def format_bot_status(self, status: str, balance: float, open_trades: int, total_pnl: float) -> str:
        """Format bot status update message"""
        
        status_emoji = "🟢" if status == "running" else "🔴"
        
        message = f"""
{status_emoji} <b>BOT STATUS UPDATE</b>

🤖 <b>Status:</b> {status.upper()}
💰 <b>Balance:</b> ${balance:.2f}
📊 <b>Open Trades:</b> {open_trades}
📈 <b>Total P&L:</b> ${total_pnl:.2f}

🕐 <b>Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return message.strip()
    
    def format_daily_summary(self, trades_today: int, total_pnl: float, win_rate: float, best_trade: float, worst_trade: float) -> str:
        """Format daily trading summary"""
        
        message = f"""
📊 <b>DAILY TRADING SUMMARY</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}

📈 <b>Performance:</b>
• Trades: {trades_today}
• Total P&L: ${total_pnl:.2f}
• Win Rate: {win_rate:.1f}%
• Best Trade: ${best_trade:.2f}
• Worst Trade: ${worst_trade:.2f}

🕐 <b>Generated:</b> {datetime.now().strftime('%H:%M:%S')}
"""
        
        return message.strip()
    
    async def send_trade_entry(self, trade: Dict[str, Any]) -> bool:
        """Send trade entry notification"""
        if not self.send_entry_signals:
            return False
        
        message = self.format_trade_entry(trade)
        return await self.send_message(message)
    
    async def send_trade_exit(self, trade: Dict[str, Any]) -> bool:
        """Send trade exit notification"""
        if not self.send_exit_signals:
            return False
        
        message = self.format_trade_exit(trade)
        return await self.send_message(message)
    
    async def send_hedge_completion(self, long_trade: Dict[str, Any], short_trade: Dict[str, Any], total_pnl: float) -> bool:
        """Send hedge completion notification"""
        if not self.send_profits:
            return False
        
        message = self.format_hedge_completion(long_trade, short_trade, total_pnl)
        return await self.send_message(message)
    
    async def send_error(self, error: str, context: str = "") -> bool:
        """Send error notification"""
        if not self.send_errors:
            return False
        
        message = self.format_error_message(error, context)
        return await self.send_message(message)
    
    async def send_bot_status(self, status: str, balance: float, open_trades: int, total_pnl: float) -> bool:
        """Send bot status update"""
        if not self.send_status_updates:
            return False
        
        message = self.format_bot_status(status, balance, open_trades, total_pnl)
        return await self.send_message(message)
    
    async def send_daily_summary(self, trades_today: int, total_pnl: float, win_rate: float, best_trade: float, worst_trade: float) -> bool:
        """Send daily trading summary"""
        if not self.send_profits:
            return False
        
        message = self.format_daily_summary(trades_today, total_pnl, win_rate, best_trade, worst_trade)
        return await self.send_message(message)
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.is_enabled():
            return False
        
        test_message = f"""
🧪 <b>TELEGRAM BOT TEST</b>

✅ Connection successful!
🤖 Bot is properly configured
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Ready to send trading notifications! 🚀
"""
        
        return await self.send_message(test_message)

# Global telegram bot instance
telegram_bot = TelegramBot()

# Convenience functions for easy integration
async def send_trade_entry_notification(trade: Dict[str, Any]) -> bool:
    """Send trade entry notification"""
    return await telegram_bot.send_trade_entry(trade)

async def send_trade_exit_notification(trade: Dict[str, Any]) -> bool:
    """Send trade exit notification"""
    return await telegram_bot.send_trade_exit(trade)

async def send_hedge_completion_notification(long_trade: Dict[str, Any], short_trade: Dict[str, Any], total_pnl: float) -> bool:
    """Send hedge completion notification"""
    return await telegram_bot.send_hedge_completion(long_trade, short_trade, total_pnl)

async def send_error_notification(error: str, context: str = "") -> bool:
    """Send error notification"""
    return await telegram_bot.send_error(error, context)

async def send_bot_status_notification(status: str, balance: float, open_trades: int, total_pnl: float) -> bool:
    """Send bot status notification"""
    return await telegram_bot.send_bot_status(status, balance, open_trades, total_pnl)

if __name__ == "__main__":
    """Test the Telegram bot functionality"""
    
    async def test_telegram_bot():
        print("Testing Telegram Bot...")
        
        if not telegram_bot.is_enabled():
            print("❌ Telegram bot is not enabled or not configured properly")
            print("Please set TELEGRAM_ENABLED=True and configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config.py")
            return
        
        # Test connection
        success = await telegram_bot.test_connection()
        if success:
            print("✅ Telegram bot test successful!")
        else:
            print("❌ Telegram bot test failed!")
    
    # Run the test
    asyncio.run(test_telegram_bot())
