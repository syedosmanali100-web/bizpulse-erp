#!/usr/bin/env python3
import urllib.request
import json

def test_api():
    try:
        print("🌐 TESTING API DIRECTLY")
        print("=" * 25)
        
        url = 'http://localhost:5000/api/sales/summary'
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        print("API Response Keys:", list(data.keys()))
        
        today = data.get('today', {})
        yesterday = data.get('yesterday', {})
        all_time = data.get('all_time', {})
        
        print(f"TODAY: {today}")
        print(f"YESTERDAY: {yesterday}")
        print(f"ALL TIME: {all_time}")
        
        if yesterday.get('count', 0) > 0:
            print("✅ API WORKING - Yesterday data found!")
        else:
            print("❌ API ISSUE - Yesterday data missing")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    test_api()