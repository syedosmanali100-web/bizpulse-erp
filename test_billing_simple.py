#!/usr/bin/env python3
"""
Simple test for billing API without external dependencies
"""

import json
import urllib.request
import urllib.parse

# Test data matching frontend format
test_bill_data = {
    "items": [
        {
            "id": "test-product-1",
            "name": "Test Product 1", 
            "price": 100.0,
            "quantity": 2
        }
    ],
    "subtotal": 200.0,
    "cgst": 18.0,
    "sgst": 18.0,
    "total": 236.0,
    "payment_method": "cash",
    "customer_name": "Test Customer"
}

def test_billing():
    """Test billing API"""
    try:
        # Prepare request
        url = 'http://localhost:5000/api/sales'
        data = json.dumps(test_bill_data).encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        print("🧪 Testing Billing API...")
        print(f"📤 Sending: {json.dumps(test_bill_data, indent=2)}")
        
        # Send request
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Success! Status: {response.status}")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            print(f"Error details: {error_data}")
        except:
            print(f"Raw error: {e.read()}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_billing()