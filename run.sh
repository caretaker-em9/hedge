#!/bin/bash

# Trading Bot Runner Script
echo "Starting Trading Bot Application..."

# Check if virtual environment exists
if [ ! -d "trading_bot_env" ]; then
    echo "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source trading_bot_env/bin/activate

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo "Configuration file not found. Creating from template..."
    cp config_template.py config.py
    echo "Please edit config.py with your API keys and settings before running again."
    exit 1
fi

# Check for API keys in config
if grep -q "your_testnet_api_key_here" config.py; then
    echo "⚠️  Warning: Using default API keys (demo mode)"
    echo "   Update config.py with your Binance Testnet API keys for live trading"
    echo ""
fi

# Start the application
echo "Starting web interface on http://localhost:5000"
echo "Press Ctrl+C to stop the application"
echo ""
python main.py
