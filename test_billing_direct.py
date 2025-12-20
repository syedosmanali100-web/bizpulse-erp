#!/usr/bin/env python3
"""
Direct test of billing functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app to test the function directly
from app import app
import json

def test_billing_direct():
    """Test billing API directly"""
    
    print("🧪 Testing Billing API Directly")
    print("=" * 40)
    
    # Test data matching frontend format
    test_data = {
        "items": [
            {
                "id": "test-product-1",
                "name": "Test Product",
                "price": 100.0,
                "quantity": 1
            }
        ],
        "subtotal": 100.0,
        "cgst": 9.0,
        "sgst": 9.0,
        "total": 118.0,
        "payment_method": "cash",
        "customer_name": "Test Customer"
    }
    
    try:
        with app.test_client() as client:
            print("📤 Sending POST request to /api/sales")
            print(f"Data: {json.dumps(test_data, indent=2)}")
            
            response = client.post(
                '/api/sales',
                data=json.dumps(test_data),
                content_type='application/json'
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.get_json()
                print("✅ SUCCESS! Bill created successfully!")
                print(f"📋 Bill ID: {result.get('bill_id')}")
                print(f"📋 Bill Number: {result.get('bill_number')}")
                print(f"💰 Total Amount: ₹{result.get('total_amount')}")
                print(f"📦 Items Count: {result.get('items_count')}")
                return True
            else:
                print("❌ FAILED! Bill creation failed!")
                try:
                    error_data = response.get_json()
                    print(f"Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"Raw response: {response.get_data(as_text=True)}")
                return False
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_billing_direct()
    if success:
        print("\n🎉 Billing is working correctly!")
    else:
        print("\n💥 Billing has issues!")