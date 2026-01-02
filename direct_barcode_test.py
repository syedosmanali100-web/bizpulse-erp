#!/usr/bin/env python3
"""
Direct test of barcode functionality without running the server
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from modules.shared.database import init_db, get_db_connection
from modules.products.service import ProductsService
from modules.billing.service import BillingService

def test_barcode_functionality():
    """Test barcode functionality directly"""
    print("🚀 Testing Barcode Functionality Directly")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    print("✅ Database initialized")
    
    # Initialize services
    products_service = ProductsService()
    billing_service = BillingService()
    
    # Test data
    TEST_BARCODE = "1234567890123"
    test_product_data = {
        "name": "Test Product for Barcode",
        "price": 100.0,
        "cost": 80.0,
        "stock": 50,
        "category": "Test",
        "barcode_data": TEST_BARCODE
    }
    
    print(f"\n🧪 Test 1: Adding product with barcode '{TEST_BARCODE}'")
    
    # Test 1: Add product with barcode
    result = products_service.add_product(test_product_data)
    print(f"📤 Add Product Result: {result}")
    
    if not result.get('success'):
        print(f"❌ Failed to add product: {result.get('error')}")
        return False
    
    product_id = result['product']['id']
    print(f"✅ Product added successfully with ID: {product_id}")
    
    print(f"\n🧪 Test 2: Searching product by barcode '{TEST_BARCODE}'")
    
    # Test 2: Search product by barcode
    search_result = products_service.search_product_by_barcode(TEST_BARCODE)
    print(f"📤 Search Result: {search_result}")
    
    if not search_result.get('success'):
        print(f"❌ Failed to find product by barcode: {search_result.get('message')}")
        return False
    
    found_product = search_result['product']
    print(f"✅ Product found: {found_product['name']} (Barcode: {found_product['barcode_data']})")
    
    print(f"\n🧪 Test 3: Creating bill with barcode product")
    
    # Test 3: Create bill with the product
    bill_data = {
        "items": [
            {
                "product_id": found_product['id'],
                "product_name": found_product['name'],
                "quantity": 2,
                "unit_price": found_product['price'],
                "total_price": found_product['price'] * 2
            }
        ],
        "subtotal": found_product['price'] * 2,
        "tax_amount": 0,
        "discount_amount": 0,
        "total_amount": found_product['price'] * 2,
        "payment_method": "cash",
        "customer_name": "Test Customer"
    }
    
    bill_result = billing_service.create_bill(bill_data)
    print(f"📤 Bill Creation Result: {bill_result}")
    
    if not bill_result.get('success'):
        print(f"❌ Failed to create bill: {bill_result.get('error')}")
        return False
    
    print(f"✅ Bill created successfully: {bill_result['bill_number']}")
    
    print(f"\n🧪 Test 4: Verifying stock reduction")
    
    # Test 4: Verify stock was reduced
    updated_search = products_service.search_product_by_barcode(TEST_BARCODE)
    if updated_search.get('success'):
        updated_product = updated_search['product']
        original_stock = test_product_data['stock']
        current_stock = updated_product['stock']
        expected_stock = original_stock - 2  # We bought 2 items
        
        print(f"📊 Stock Check:")
        print(f"   Original Stock: {original_stock}")
        print(f"   Current Stock: {current_stock}")
        print(f"   Expected Stock: {expected_stock}")
        
        if current_stock == expected_stock:
            print("✅ Stock reduction is correct!")
        else:
            print(f"❌ Stock reduction is incorrect! Expected {expected_stock}, got {current_stock}")
            return False
    
    print("\n" + "=" * 50)
    print("🎯 ALL BARCODE TESTS PASSED!")
    print("✅ Add Product with Barcode: WORKING")
    print("✅ Search Product by Barcode: WORKING") 
    print("✅ Create Bill with Barcode Product: WORKING")
    print("✅ Stock Management: WORKING")
    
    return True

def test_database_schema():
    """Test that database has all required columns"""
    print("\n🧪 Testing Database Schema")
    
    conn = get_db_connection()
    
    # Test bills table schema
    bills_schema = conn.execute("PRAGMA table_info(bills)").fetchall()
    bills_columns = [col[1] for col in bills_schema]
    print(f"📊 Bills table columns: {bills_columns}")
    
    required_bills_columns = ['customer_name']
    for col in required_bills_columns:
        if col in bills_columns:
            print(f"✅ Bills table has '{col}' column")
        else:
            print(f"❌ Bills table missing '{col}' column")
    
    # Test sales table schema
    sales_schema = conn.execute("PRAGMA table_info(sales)").fetchall()
    sales_columns = [col[1] for col in sales_schema]
    print(f"📊 Sales table columns: {sales_columns}")
    
    required_sales_columns = ['balance_due', 'paid_amount']
    for col in required_sales_columns:
        if col in sales_columns:
            print(f"✅ Sales table has '{col}' column")
        else:
            print(f"❌ Sales table missing '{col}' column")
    
    conn.close()

if __name__ == "__main__":
    try:
        test_database_schema()
        test_barcode_functionality()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()