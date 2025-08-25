#!/usr/bin/env python3
"""
Test script for the close_trade API endpoint
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_interface import app
import json

def test_close_trade_api():
    """Test the close_trade API endpoint functionality"""
    
    with app.test_client() as client:
        # Test without authentication first (should fail)
        response = client.post('/api/close_trade', 
                              json={'symbol': 'BTC/USDT'},
                              content_type='application/json')
        print(f"Without auth - Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # Test with session (simulate login)
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['login_time'] = 1234567890
        
        # Test with missing symbol
        response = client.post('/api/close_trade', 
                              json={},
                              content_type='application/json')
        print(f"\nMissing symbol - Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # Test with valid symbol (but no bot initialized)
        response = client.post('/api/close_trade', 
                              json={'symbol': 'BTC/USDT'},
                              content_type='application/json')
        print(f"\nNo bot - Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

if __name__ == "__main__":
    print("Testing close_trade API endpoint...")
    test_close_trade_api()
    print("\nAPI endpoint test completed!")
