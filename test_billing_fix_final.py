#!/usr/bin/env python3
"""
Test the fixed billing API with the exact data format from frontend
"""

import requests
import json

# Test data matching frontend format
test_bill_data = {
    "items": [
        {
            "id": "test-product-1",
            "name": "Test Product 1",
            "price": 100.0,
            "quantity": 2
        },
        {
            "id": "test-product-2", 
            "name": "Test Product 2",
            "price": 50.0,
            "quantity": 1
        }
    ],
    "subtotal": 250.0,
    "cgst": 22.5,
    "sgst": 22.5,
    "total": 295.0,
    "payment_method": "cash",
    "customer_name": "Test Customer",
    "customer_phone": "9876543210"
}

def test_billing_api():
    """Test the billing API with frontend data format"""
    
    print("🧪 Testing Billing API with Frontend Data Format")
    print("=" * 60)
    
    try:
        # Test POST request to create bill
        print("📤 Sending bill creation request...")
        print(f"Data: {json.dumps(test_bill_data, indent=2)}")
        
        response = requests.post(
            'http://localhost:5000/api/sales',
            json=test_bill_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Bill created successfully!")
            print(f"📋 Bill ID: {result.get('bill_id')}")
            print(f"📋 Bill Number: {result.get('bill_number')}")
            print(f"💰 Total Amount: ₹{result.get('total_amount')}")
            print(f"📦 Items Count: {result.get('items_count')}")
            print(f"⏰ Created At: {result.get('created_at')}")
            
            # Test GET request to verify bill was created
            print("\n🔍 Verifying bill creation with GET request...")
            get_response = requests.get('http://localhost:5000/api/sales?filter=today&limit=5')
            
            if get_response.status_code == 200:
                sales_data = get_response.json()
                print(f"✅ Found {len(sales_data.get('sales', []))} sales records")
                if sales_data.get('sales'):
                    latest_sale = sales_data['sales'][0]
                    print(f"📋 Latest Bill: {latest_sale.get('bill_number')}")
                    print(f"💰 Amount: ₹{latest_sale.get('total_price')}")
            else:
                print(f"❌ GET request failed: {get_response.status_code}")
                
        else:
            print(f"❌ Bill creation failed!")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed! Make sure the server is running on localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_billing_api()