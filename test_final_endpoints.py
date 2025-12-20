"""
Final test for all bill creation endpoints
"""

import requests
import json

def test_endpoint(name, url, data=None):
    """Test an endpoint"""
    print(f"\n🧪 Testing: {name}")
    print(f"URL: {url}")
    
    try:
        if data is not None:
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            if response.status_code in [200, 201] and result.get('success'):
                print("✅ SUCCESS!")
                return True
            else:
                print("❌ FAILED!")
                return False
                
        except:
            print(f"Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 FINAL BILL CREATION TEST")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
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
    
    # Test all endpoints
    results = []
    
    # 1. Ultra simple endpoint
    results.append(test_endpoint(
        "Ultra Simple Bill", 
        f"{base_url}/api/create-bill-now", 
        bill_data
    ))
    
    # 2. Simple endpoint
    results.append(test_endpoint(
        "Simple Bill", 
        f"{base_url}/api/bills-simple", 
        bill_data
    ))
    
    # 3. Original simple endpoint
    results.append(test_endpoint(
        "Original Simple Bill", 
        f"{base_url}/api/bills/create", 
        bill_data
    ))
    
    # 4. Test with minimal data
    minimal_data = {"total_amount": 50.0}
    results.append(test_endpoint(
        "Minimal Data Test", 
        f"{base_url}/api/create-bill-now", 
        minimal_data
    ))
    
    # 5. Test with no data
    results.append(test_endpoint(
        "No Data Test", 
        f"{base_url}/api/bills-simple", 
        {}
    ))
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count > 0:
        print(f"✅ {success_count}/{total_count} endpoints working!")
        print("\n🎯 WORKING ENDPOINTS:")
        if results[0]: print("• POST /api/create-bill-now")
        if results[1]: print("• POST /api/bills-simple") 
        if results[2]: print("• POST /api/bills/create")
        
        print("\n📋 CURL EXAMPLES:")
        if results[0]:
            print("curl -X POST http://localhost:5000/api/create-bill-now \\")
            print("  -H 'Content-Type: application/json' \\")
            print("  -d '{\"total_amount\":160.0,\"items\":[{\"product_id\":\"prod-1\",\"quantity\":2,\"unit_price\":80.0}]}'")
        
        if results[1]:
            print("\ncurl -X POST http://localhost:5000/api/bills-simple")
            
    else:
        print("❌ No endpoints working!")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure server is running: python app.py")
        print("2. Check server logs for errors")
        print("3. Try: curl -X POST http://localhost:5000/api/bills-simple")
    
    print("\n🌐 FOR PRODUCTION:")
    print("Replace localhost:5000 with www.bizpulse24.com")
    print("Example: curl -X POST https://www.bizpulse24.com/api/create-bill-now")

if __name__ == "__main__":
    main()