#!/usr/bin/env python3
"""
Web Interface for Trading Bot
Flask-based web dashboard to monitor trades, view charts, and control the bot
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
import plotly.graph_objs as go
import plotly.utils
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from trading_bot import TradingBot, BotConfig
import threading
import time
import logging
from functools import wraps

# Setup logger
logger = logging.getLogger(__name__)

# Load configuration for authentication
try:
    import config
    WEB_USERNAME = getattr(config, 'WEB_USERNAME', 'admin')
    WEB_PASSWORD = getattr(config, 'WEB_PASSWORD', 'hedge123')
    SESSION_TIMEOUT = getattr(config, 'SESSION_TIMEOUT', 3600)
    SECRET_KEY = getattr(config, 'SECRET_KEY', 'trading_bot_secret_key_change_this_in_production')
except ImportError:
    WEB_USERNAME = 'admin'
    WEB_PASSWORD = 'hedge123'
    SESSION_TIMEOUT = 3600
    SECRET_KEY = 'default_secret_key_change_this'

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(seconds=SESSION_TIMEOUT)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            if request.endpoint and request.endpoint.startswith('api'):
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        
        # Check session timeout
        if 'login_time' in session:
            if datetime.now().timestamp() - session['login_time'] > SESSION_TIMEOUT:
                session.clear()
                if request.endpoint and request.endpoint.startswith('api'):
                    return jsonify({'error': 'Session expired'}), 401
                flash('Session expired. Please log in again.', 'warning')
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# Global bot instance
bot = None
bot_thread = None

def create_candlestick_chart(symbol_data, signals_df=None):
    """Create candlestick chart using Freqtrade-style plotting mechanism"""
    df = symbol_data['dataframe']
    
    # Freqtrade-style chart creation
    from plotly.subplots import make_subplots
    import plotly.graph_objects as go
    
    # Create figure with subplots (price + volume)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol_data["symbol"]} Price Chart', 'Volume'),
        row_heights=[0.8, 0.2],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # Ensure we have the required OHLCV columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_cols):
        return json.dumps({'error': 'Missing OHLCV data'}, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Create candlestick trace - Freqtrade style
    candlestick = go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='OHLC',
        increasing_line_color='#26A69A',  # Freqtrade green
        decreasing_line_color='#EF5350',  # Freqtrade red
        increasing_fillcolor='#26A69A',
        decreasing_fillcolor='#EF5350',
        line=dict(width=1),
        showlegend=False
    )
    
    # Add candlestick to main plot
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add volume bars - Freqtrade style
    colors = ['#26A69A' if close >= open else '#EF5350' 
              for close, open in zip(df['close'], df['open'])]
    
    volume_trace = go.Bar(
        x=df.index,
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.6,
        showlegend=False
    )
    
    fig.add_trace(volume_trace, row=2, col=1)
    
    # Add buy signals - Freqtrade style
    if 'enter_long' in df.columns:
        buy_signals = df[df['enter_long'] == 1]
        if not buy_signals.empty:
            buy_scatter = go.Scatter(
                x=buy_signals.index,
                y=buy_signals['low'] * 0.998,  # Place slightly below low
                mode='markers',
                name='Buy Signal',
                marker=dict(
                    symbol='triangle-up',
                    size=10,
                    color='#00FF00',
                    line=dict(color='#008000', width=1)
                ),
                showlegend=True,
                hovertemplate='<b>BUY</b><br>Price: %{text}<br>%{x}<extra></extra>',
                text=[f'${price:.2f}' for price in buy_signals['close']]
            )
            fig.add_trace(buy_scatter, row=1, col=1)
    
    # Add sell signals - Freqtrade style  
    if 'exit_long' in df.columns:
        sell_signals = df[df['exit_long'] == 1]
        if not sell_signals.empty:
            sell_scatter = go.Scatter(
                x=sell_signals.index,
                y=sell_signals['high'] * 1.002,  # Place slightly above high
                mode='markers',
                name='Sell Signal',
                marker=dict(
                    symbol='triangle-down',
                    size=10,
                    color='#FF0000',
                    line=dict(color='#800000', width=1)
                ),
                showlegend=True,
                hovertemplate='<b>SELL</b><br>Price: %{text}<br>%{x}<extra></extra>',
                text=[f'${price:.2f}' for price in sell_signals['close']]
            )
            fig.add_trace(sell_scatter, row=1, col=1)
    
    # Update layout - Freqtrade style
    fig.update_layout(
        title=f'{symbol_data["symbol"]} Trading Chart',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Time",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        row=2, col=1
    )
    
    fig.update_yaxes(
        title_text="Price (USDT)",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        row=1, col=1
    )
    
    fig.update_yaxes(
        title_text="Volume",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)',
        row=2, col=1
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Update layout with enhanced styling
    fig.update_layout(
        title=dict(
            text=f'{symbol_data["symbol"]} - Candlestick Chart with Trading Signals',
            x=0.5,
            font=dict(size=16, color='#333333')
        ),
        template='plotly_white',
        height=700,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    # Update x-axis
    fig.update_xaxes(
        title_text="Time",
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=2, col=1
    )
    
    # Update y-axis for price
    fig.update_yaxes(
        title_text="Price (USDT)",
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=1, col=1
    )
    
    # Update y-axis for volume
    fig.update_yaxes(
        title_text="Volume",
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=2, col=1
    )
    
    # Remove range slider for cleaner look
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_indicator_chart(symbol_data):
    """Create enhanced indicator charts (RSI, EWO) with better styling"""
    df = symbol_data['dataframe']
    
    # Create subplots for indicators
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('RSI (Relative Strength Index)', 'EWO (Elliott Wave Oscillator)'),
        vertical_spacing=0.15,
        row_heights=[0.5, 0.5]
    )
    
    # RSI Chart with enhanced styling
    if 'rsi' in df.columns:
        # RSI line
        fig.add_trace(
            go.Scatter(
                x=df.index, 
                y=df['rsi'], 
                name='RSI',
                line=dict(color='#8A2BE2', width=2),
                fill=None
            ),
            row=1, col=1
        )
        
        # RSI overbought/oversold zones
        fig.add_hline(
            y=70, line_dash="dash", line_color="#ff6b6b", 
            annotation_text="Overbought (70)", annotation_position="bottom right",
            row=1, col=1
        )
        fig.add_hline(
            y=30, line_dash="dash", line_color="#51cf66", 
            annotation_text="Oversold (30)", annotation_position="top right",
            row=1, col=1
        )
        fig.add_hline(
            y=bot.config.rsi_buy, line_dash="dot", line_color="#4dabf7", 
            annotation_text=f"Buy Threshold ({bot.config.rsi_buy})", annotation_position="top left",
            row=1, col=1
        )
        
        # Add background color zones
        fig.add_hrect(
            y0=70, y1=100, fillcolor="#ff6b6b", opacity=0.1,
            layer="below", line_width=0, row=1, col=1
        )
        fig.add_hrect(
            y0=0, y1=30, fillcolor="#51cf66", opacity=0.1,
            layer="below", line_width=0, row=1, col=1
        )
    
    # EWO Chart with enhanced styling
    if 'EWO' in df.columns:
        # EWO line with conditional coloring
        colors = ['#00ff88' if val > 0 else '#ff4444' for val in df['EWO']]
        
        fig.add_trace(
            go.Scatter(
                x=df.index, 
                y=df['EWO'], 
                name='EWO',
                line=dict(color='#FF6347', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 99, 71, 0.2)'
            ),
            row=2, col=1
        )
        
        # EWO threshold lines
        fig.add_hline(
            y=bot.config.ewo_high, line_dash="dash", line_color="#ff6b6b",
            annotation_text=f"High Threshold ({bot.config.ewo_high:.1f})", annotation_position="bottom right",
            row=2, col=1
        )
        fig.add_hline(
            y=bot.config.ewo_low, line_dash="dash", line_color="#51cf66",
            annotation_text=f"Low Threshold ({bot.config.ewo_low:.1f})", annotation_position="top right",
            row=2, col=1
        )
        fig.add_hline(
            y=0, line_dash="dot", line_color="#9ca3af",
            annotation_text="Zero Line", annotation_position="top left",
            row=2, col=1
        )
        
        # Add background color zones for EWO
        fig.add_hrect(
            y0=bot.config.ewo_high, y1=max(df['EWO'].max(), bot.config.ewo_high + 5), 
            fillcolor="#ff6b6b", opacity=0.1,
            layer="below", line_width=0, row=2, col=1
        )
        fig.add_hrect(
            y0=min(df['EWO'].min(), bot.config.ewo_low - 5), y1=bot.config.ewo_low, 
            fillcolor="#51cf66", opacity=0.1,
            layer="below", line_width=0, row=2, col=1
        )
    
    # Update layout with enhanced styling
    fig.update_layout(
        title=dict(
            text=f'{symbol_data["symbol"]} - Technical Indicators',
            x=0.5,
            font=dict(size=16, color='#333333')
        ),
        height=600,
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='x unified'
    )
    
    # Update RSI y-axis
    fig.update_yaxes(
        title_text="RSI",
        range=[0, 100],
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=1, col=1
    )
    
    # Update EWO y-axis
    fig.update_yaxes(
        title_text="EWO",
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=2, col=1
    )
    
    # Update x-axis
    fig.update_xaxes(
        title_text="Time",
        showgrid=True,
        gridwidth=1,
        gridcolor='#f0f0f0',
        row=2, col=1
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def create_pnl_chart():
    """Create enhanced P&L chart with better styling"""
    if not bot or not bot.trades:
        return json.dumps({})
    
    closed_trades = [t for t in bot.trades if t.status == 'closed' and t.pnl is not None]
    
    if not closed_trades:
        return json.dumps({})
    
    # Calculate cumulative PnL
    cumulative_pnl = []
    running_total = bot.config.initial_balance
    timestamps = []
    trade_pnls = []
    trade_symbols = []
    
    for trade in sorted(closed_trades, key=lambda x: x.exit_timestamp):
        running_total += trade.pnl
        cumulative_pnl.append(running_total)
        timestamps.append(trade.exit_timestamp)
        trade_pnls.append(trade.pnl)
        trade_symbols.append(trade.symbol)
    
    # Create main P&L line
    trace = go.Scatter(
        x=timestamps,
        y=cumulative_pnl,
        mode='lines+markers',
        name='Portfolio Balance',
        line=dict(color='#2E86AB', width=3),
        marker=dict(size=8, color='#2E86AB'),
        fill='tonexty',
        fillcolor='rgba(46, 134, 171, 0.1)',
        hovertemplate='<b>Balance: $%{y:.2f}</b><br>Time: %{x}<extra></extra>'
    )
    
    # Add baseline at initial balance
    baseline = go.Scatter(
        x=[timestamps[0], timestamps[-1]],
        y=[bot.config.initial_balance, bot.config.initial_balance],
        mode='lines',
        name='Initial Balance',
        line=dict(color='#9CA3AF', width=2, dash='dash'),
        hoverinfo='skip'
    )
    
    # Add individual trade markers
    colors = ['#00ff88' if pnl > 0 else '#ff4444' for pnl in trade_pnls]
    trade_markers = go.Scatter(
        x=timestamps,
        y=cumulative_pnl,
        mode='markers',
        name='Trades',
        marker=dict(
            size=12,
            color=colors,
            line=dict(color='white', width=2),
            symbol='circle'
        ),
        text=[f'{symbol}<br>P&L: ${pnl:.2f}' for symbol, pnl in zip(trade_symbols, trade_pnls)],
        hovertemplate='<b>%{text}</b><br>Balance: $%{y:.2f}<br>Time: %{x}<extra></extra>'
    )
    
    layout = go.Layout(
        title=dict(
            text='Portfolio Performance Over Time',
            x=0.5,
            font=dict(size=16, color='#333333')
        ),
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0'
        ),
        yaxis=dict(
            title='Balance (USDT)',
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0'
        ),
        template='plotly_white',
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='closest'
    )
    
    fig = go.Figure(data=[baseline, trace, trade_markers], layout=layout)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == WEB_USERNAME and password == WEB_PASSWORD:
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().timestamp()
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/bot/status')
@login_required
def bot_status():
    """Get bot status"""
    if not bot:
        return jsonify({'status': 'stopped', 'message': 'Bot not initialized'})
    
    return jsonify({
        'status': 'running' if bot.is_running else 'stopped',
        'balance': bot.balance,
        'portfolio': bot.get_portfolio_summary()
    })

@app.route('/api/bot/start', methods=['POST'])
@login_required
def start_bot():
    """Start the trading bot"""
    global bot, bot_thread
    
    try:
        if not bot:
            config = BotConfig()
            bot = TradingBot(config)
        
        if not bot.is_running:
            bot.start()
            return jsonify({'success': True, 'message': 'Bot started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Bot is already running'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting bot: {str(e)}'})

@app.route('/api/bot/stop', methods=['POST'])
@login_required
def stop_bot():
    """Stop the trading bot"""
    global bot
    
    try:
        if bot and bot.is_running:
            bot.stop()
            return jsonify({'success': True, 'message': 'Bot stopped successfully'})
        else:
            return jsonify({'success': False, 'message': 'Bot is not running'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping bot: {str(e)}'})

@app.route('/api/trades')
@login_required
def get_trades():
    """Get all trades with detailed entry/exit reasons and current P&L for open positions"""
    if not bot:
        return jsonify([])
    
    trades_data = []
    for trade in bot.trades:
        # Get actual leverage from exchange for this trade
        actual_leverage = bot.get_trade_leverage(trade)
        
        trade_dict = {
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'amount': trade.amount,
            'price': trade.price,
            'timestamp': trade.timestamp.isoformat(),
            'status': trade.status,
            'entry_signal': trade.entry_signal,
            'exit_signal': trade.exit_signal,
            'exit_price': trade.exit_price,
            'exit_timestamp': trade.exit_timestamp.isoformat() if trade.exit_timestamp else None,
            'pnl': trade.pnl,
            'pnl_percentage': trade.pnl_percentage,
            'trade_type': getattr(trade, 'trade_type', 'normal'),
            'pair_id': getattr(trade, 'pair_id', None),
            'leverage': actual_leverage,  # Actual leverage from exchange
            # Detailed reasons
            'entry_reason': getattr(trade, 'entry_reason', 'Standard entry'),
            'exit_reason': getattr(trade, 'exit_reason', None),
        }
        
        # Add current price and unrealized P&L for open positions
        if trade.status == 'open':
            try:
                current_price = bot._get_current_price(trade.symbol)
                if current_price:
                    trade_dict['current_price'] = current_price
                    price_diff = current_price - trade.price
                    current_pnl = price_diff * trade.amount
                    current_pnl_percentage = (price_diff / trade.price) * 100 * actual_leverage
                    
                    trade_dict['current_pnl'] = current_pnl
                    trade_dict['current_pnl_percentage'] = current_pnl_percentage
                    
                    # Calculate time in trade and ROI threshold if applicable
                    time_diff = (datetime.now() - trade.timestamp).total_seconds() / 60
                    trade_dict['time_in_trade_minutes'] = time_diff
                    
                    if trade.trade_type == 'normal':
                        roi_threshold = bot._get_roi_threshold(time_diff)
                        trade_dict['roi_threshold'] = roi_threshold
                        trade_dict['roi_threshold_percentage'] = roi_threshold * 100
                        
                        # Check if close to ROI exit
                        profit_pct = price_diff / trade.price
                        trade_dict['close_to_roi_exit'] = profit_pct >= (roi_threshold * 0.8)  # Within 80% of ROI threshold
                        
                        # Add trailing stop information
                        if hasattr(trade, 'max_price') and trade.max_price:
                            trade_dict['max_price'] = trade.max_price
                            trade_dict['max_profit_percentage'] = ((trade.max_price - trade.price) / trade.price) * 100
                            
                        if hasattr(trade, 'trailing_stop_price') and trade.trailing_stop_price:
                            trade_dict['trailing_stop_price'] = trade.trailing_stop_price
                            trade_dict['trailing_stop_distance'] = ((current_price - trade.trailing_stop_price) / current_price) * 100
                        
            except Exception as e:
                logger.error(f"Error getting current price for {trade.symbol}: {e}")
        
        # Add additional trade metadata
        trade_dict['technical_indicators'] = getattr(trade, 'technical_indicators', {})
        trade_dict['market_conditions'] = getattr(trade, 'market_conditions', 'Normal conditions')
        
        trades_data.append(trade_dict)
    
    # Calculate total PnL (realized + unrealized)
    total_realized_pnl = sum(trade.pnl for trade in bot.trades if trade.status == 'closed')
    total_unrealized_pnl = 0
    total_open_trades = 0
    
    for trade in bot.trades:
        if trade.status == 'open':
            total_open_trades += 1
            try:
                current_price = bot._get_current_price(trade.symbol)
                if current_price:
                    price_diff = current_price - trade.price
                    if trade.side == 'buy':
                        unrealized_pnl = price_diff * trade.amount
                    else:  # sell/short
                        unrealized_pnl = -price_diff * trade.amount
                    total_unrealized_pnl += unrealized_pnl
            except Exception as e:
                logger.error(f"Error calculating unrealized PnL for {trade.symbol}: {e}")
    
    total_pnl = total_realized_pnl + total_unrealized_pnl
    
    # Return trades data with summary
    return jsonify({
        'trades': trades_data,
        'summary': {
            'total_trades': len(bot.trades),
            'open_trades': total_open_trades,
            'closed_trades': len(bot.trades) - total_open_trades,
            'total_realized_pnl': total_realized_pnl,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_pnl': total_pnl,
            'max_trades': bot.config.max_trades
        }
    })

@app.route('/api/close_trade', methods=['POST'])
@login_required
def close_trade():
    """Close a specific trade by symbol"""
    if not bot:
        return jsonify({'error': 'Bot not initialized', 'success': False})
    
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'Symbol is required', 'success': False})
        
        symbol = data['symbol']
        logger.info(f"Attempting to close trade for symbol: {symbol}")
        
        # Find open trades for this symbol
        open_trades = [trade for trade in bot.trades if trade.symbol == symbol and trade.status == 'open']
        
        if not open_trades:
            return jsonify({'error': f'No open trades found for {symbol}', 'success': False})
        
        # Close all open trades for this symbol
        closed_count = 0
        errors = []
        
        for trade in open_trades:
            try:
                # Determine close side (opposite of open side)
                close_side = 'sell' if trade.side == 'buy' else 'buy'
                
                # Get current market price
                current_price = bot._get_current_price(symbol)
                if not current_price:
                    errors.append(f"Could not get current price for {symbol}")
                    continue
                
                # Create market order to close position
                order_result = bot.exchange.create_market_order(
                    symbol=symbol,
                    side=close_side,
                    amount=trade.amount,
                    params={'reduceOnly': True}  # Ensure we're closing position, not opening new one
                )
                
                if order_result:
                    # Update trade status
                    trade.status = 'closed'
                    trade.close_price = current_price
                    trade.close_time = datetime.now()
                    
                    # Calculate realized PnL
                    if trade.side == 'buy':
                        trade.realized_pnl = (current_price - trade.price) * trade.amount
                    else:
                        trade.realized_pnl = (trade.price - current_price) * trade.amount
                    
                    closed_count += 1
                    logger.info(f"Successfully closed {trade.side} trade for {symbol}, PnL: ${trade.realized_pnl:.2f}")
                    
                    # Send Telegram notification if enabled
                    if hasattr(bot.config, 'TELEGRAM_ENABLED') and bot.config.TELEGRAM_ENABLED:
                        bot._send_telegram_message(
                            f"🔒 Trade Closed (Manual)\n"
                            f"Symbol: {symbol}\n"
                            f"Side: {trade.side.upper()}\n"
                            f"Amount: {trade.amount}\n"
                            f"Entry: ${trade.price:.4f}\n"
                            f"Exit: ${current_price:.4f}\n"
                            f"PnL: ${trade.realized_pnl:.2f}\n"
                            f"Time: {trade.close_time.strftime('%H:%M:%S')}"
                        )
                else:
                    errors.append(f"Failed to create close order for {symbol}")
                    
            except Exception as e:
                error_msg = f"Error closing trade for {symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        if closed_count > 0:
            message = f"Successfully closed {closed_count} trade(s) for {symbol}"
            if errors:
                message += f". Errors: {'; '.join(errors)}"
            return jsonify({'success': True, 'message': message, 'closed_count': closed_count})
        else:
            error_message = f"Failed to close any trades for {symbol}"
            if errors:
                error_message += f". Errors: {'; '.join(errors)}"
            return jsonify({'error': error_message, 'success': False})
            
    except Exception as e:
        error_msg = f"Error processing close trade request: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg, 'success': False})

@app.route('/api/chart/<path:symbol>')
@login_required
def get_chart(symbol):
    """Get chart data for a symbol"""
    if not bot:
        return jsonify({'error': 'Bot not initialized'})
    
    # If symbol not in cache, try to analyze it now
    if symbol not in bot.data_cache:
        try:
            logger.info(f"Symbol {symbol} not in cache, analyzing now...")
            analysis = bot.analyze_symbol(symbol)
            bot.data_cache[symbol] = analysis
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return jsonify({'error': f'Failed to analyze {symbol}: {str(e)}'})
    
    if symbol not in bot.data_cache:
        return jsonify({'error': f'No data available for {symbol}'})
    
    symbol_data = bot.data_cache[symbol]
    
    try:
        price_chart = create_candlestick_chart(symbol_data)
        indicator_chart = create_indicator_chart(symbol_data)
        
        return jsonify({
            'price_chart': price_chart,
            'indicator_chart': indicator_chart
        })
    except Exception as e:
        logger.error(f"Error creating charts for {symbol}: {e}")
        return jsonify({'error': f'Failed to create charts: {str(e)}'})

@app.route('/api/chart/pnl')
@login_required
def get_pnl_chart():
    """Get P&L chart"""
    pnl_chart = create_pnl_chart()
    return jsonify({'pnl_chart': pnl_chart})

@app.route('/api/symbols')
@login_required
def get_symbols():
    """Get available symbols"""
    if not bot:
        return jsonify([])
    
    return jsonify(bot.config.symbols)

@app.route('/api/symbol_stats')
def get_symbol_stats():
    """Get symbol statistics including volume info"""
    if not bot:
        return jsonify({})
    
    try:
        stats = {
            'total_symbols': len(bot.config.symbols),
            'symbols_with_data': len(bot.data_cache),
            'active_symbols': bot.config.symbols[:20],  # Show first 20
            'last_update': datetime.now().isoformat()
        }
        
        # Add volume info if available
        if hasattr(bot.exchange, 'fetch_tickers'):
            try:
                tickers = bot.exchange.fetch_tickers()
                symbol_volumes = []
                for symbol in bot.config.symbols[:10]:  # Top 10 by current list
                    if symbol in tickers:
                        symbol_volumes.append({
                            'symbol': symbol,
                            'volume': tickers[symbol].get('quoteVolume', 0),
                            'price': tickers[symbol].get('last', 0),
                            'change': tickers[symbol].get('percentage', 0)
                        })
                stats['top_symbols'] = symbol_volumes
            except Exception as e:
                logger.error(f"Error fetching symbol stats: {e}")
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/refresh_symbols', methods=['POST'])
def refresh_symbols():
    """Refresh symbol list based on current volume"""
    if not bot:
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    try:
        old_count = len(bot.config.symbols)
        bot.update_symbol_list()
        new_count = len(bot.config.symbols)
        
        return jsonify({
            'success': True, 
            'message': f'Symbol list updated: {old_count} → {new_count} symbols',
            'symbol_count': new_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating symbols: {str(e)}'})

@app.route('/api/refresh_data', methods=['POST'])
def refresh_data():
    """Refresh data for all symbols"""
    if not bot:
        return jsonify({'success': False, 'message': 'Bot not initialized'})
    
    try:
        # Refresh a subset of symbols to avoid timeout
        symbols_to_refresh = bot.config.symbols[:20]  # Limit to first 20 for quick refresh
        
        for symbol in symbols_to_refresh:
            analysis = bot.analyze_symbol(symbol)
            bot.data_cache[symbol] = analysis
        
        return jsonify({
            'success': True, 
            'message': f'Data refreshed for {len(symbols_to_refresh)} symbols'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error refreshing data: {str(e)}'})

@app.route('/api/portfolio')
@login_required
def get_portfolio():
    """Get portfolio summary"""
    if not bot:
        return jsonify({})
    
    return jsonify(bot.get_portfolio_summary())

@app.route('/api/hedge_pairs')
@login_required
def get_hedge_pairs():
    """Get hedge pairs status"""
    if not bot:
        return jsonify([])
    
    hedge_pairs_data = []
    for pair in bot.hedge_pairs:
        pair_data = {
            'pair_id': pair.pair_id,
            'symbol': pair.symbol,
            'status': pair.status,
            'total_allocation': pair.total_allocation,
            'long_size': pair.long_size,
            'short_size': pair.short_size,
            'hedge_trigger': pair.hedge_trigger,
            'created_timestamp': pair.created_timestamp.isoformat() if pair.created_timestamp else None,
            'long_trade': None,
            'short_trade': None
        }
        
        if pair.long_trade:
            pair_data['long_trade'] = {
                'id': pair.long_trade.id,
                'price': pair.long_trade.price,
                'amount': pair.long_trade.amount,
                'timestamp': pair.long_trade.timestamp.isoformat(),
                'status': pair.long_trade.status,
                'pnl': pair.long_trade.pnl,
                'pnl_percentage': pair.long_trade.pnl_percentage
            }
        
        if pair.short_trade:
            pair_data['short_trade'] = {
                'id': pair.short_trade.id,
                'price': pair.short_trade.price,
                'amount': pair.short_trade.amount,
                'timestamp': pair.short_trade.timestamp.isoformat(),
                'status': pair.short_trade.status,
                'pnl': pair.short_trade.pnl,
                'pnl_percentage': pair.short_trade.pnl_percentage
            }
        
        hedge_pairs_data.append(pair_data)
    
    return jsonify(hedge_pairs_data)

if __name__ == '__main__':
    # Initialize bot
    config = BotConfig()
    bot = TradingBot(config)
    
    # Get port from config
    web_port = getattr(config, 'WEB_PORT', 5000)
    print(f"Starting web interface on http://localhost:{web_port}")
    app.run(debug=True, host='0.0.0.0', port=web_port)
