#!/usr/bin/env python3

import time
import requests
import json
from datetime import datetime, timedelta

def test_authentication_and_trade_display():
    """Test the authentication system and detailed trade display"""
    
    base_url = "http://localhost:5000"
    
    # Test that we get redirected to login when not authenticated
    print("Testing authentication...")
    response = requests.get(f"{base_url}/")
    print(f"Unauthenticated access status: {response.status_code}")
    
    # Create a session and login
    session = requests.Session()
    
    # Login with credentials from config
    login_data = {
        'username': 'admin',
        'password': 'hedge123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code == 200 or login_response.status_code == 302:
        print("✅ Authentication successful!")
        
        # Test accessing the dashboard
        dashboard_response = session.get(f"{base_url}/")
        print(f"Dashboard access status: {dashboard_response.status_code}")
        
        # Test API endpoints
        trades_response = session.get(f"{base_url}/api/trades")
        print(f"Trades API status: {trades_response.status_code}")
        
        if trades_response.status_code == 200:
            trades = trades_response.json()
            print(f"Current trades count: {len(trades)}")
            
            # Display any existing trade details
            for i, trade in enumerate(trades[:3]):  # Show first 3 trades
                print(f"\nTrade {i+1}:")
                print(f"  Symbol: {trade.get('symbol')}")
                print(f"  Side: {trade.get('side')}")
                print(f"  Entry Reason: {trade.get('entry_reason', 'N/A')}")
                print(f"  Exit Reason: {trade.get('exit_reason', 'N/A')}")
                print(f"  Technical Indicators: {trade.get('technical_indicators', 'N/A')}")
                print(f"  Market Conditions: {trade.get('market_conditions', 'N/A')}")
        
        # Test bot status
        status_response = session.get(f"{base_url}/api/status")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"\nBot Status: {status}")
        
    else:
        print("❌ Authentication failed!")
        print(f"Response: {login_response.text}")

def create_sample_trade_data():
    """Create some sample trades with detailed information to test the display"""
    
    session = requests.Session()
    
    # Login first
    login_data = {'username': 'admin', 'password': 'hedge123'}
    session.post("http://localhost:5000/login", data=login_data)
    
    # Try to start the bot to create some activity
    start_response = session.post("http://localhost:5000/api/bot/start")
    print(f"Bot start response: {start_response.status_code}")
    
    if start_response.status_code == 200:
        print("✅ Bot started successfully!")
        
        # Let it run for a few seconds to potentially create trades
        print("Waiting for potential trade creation...")
        time.sleep(10)
        
        # Check for new trades
        trades_response = session.get("http://localhost:5000/api/trades")
        if trades_response.status_code == 200:
            trades = trades_response.json()
            print(f"Trades after bot run: {len(trades)}")
            
            for trade in trades[-3:]:  # Show last 3 trades
                print(f"\nRecent Trade:")
                print(f"  Symbol: {trade.get('symbol')}")
                print(f"  Side: {trade.get('side')}")
                print(f"  Status: {trade.get('status')}")
                print(f"  Entry Reason: {trade.get('entry_reason', 'N/A')}")
                print(f"  Technical Indicators: {trade.get('technical_indicators', 'N/A')}")
        
        # Stop the bot
        stop_response = session.post("http://localhost:5000/api/bot/stop")
        print(f"Bot stop response: {stop_response.status_code}")

if __name__ == "__main__":
    print("Testing Authentication and Detailed Trade Display")
    print("=" * 50)
    
    try:
        test_authentication_and_trade_display()
        print("\n" + "=" * 50)
        print("Testing Trade Creation...")
        create_sample_trade_data()
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the web interface.")
        print("Make sure the trading bot is running with: python main.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("\n✅ Testing completed!")
    print("\nYou can now:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Login with username: admin, password: hedge123")
    print("3. View the enhanced dashboard with detailed trade reasons")
