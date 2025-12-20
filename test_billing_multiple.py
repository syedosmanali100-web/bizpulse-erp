#!/usr/bin/env python3
"""
Test billing with multiple items and scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import json

def test_multiple_scenarios():
    """Test different billing scenarios"""
    
    print("🧪 Testing Multiple Billing Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Single Item Bill",
            "data": {
                "items": [{"id": "prod-1", "name": "Product 1", "price": 50.0, "quantity": 2}],
                "subtotal": 100.0,
                "cgst": 9.0,
                "sgst": 9.0,
                "total": 118.0,
                "payment_method": "cash",
                "customer_name": "Customer A"
            }
        },
        {
            "name": "Multiple Items Bill",
            "data": {
                "items": [
                    {"id": "prod-1", "name": "Product 1", "price": 100.0, "quantity": 1},
                    {"id": "prod-2", "name": "Product 2", "price": 200.0, "quantity": 2}
                ],
                "subtotal": 500.0,
                "cgst": 45.0,
                "sgst": 45.0,
                "total": 590.0,
                "payment_method": "upi",
                "customer_name": "Customer B",
                "customer_phone": "9876543210"
            }
        },
        {
            "name": "Walk-in Customer",
            "data": {
                "items": [{"id": "prod-3", "name": "Product 3", "price": 25.0, "quantity": 4}],
                "subtotal": 100.0,
                "cgst": 9.0,
                "sgst": 9.0,
                "total": 118.0,
                "payment_method": "card"
            }
        }
    ]
    
    success_count = 0
    
    with app.test_client() as client:
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print("-" * 30)
            
            try:
                response = client.post(
                    '/api/sales',
                    data=json.dumps(scenario['data']),
                    content_type='application/json'
                )
                
                if response.status_code == 201:
                    result = response.get_json()
                    print(f"✅ SUCCESS!")
                    print(f"   Bill Number: {result.get('bill_number')}")
                    print(f"   Total: ₹{result.get('total_amount')}")
                    print(f"   Items: {result.get('items_count')}")
                    success_count += 1
                else:
                    print(f"❌ FAILED! Status: {response.status_code}")
                    try:
                        error = response.get_json()
                        print(f"   Error: {error.get('error')}")
                    except:
                        print(f"   Raw: {response.get_data(as_text=True)}")
                        
            except Exception as e:
                print(f"❌ EXCEPTION: {str(e)}")
    
    print(f"\n📊 Results: {success_count}/{len(scenarios)} tests passed")
    return success_count == len(scenarios)

if __name__ == "__main__":
    success = test_multiple_scenarios()
    if success:
        print("\n🎉 All billing scenarios working perfectly!")
    else:
        print("\n💥 Some billing scenarios failed!")