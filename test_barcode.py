#!/usr/bin/env python3
"""
Test script to verify barcode functionality works end-to-end
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_BARCODE = "1234567890123"
TEST_PRODUCT = {
    "name": "Test Product for Barcode",
    "price": 100.0,
    "cost": 80.0,
    "stock": 50,
    "category": "Test",
    "barcode_data": TEST_BARCODE
}

def test_add_product_with_barcode():
    """Test adding a product with barcode"""
    print("🧪 Testing: Add Product with Barcode")
    
    url = f"{BASE_URL}/api/products"
    response = requests.post(url, json=TEST_PRODUCT)
    
    print(f"📡 Request URL: {url}")
    print(f"📤 Request Data: {json.dumps(TEST_PRODUCT, indent=2)}")
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Data: {response.text}")
    
    if response.status_code == 201:
        result = response.json()
        if result.get('success'):
            print(f"✅ Product added successfully with barcode: {result.get('product', {}).get('barcode')}")
            return result.get('product', {}).get('id')
        else:
            print(f"❌ Product add failed: {result.get('error')}")
            return None
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return None

def test_search_product_by_barcode():
    """Test searching product by barcode"""
    print("\n🧪 Testing: Search Product by Barcode")
    
    url = f"{BASE_URL}/api/products/search/barcode/{TEST_BARCODE}"
    response = requests.get(url)
    
    print(f"📡 Request URL: {url}")
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Data: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success') and result.get('product'):
            product = result['product']
            print(f"✅ Product found: {product.get('name')} (Barcode: {product.get('barcode_data')})")
            return product
        else:
            print(f"❌ Product not found: {result.get('message')}")
            return None
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return None

def test_create_bill_with_barcode_product():
    """Test creating a bill with the barcode product"""
    print("\n🧪 Testing: Create Bill with Barcode Product")
    
    # First, search for the product to get its details
    product = test_search_product_by_barcode()
    if not product:
        print("❌ Cannot test billing - product not found")
        return False
    
    # Create a bill with this product
    bill_data = {
        "items": [
            {
                "product_id": product['id'],
                "product_name": product['name'],
                "quantity": 2,
                "unit_price": product['price'],
                "total_price": product['price'] * 2
            }
        ],
        "subtotal": product['price'] * 2,
        "tax_amount": 0,
        "discount_amount": 0,
        "total_amount": product['price'] * 2,
        "payment_method": "cash",
        "customer_name": "Test Customer"
    }
    
    url = f"{BASE_URL}/api/bills"
    response = requests.post(url, json=bill_data)
    
    print(f"📡 Request URL: {url}")
    print(f"📤 Request Data: {json.dumps(bill_data, indent=2)}")
    print(f"📥 Response Status: {response.status_code}")
    print(f"📥 Response Data: {response.text}")
    
    if response.status_code == 201:
        result = response.json()
        if result.get('success'):
            print(f"✅ Bill created successfully: {result.get('bill_number')}")
            return True
        else:
            print(f"❌ Bill creation failed: {result.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False

def main():
    """Run all barcode tests"""
    print("🚀 Starting Barcode End-to-End Tests")
    print("=" * 50)
    
    try:
        # Test 1: Add product with barcode
        product_id = test_add_product_with_barcode()
        
        # Test 2: Search product by barcode
        if product_id:
            test_search_product_by_barcode()
        
        # Test 3: Create bill with barcode product
        test_create_bill_with_barcode_product()
        
        print("\n" + "=" * 50)
        print("🎯 Barcode Tests Completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()