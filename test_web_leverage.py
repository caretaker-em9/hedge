#!/usr/bin/env python3
"""
Simple test to verify web interface with leverage display
"""

from web_interface import app
import json

def test_api_trades():
    """Test the /api/trades endpoint"""
    with app.test_client() as client:
        # Test without authentication first
        response = client.get('/api/trades')
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication required (as expected)")
            
            # Login first
            login_response = client.post('/login', data={
                'username': 'hedgeadmin',
                'password': 'makemoney@123'
            })
            print(f"Login response status: {login_response.status_code}")
            
            # Try API again after login
            response = client.get('/api/trades')
            print(f"Response status after login: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print("✅ API response structure:")
                print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data)) > 500 else json.dumps(data, indent=2))
            else:
                print(f"❌ API call failed: {response.status_code}")
        
        return response.status_code == 200

if __name__ == "__main__":
    print("Testing web interface API with leverage...")
    success = test_api_trades()
    print(f"\n{'✅ Web interface test passed!' if success else '❌ Web interface test failed!'}")
