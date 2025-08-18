#!/bin/bash

# Trading Bot Setup Script
echo "Setting up Trading Bot Environment..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv trading_bot_env

# Activate virtual environment
echo "Activating virtual environment..."
source trading_bot_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install TA-Lib dependencies (Ubuntu/Debian)
echo "Installing TA-Lib dependencies..."
sudo apt-get update
sudo apt-get install -y build-essential wget

# Download and install TA-Lib C library
echo "Installing TA-Lib C library..."
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Install Python packages
echo "Installing Python packages..."
pip install -r requirements.txt

echo "Setup complete!"
echo ""
echo "To run the trading bot:"
echo "1. Activate the virtual environment: source trading_bot_env/bin/activate"
echo "2. Configure your Binance API keys in trading_bot.py"
echo "3. Run the web interface: python web_interface.py"
echo "4. Open your browser to http://localhost:5000"
echo ""
echo "Note: Make sure to use Binance Testnet API keys for testing!"
