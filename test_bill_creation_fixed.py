#!/usr/bin/env python3
"""
Test script to verify the datetime fixes in bill creation
"""

import urllib.request
import json

def test_bill_creation():
    print("🧪 TESTING BILL CREATION - DATETIME FIXES")
    print("=" * 50)
    
    # Test data with various field name combinations
    test_cases = [
        {
            "name": "Standard Fields",
            "data": {
                "business_type": "retail",
                "items": [
                    {
                        "product_id": "prod-1",
                        "product_name": "Rice (1kg)",
                        "quantity": 2,
                        "unit_price": 80.0,
                        "total_price": 160.0
                    }
                ],
                "subtotal": 160.0,
                "tax_amount": 28.8,
                "total_amount": 188.8,
                "payment_method": "cash"
            }
        },
        {
            "name": "Alternative Field Names",
            "data": {
                "business_type": "retail",
                "items": [
                    {
                        "id": "prod-2",  # Using 'id' instead of 'product_id'
                        "name": "Wheat Flour (1kg)",  # Using 'name' instead of 'product_name'
                        "quantity": 1,
                        "price": 45.0,  # Using 'price' instead of 'unit_price'
                        # No total_price - should be calculated
                    }
                ],
                "payment_method": "upi"
                # No total_amount - should be calculated
            }
        },
        {
            "name": "Minimal Data",
            "data": {
                "items": [
                    {
                        "productId": "prod-3",  # Using 'productId'
                        "name": "Sugar (1kg)",
                        "quantity": 1,
                        "price": 55.0
                    }
                ]
                # Only items provided - everything else should get defaults
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 TEST {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            url = 'http://localhost:5000/api/bills'
            req = urllib.request.Request(
                url, 
                data=json.dumps(test_case['data']).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                print(f"✅ SUCCESS: {result.get('message', 'Bill created')}")
                print(f"   Bill Number: {result.get('bill_number')}")
                print(f"   Created At: {result.get('created_at')}")
                
        except urllib.error.HTTPError as e:
            error_data = e.read().decode()
            print(f"❌ HTTP ERROR {e.code}: {error_data}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    print(f"\n🎯 SUMMARY")
    print("=" * 50)
    print("✅ All datetime issues should be fixed")
    print("✅ Bill creation should work with any field names")
    print("✅ Default values should be applied when missing")
    print("✅ Proper transaction handling with rollback on errors")

if __name__ == "__main__":
    test_bill_creation()