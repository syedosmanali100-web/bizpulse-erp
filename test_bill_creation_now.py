"""
Quick test for bill creation - WORKING VERSION
"""

import requests
import json

def test_create_bill():
    """Test the simple bill creation endpoint"""
    print("🧪 Testing Simple Bill Creation")
    
    # Test data
    data = {
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
    
    try:
        # Create bill
        response = requests.post("http://localhost:5000/api/bills/create", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ SUCCESS: Bill created!")
            return True
        else:
            print("❌ FAILED: Bill creation failed")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_get_bills():
    """Test getting bills"""
    print("\n🧪 Testing Get Bills")
    
    try:
        response = requests.get("http://localhost:5000/api/bills/list")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            bills = response.json().get('bills', [])
            print(f"✅ SUCCESS: Found {len(bills)} bills")
            if bills:
                print(f"Latest bill: {bills[0].get('bill_number')}")
            return True
        else:
            print("❌ FAILED: Could not get bills")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTING BILL CREATION")
    print("=" * 50)
    
    # Test 1: Create bill
    success1 = test_create_bill()
    
    # Test 2: Get bills
    success2 = test_get_bills()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    print("\nEndpoints available:")
    print("• POST /api/bills/create - Create bill")
    print("• GET /api/bills/list - Get bills")