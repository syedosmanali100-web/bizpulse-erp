#!/usr/bin/env python3
"""
Test API endpoints directly using Flask test client
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app
import json

def test_api_endpoints():
    """Test API endpoints using Flask test client"""
    print("🚀 Testing API Endpoints")
    print("=" * 50)
    
    # Create test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Initialize database
    from modules.shared.database import init_db
    init_db()
    
    # Test data
    TEST_BARCODE = "9876543210987"
    test_product_data = {
        "name": "API Test Product",
        "price": 150.0,
        "cost": 120.0,
        "stock": 25,
        "category": "API Test",
        "barcode_data": TEST_BARCODE
    }
    
    print(f"\n🧪 Test 1: POST /api/products (Add product with barcode)")
    
    # Test 1: Add product via API
    response = client.post('/api/products', 
                          data=json.dumps(test_product_data),
                          content_type='application/json')
    
    print(f"📤 Status Code: {response.status_code}")
    print(f"📤 Response: {response.get_data(as_text=True)}")
    
    if response.status_code == 201:
        result = response.get_json()
        if result.get('success'):
            product_id = result['product']['id']
            print(f"✅ Product added via API: {product_id}")
        else:
            print(f"❌ API Error: {result.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False
    
    print(f"\n🧪 Test 2: GET /api/products/search/barcode/{TEST_BARCODE}")
    
    # Test 2: Search product by barcode via API
    response = client.get(f'/api/products/search/barcode/{TEST_BARCODE}')
    
    print(f"📤 Status Code: {response.status_code}")
    print(f"📤 Response: {response.get_data(as_text=True)}")
    
    if response.status_code == 200:
        result = response.get_json()
        if result.get('success') and result.get('product'):
            found_product = result['product']
            print(f"✅ Product found via API: {found_product['name']}")
        else:
            print(f"❌ Product not found: {result.get('message')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False
    
    print(f"\n🧪 Test 3: POST /api/bills (Create bill with barcode product)")
    
    # Test 3: Create bill via API
    bill_data = {
        "items": [
            {
                "product_id": found_product['id'],
                "product_name": found_product['name'],
                "quantity": 3,
                "unit_price": found_product['price'],
                "total_price": found_product['price'] * 3
            }
        ],
        "subtotal": found_product['price'] * 3,
        "tax_amount": 0,
        "discount_amount": 0,
        "total_amount": found_product['price'] * 3,
        "payment_method": "cash",
        "customer_name": "API Test Customer"
    }
    
    response = client.post('/api/bills',
                          data=json.dumps(bill_data),
                          content_type='application/json')
    
    print(f"📤 Status Code: {response.status_code}")
    print(f"📤 Response: {response.get_data(as_text=True)}")
    
    if response.status_code == 201:
        result = response.get_json()
        if result.get('success'):
            print(f"✅ Bill created via API: {result['bill_number']}")
        else:
            print(f"❌ Bill creation failed: {result.get('error')}")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False
    
    print(f"\n🧪 Test 4: GET /api/products (List all products)")
    
    # Test 4: List products to verify our test product exists
    response = client.get('/api/products')
    
    print(f"📤 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        products = response.get_json()
        print(f"📤 Found {len(products)} products")
        
        # Find our test product
        test_product = None
        for product in products:
            if product.get('barcode_data') == TEST_BARCODE:
                test_product = product
                break
        
        if test_product:
            print(f"✅ Test product found in list: {test_product['name']} (Stock: {test_product['stock']})")
            
            # Verify stock was reduced
            original_stock = test_product_data['stock']
            current_stock = test_product['stock']
            expected_stock = original_stock - 3  # We bought 3 items
            
            if current_stock == expected_stock:
                print(f"✅ Stock correctly reduced: {original_stock} → {current_stock}")
            else:
                print(f"❌ Stock reduction error: Expected {expected_stock}, got {current_stock}")
                return False
        else:
            print(f"❌ Test product not found in product list")
            return False
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎯 ALL API TESTS PASSED!")
    print("✅ Product API: WORKING")
    print("✅ Barcode Search API: WORKING")
    print("✅ Billing API: WORKING")
    print("✅ Stock Management: WORKING")
    
    return True

if __name__ == "__main__":
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"❌ API Test failed with error: {e}")
        import traceback
        traceback.print_exc()