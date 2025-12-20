#!/usr/bin/env python3
import urllib.request
import json

def test_bill_creation():
    print("🧪 TESTING BILL CREATION FIX")
    print("=" * 30)
    
    # Sample bill data (similar to what frontend sends)
    bill_data = {
        "business_type": "retail",
        "customer_id": None,
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
    
    try:
        # Test with complete data
        print("Test 1: Complete bill data")
        url = 'http://localhost:5000/api/bills'
        req = urllib.request.Request(url, 
                                   data=json.dumps(bill_data).encode('utf-8'),
                                   headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("✅ SUCCESS:", result.get('message', 'Bill created'))
            print("Bill Number:", result.get('bill_number'))
    
    except Exception as e:
        print("❌ ERROR:", str(e))
    
    # Test with missing total_amount (should auto-calculate)
    print("\nTest 2: Missing total_amount (auto-calculate)")
    bill_data_no_total = bill_data.copy()
    del bill_data_no_total['total_amount']
    
    try:
        req = urllib.request.Request(url, 
                                   data=json.dumps(bill_data_no_total).encode('utf-8'),
                                   headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("✅ SUCCESS:", result.get('message', 'Bill created'))
            print("Bill Number:", result.get('bill_number'))
    
    except Exception as e:
        print("❌ ERROR:", str(e))

if __name__ == "__main__":
    test_bill_creation()