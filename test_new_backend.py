"""
Test Script for New Production-Grade Billing Backend
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_create_bill():
    """Test creating a new bill"""
    print("🧪 Testing: Create Bill")
    
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
        "payment_method": "cash",
        "tax_amount": 0,
        "discount_amount": 0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/bills", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Bill creation successful!")
            return response.json().get('bill_id')
        else:
            print("❌ Bill creation failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_bills():
    """Test getting all bills"""
    print("\n🧪 Testing: Get Bills")
    
    try:
        response = requests.get(f"{BASE_URL}/api/bills")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Get bills successful!")
        else:
            print("❌ Get bills failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_invoice():
    """Test creating a new invoice"""
    print("\n🧪 Testing: Create Invoice")
    
    data = {
        "items": [
            {
                "product_id": "prod-2",
                "product_name": "Wheat Flour 1kg",
                "quantity": 1,
                "unit_price": 45.0
            }
        ],
        "total_amount": 45.0,
        "customer_id": "cust-2",
        "payment_method": "card"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/invoices", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Invoice creation successful!")
            return response.json().get('invoice_id')
        else:
            print("❌ Invoice creation failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_get_sales():
    """Test getting sales data"""
    print("\n🧪 Testing: Get Sales")
    
    try:
        response = requests.get(f"{BASE_URL}/api/sales?filter=today")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Get sales successful!")
        else:
            print("❌ Get sales failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_insufficient_stock():
    """Test insufficient stock scenario"""
    print("\n🧪 Testing: Insufficient Stock")
    
    data = {
        "items": [
            {
                "product_id": "prod-1",
                "product_name": "Rice 1kg",
                "quantity": 1000,  # Way more than available
                "unit_price": 80.0
            }
        ],
        "total_amount": 80000.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/bills", json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400 and "Insufficient stock" in response.json().get('message', ''):
            print("✅ Insufficient stock handling successful!")
        else:
            print("❌ Insufficient stock handling failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_delete_bill(bill_id):
    """Test deleting a bill"""
    if not bill_id:
        print("\n⏭️  Skipping delete test (no bill ID)")
        return
        
    print(f"\n🧪 Testing: Delete Bill {bill_id}")
    
    try:
        response = requests.delete(f"{BASE_URL}/api/bills/{bill_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Bill deletion successful!")
        else:
            print("❌ Bill deletion failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🚀 TESTING NEW PRODUCTION-GRADE BILLING BACKEND")
    print("=" * 60)
    
    # Test 1: Create bill
    bill_id = test_create_bill()
    
    # Test 2: Get bills
    test_get_bills()
    
    # Test 3: Create invoice
    invoice_id = test_create_invoice()
    
    # Test 4: Get sales
    test_get_sales()
    
    # Test 5: Insufficient stock
    test_insufficient_stock()
    
    # Test 6: Delete bill
    test_delete_bill(bill_id)
    
    print("\n" + "=" * 60)
    print("🎉 TESTING COMPLETE!")
    print("\nTo run these tests:")
    print("1. Start the server: python app.py")
    print("2. Run tests: python test_new_backend.py")

if __name__ == "__main__":
    main()