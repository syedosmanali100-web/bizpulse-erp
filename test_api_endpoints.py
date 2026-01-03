"""
Test all API endpoints to ensure data is loading properly
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        else:
            response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"✅ {name}: OK")
            return result
        else:
            print(f"❌ {name}: Status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"⚠️ {name}: Server not running (connection refused)")
        return None
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return None

def main():
    print("🔧 Testing BizPulse ERP API Endpoints")
    print("=" * 50)
    print()
    
    # Test Products API
    print("📦 PRODUCTS API:")
    test_endpoint("GET /api/products", "/api/products")
    test_endpoint("GET /api/products/debug", "/api/products/debug")
    print()
    
    # Test Sales API
    print("📊 SALES API:")
    test_endpoint("GET /api/sales", "/api/sales")
    test_endpoint("GET /api/sales/all", "/api/sales/all")
    test_endpoint("GET /api/sales/summary", "/api/sales/summary")
    test_endpoint("GET /api/sales/today", "/api/sales/today")
    test_endpoint("GET /api/sales/yesterday", "/api/sales/yesterday")
    test_endpoint("GET /api/sales/top-products", "/api/sales/top-products")
    test_endpoint("GET /api/sales/chart", "/api/sales/chart")
    test_endpoint("GET /api/sales/health", "/api/sales/health")
    test_endpoint("GET /api/sales/export", "/api/sales/export")
    test_endpoint("POST /api/sales/refresh", "/api/sales/refresh", "POST", {})
    print()
    
    # Test Bills API
    print("🧾 BILLS API:")
    test_endpoint("GET /api/bills", "/api/bills")
    print()
    
    # Test Dashboard API
    print("📈 DASHBOARD API:")
    test_endpoint("GET /api/dashboard/stats", "/api/dashboard/stats")
    test_endpoint("GET /api/dashboard/activity", "/api/dashboard/activity")
    print()
    
    print("=" * 50)
    print("🎯 API ENDPOINT TEST COMPLETE")
    print()
    print("If server is not running, start it with:")
    print("  python app.py")

if __name__ == "__main__":
    main()
