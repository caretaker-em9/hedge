#!/usr/bin/env python3
"""
Web Interface for Trading Bot
Flask-based web dashboard to monitor trades, view charts, and control the bot
"""

from flask import Flask, render_template, jsonify, request
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

# Setup logger
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Global bot instance
bot = None
bot_thread = None

def create_candlestick_chart(symbol_data, signals_df=None):
    """Create candlestick chart with entry/exit signals and volume"""
    df = symbol_data['dataframe']
    
    # Create subplots with secondary y-axis for volume
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f'{symbol_data["symbol"]} - Price Chart with Signals', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Create candlestick trace with enhanced styling
    candlestick = go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
        increasing_line_color='#00ff88',  # Green for bullish candles
        decreasing_line_color='#ff4444',  # Red for bearish candles
        increasing_fillcolor='#00ff88',
        decreasing_fillcolor='#ff4444',
        line=dict(width=1),
        showlegend=True
    )
    
    fig.add_trace(candlestick, row=1, col=1)
    
    # Add volume bars
    colors = ['#00ff88' if close >= open else '#ff4444' 
              for close, open in zip(df['close'], df['open'])]
    
    volume_bars = go.Bar(
        x=df.index,
        y=df['volume'],
        name='Volume',
        marker_color=colors,
        opacity=0.7,
        showlegend=True
    )
    
    fig.add_trace(volume_bars, row=2, col=1)
    
    # Add moving averages
    if f'ma_buy_{bot.config.base_nb_candles_buy}' in df.columns:
        ma_buy = go.Scatter(
            x=df.index,
            y=df[f'ma_buy_{bot.config.base_nb_candles_buy}'],
            mode='lines',
            name=f'EMA Buy ({bot.config.base_nb_candles_buy})',
            line=dict(color='#2E86AB', width=2, dash='solid'),
            opacity=0.8
        )
        fig.add_trace(ma_buy, row=1, col=1)
    
    if f'ma_sell_{bot.config.base_nb_candles_sell}' in df.columns:
        ma_sell = go.Scatter(
            x=df.index,
            y=df[f'ma_sell_{bot.config.base_nb_candles_sell}'],
            mode='lines',
            name=f'EMA Sell ({bot.config.base_nb_candles_sell})',
            line=dict(color='#F18F01', width=2, dash='solid'),
            opacity=0.8
        )
        fig.add_trace(ma_sell, row=1, col=1)
    
    # Add entry signals with enhanced markers
    if 'enter_long' in df.columns:
        entry_signals = df[df['enter_long'] == 1]
        if not entry_signals.empty:
            entry_scatter = go.Scatter(
                x=entry_signals.index,
                y=entry_signals['close'],
                mode='markers',
                name='Buy Signals',
                marker=dict(
                    color='#00ff00',
                    size=12,
                    symbol='triangle-up',
                    line=dict(color='#008800', width=2)
                ),
                hovertemplate='<b>BUY SIGNAL</b><br>Price: $%{y:.4f}<br>Time: %{x}<extra></extra>'
            )
            fig.add_trace(entry_scatter, row=1, col=1)
    
    # Add exit signals with enhanced markers
    if 'exit_long' in df.columns:
        exit_signals = df[df['exit_long'] == 1]
        if not exit_signals.empty:
            exit_scatter = go.Scatter(
                x=exit_signals.index,
                y=exit_signals['close'],
                mode='markers',
                name='Sell Signals',
                marker=dict(
                    color='#ff0000',
                    size=12,
                    symbol='triangle-down',
                    line=dict(color='#880000', width=2)
                ),
                hovertemplate='<b>SELL SIGNAL</b><br>Price: $%{y:.4f}<br>Time: %{x}<extra></extra>'
            )
            fig.add_trace(exit_scatter, row=1, col=1)
    
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

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/bot/status')
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
def get_trades():
    """Get all trades"""
    if not bot:
        return jsonify([])
    
    trades_data = []
    for trade in bot.trades:
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
            'pnl_percentage': trade.pnl_percentage
        }
        trades_data.append(trade_dict)
    
    return jsonify(trades_data)

@app.route('/api/chart/<path:symbol>')
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
def get_pnl_chart():
    """Get P&L chart"""
    pnl_chart = create_pnl_chart()
    return jsonify({'pnl_chart': pnl_chart})

@app.route('/api/symbols')
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
def get_portfolio():
    """Get portfolio summary"""
    if not bot:
        return jsonify({})
    
    return jsonify(bot.get_portfolio_summary())

if __name__ == '__main__':
    # Initialize bot
    config = BotConfig()
    bot = TradingBot(config)
    
    print("Starting web interface on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
