#!/usr/bin/env python3
import urllib.request
import json

def test_live_bill_creation():
    print("🌐 TESTING LIVE SITE BILL CREATION")
    print("=" * 40)
    
    # Test data similar to what frontend sends
    bill_data = {
        "business_type": "retail",
        "items": [
            {
                "product_id": "prod-1",
                "product_name": "Rice (1kg)",
                "quantity": 1,
                "unit_price": 80.0,
                "total_price": 80.0
            }
        ],
        "subtotal": 80.0,
        "tax_amount": 14.4,
        "total_amount": 94.4,
        "payment_method": "cash"
    }
    
    try:
        url = 'https://www.bizpulse24.com/api/bills'
        req = urllib.request.Request(url, 
                                   data=json.dumps(bill_data).encode('utf-8'),
                                   headers={
                                       'Content-Type': 'application/json',
                                       'Cookie': 'session=test'  # You might need actual session
                                   })
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("✅ SUCCESS:", result)
    
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        print("❌ HTTP ERROR:", e.code)
        print("Error details:", error_data)
        
        if "Invalid total amount" in error_data:
            print("🔍 CONFIRMED: Live site still has old validation code")
            print("🚀 SOLUTION: Need to redeploy the fix")
    
    except Exception as e:
        print("❌ ERROR:", str(e))

if __name__ == "__main__":
    test_live_bill_creation()