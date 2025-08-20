#!/usr/bin/env python3
"""
Simple test to verify web interface starts with Freqtrade-style charts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_web_interface():
    """Test web interface startup"""
    print("🧪 Testing Web Interface with Freqtrade Charts")
    print("=" * 50)
    
    try:
        # Import main components
        from web_interface import app, create_candlestick_chart
        from trading_bot import TradingBot, BotConfig
        from config import STRATEGY_PARAMS
        
        print("✅ All imports successful")
        
        # Create bot instance
        config = BotConfig()
        bot = TradingBot(config)
        print("✅ Trading bot created")
        
        # Test data analysis
        analysis = bot.analyze_symbol('BTC/USDT')
        if analysis and 'dataframe' in analysis:
            print(f"✅ Symbol analysis successful: {len(analysis['dataframe'])} data points")
            
            # Test chart creation
            chart_json = create_candlestick_chart(analysis)
            if chart_json:
                print("✅ Freqtrade-style chart created successfully")
                
                # Basic validation
                import json
                chart_data = json.loads(chart_json)
                
                if 'error' in chart_data:
                    print(f"❌ Chart error: {chart_data['error']}")
                    return False
                
                if 'data' in chart_data:
                    traces = len(chart_data['data'])
                    print(f"✅ Chart has {traces} traces")
                    
                    # Check for candlestick trace
                    candlestick_found = False
                    for trace in chart_data['data']:
                        if trace.get('type') == 'candlestick':
                            candlestick_found = True
                            break
                    
                    if candlestick_found:
                        print("✅ Candlestick trace found in chart")
                    else:
                        print("❌ No candlestick trace found")
                        return False
                
                print("✅ Chart validation passed")
            else:
                print("❌ Chart creation failed")
                return False
        else:
            print("❌ Symbol analysis failed")
            return False
        
        # Test Flask app configuration
        app.config['TESTING'] = True
        client = app.test_client()
        print("✅ Flask test client created")
        
        print("\n🎉 Web interface ready!")
        print("📊 Freqtrade-style candlestick charts implemented")
        print("🚀 Run 'python main.py' to start the web interface")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing web interface: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_interface()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
