#!/usr/bin/env python3
"""
Test Freqtrade-style candlestick chart creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.utils
import json

def create_freqtrade_candlestick_chart(df, symbol="TEST/USDT"):
    """Create Freqtrade-style candlestick chart"""
    
    # Create figure with subplots (price + volume)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} Price Chart', 'Volume'),
        row_heights=[0.8, 0.2],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
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
    
    # Add sample buy/sell signals
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
        title=f'{symbol} Trading Chart',
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
    
    return fig

def test_freqtrade_chart():
    """Test the Freqtrade-style chart creation"""
    print("🧪 Testing Freqtrade-style Candlestick Chart")
    print("=" * 50)
    
    # Create realistic test data
    dates = pd.date_range('2024-01-01', periods=100, freq='5min')
    
    # Generate realistic price data
    base_price = 50000
    price_changes = np.random.randn(100) * 0.001
    price_changes[0] = 0
    cumulative_changes = np.cumsum(price_changes)
    close_prices = base_price * (1 + cumulative_changes)
    
    # Create OHLC data
    df = pd.DataFrame({
        'open': close_prices,
        'close': close_prices * (1 + np.random.randn(100) * 0.0005),
        'volume': np.random.uniform(100, 1000, 100),
    }, index=dates)
    
    # Ensure proper high/low
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.randn(100) * 0.0002))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.randn(100) * 0.0002))
    
    # Add some signals
    df['enter_long'] = 0
    df['exit_long'] = 0
    df.iloc[20, df.columns.get_loc('enter_long')] = 1
    df.iloc[60, df.columns.get_loc('exit_long')] = 1
    df.iloc[80, df.columns.get_loc('enter_long')] = 1
    
    print(f"✅ Test data created: {df.shape}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"   Buy signals: {df['enter_long'].sum()}")
    print(f"   Sell signals: {df['exit_long'].sum()}")
    
    # Create chart
    fig = create_freqtrade_candlestick_chart(df)
    
    print(f"✅ Chart created with {len(fig.data)} traces")
    
    # Analyze traces
    candlestick_traces = 0
    volume_traces = 0
    signal_traces = 0
    
    for trace in fig.data:
        if hasattr(trace, 'type'):
            if trace.type == 'candlestick':
                candlestick_traces += 1
                print(f"   📊 Candlestick trace: {len(trace.x)} data points")
            elif trace.type == 'bar':
                volume_traces += 1
                print(f"   📈 Volume trace: {len(trace.x)} data points")
            elif trace.type == 'scatter':
                signal_traces += 1
                print(f"   🎯 Signal trace: {trace.name}")
    
    print(f"✅ Chart analysis:")
    print(f"   - Candlestick traces: {candlestick_traces}")
    print(f"   - Volume traces: {volume_traces}")
    print(f"   - Signal traces: {signal_traces}")
    
    # Save as HTML for testing
    fig.write_html("freqtrade_test_chart.html")
    print(f"✅ Chart saved as 'freqtrade_test_chart.html'")
    
    return True

if __name__ == "__main__":
    try:
        success = test_freqtrade_chart()
        if success:
            print("\n🎉 Freqtrade-style chart test completed successfully!")
            print("📁 Open 'freqtrade_test_chart.html' in your browser to view the chart")
        else:
            print("\n❌ Chart test failed")
    except Exception as e:
        print(f"\n❌ Error during chart test: {e}")
        import traceback
        traceback.print_exc()
