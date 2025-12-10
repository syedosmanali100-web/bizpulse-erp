#!/usr/bin/env python3
"""
Test Mobile ERP - Verify all modules and APIs are working
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_api(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ {endpoint} - OK")
            return True
        else:
            print(f"⚠️  {endpoint} - Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {endpoint} - Error: {e}")
        return False

print("="*60)
print("🧪 Testing Mobile ERP APIs")
print("="*60)

# Test core APIs
print("\n📱 Core APIs:")
test_api("/api/version")
test_api("/api/modules")
test_api("/api/modules/quick-access")

# Test data APIs
print("\n📦 Data APIs:")
test_api("/api/products")
test_api("/api/customers")
test_api("/api/bills")

# Test sales APIs
print("\n💰 Sales APIs:")
test_api("/api/sales/summary")
test_api("/api/sales/hourly")
test_api("/api/sales/categories")
test_api("/api/sales/live-stats")

# Test inventory APIs
print("\n📊 Inventory APIs:")
test_api("/api/inventory/low-stock")

# Test invoice APIs
print("\n📄 Invoice APIs:")
test_api("/api/invoices")

# Test mobile routes
print("\n📱 Mobile Routes:")
test_api("/mobile")
test_api("/mobile-working")
test_api("/mobile-pwa")

print("\n" + "="*60)
print("✅ Testing Complete!")
print("="*60)
print("\n💡 If all tests passed, your mobile ERP is ready!")
print("   Open: http://localhost:5000/mobile")
