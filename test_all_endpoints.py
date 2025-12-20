"""
Test all bill creation endpoints
"""

import requests
import json

def test_endpoint(url, data=None, method='GET'):
    """Test an endpoint"""
    try:
        if method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return response.status_code, result
        except:
            print(f"Response: {response.text}")
            return response.status_code, response.text
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, str(e)

def main():
    print("🧪 TESTING ALL BILL ENDPOINTS")
    print("=" * 60)
    
    # Test data
    bill_data = {
        "items": [
            {
                "product_id": "prod-1",
                "product_name": "Rice 1kg",
                "quantity": 2,
                "unit_price": 80.0
            }
        ],
        "total_amount": 160.0,
        "customer_id": "cust-1",
        "payment_method": "cash"
    }
    
    base_url = "http://localhost:5000"
    
    # Test 1: Super simple test endpoint
    print("\n1️⃣ Testing: POST /api/test-bill")
    status, result = test_endpoint(f"{base_url}/api/test-bill", {}, 'POST')
    if status == 201:
        print("✅ Test endpoint works!")
    else:
        print("❌ Test endpoint failed")
    
    # Test 2: Main bill creation endpoint
    print("\n2️⃣ Testing: POST /api/bills")
    status, result = test_endpoint(f"{base_url}/api/bills", bill_data, 'POST')
    if status == 201:
        print("✅ Main bill endpoint works!")
    else:
        print("❌ Main bill endpoint failed")
    
    # Test 3: Simple bill creation endpoint
    print("\n3️⃣ Testing: POST /api/bills/create")
    status, result = test_endpoint(f"{base_url}/api/bills/create", bill_data, 'POST')
    if status == 201:
        print("✅ Simple bill endpoint works!")
    else:
        print("❌ Simple bill endpoint failed")
    
    # Test 4: Get bills
    print("\n4️⃣ Testing: GET /api/bills/list")
    status, result = test_endpoint(f"{base_url}/api/bills/list")
    if status == 200:
        print("✅ Get bills works!")
    else:
        print("❌ Get bills failed")
    
    print("\n" + "=" * 60)
    print("🎯 AVAILABLE ENDPOINTS:")
    print("• POST /api/test-bill - Super simple test")
    print("• POST /api/bills - Main bill creation")
    print("• POST /api/bills/create - Simple bill creation")
    print("• GET /api/bills/list - Get all bills")
    
    print("\n📋 CURL EXAMPLES:")
    print("# Test endpoint:")
    print("curl -X POST http://localhost:5000/api/test-bill")
    print("\n# Create bill:")
    print("curl -X POST http://localhost:5000/api/bills \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"items\":[{\"product_id\":\"prod-1\",\"quantity\":2,\"unit_price\":80.0}],\"total_amount\":160.0}'")
    print("\n# Get bills:")
    print("curl http://localhost:5000/api/bills/list")

if __name__ == "__main__":
    main()