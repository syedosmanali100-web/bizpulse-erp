#!/usr/bin/env python3
"""
Debug billing issue directly
"""

import sqlite3
import json
from datetime import datetime
import uuid

def generate_id():
    return str(uuid.uuid4())

def get_db_connection():
    conn = sqlite3.connect('billing.db')
    conn.row_factory = sqlite3.Row
    return conn

def test_billing_creation():
    """Test the exact billing logic"""
    
    print("🧪 Testing Billing Creation Logic")
    print("=" * 50)
    
    try:
        # Sample data exactly like frontend sends
        data = {
            'items': [
                {
                    'id': 'test-product-1',
                    'name': 'Test Product',
                    'price': 100.0,
                    'quantity': 1
                }
            ],
            'total': 118.0,
            'cgst': 9.0,
            'sgst': 9.0,
            'subtotal': 100.0,
            'payment_method': 'cash',
            'customer_name': 'Test Customer'
        }
        
        print("📥 Original data:", json.dumps(data, indent=2))
        
        # Step 1: Data mapping
        if data.get('total') and not data.get('total_amount'):
            data['total_amount'] = data['total']
            print("✅ Mapped 'total' to 'total_amount'")
        
        if not data.get('tax_amount'):
            cgst = data.get('cgst', 0)
            sgst = data.get('sgst', 0)
            data['tax_amount'] = cgst + sgst
            print(f"✅ Mapped cgst({cgst}) + sgst({sgst}) = tax_amount({data['tax_amount']})")
        
        # Step 2: Test datetime
        current_time = datetime.now()
        print(f"✅ Current time: {current_time}")
        
        # Step 3: Test database connection
        conn = get_db_connection()
        print("✅ Database connection successful")
        
        # Step 4: Generate IDs
        bill_id = generate_id()
        bill_number = f"BILL-{current_time.strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"✅ Generated bill_id: {bill_id}")
        print(f"✅ Generated bill_number: {bill_number}")
        
        # Step 5: Test transaction
        conn.execute('BEGIN TRANSACTION')
        print("✅ Transaction started")
        
        # Step 6: Test bill insertion
        bill_timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        conn.execute('''
            INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, discount_amount, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bill_id, bill_number, None, 'retail',
            data.get('subtotal', 0), data.get('tax_amount', 0), 
            data.get('discount_amount', 0), data['total_amount'], 'completed', bill_timestamp
        ))
        print("✅ Bill record inserted")
        
        # Step 7: Test item processing
        for item in data['items']:
            product_id = item.get('product_id') or item.get('id') or 'default-product'
            product_name = item.get('product_name') or item.get('name') or 'Unknown Product'
            quantity = item.get('quantity', 1)
            unit_price = item.get('unit_price') or item.get('price', 0)
            total_price = item.get('total_price') or (unit_price * quantity)
            
            print(f"✅ Processing item: {product_name} (ID: {product_id})")
            print(f"   Quantity: {quantity}, Unit Price: {unit_price}, Total: {total_price}")
            
            # Create bill item
            item_id = generate_id()
            conn.execute('''
                INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price, tax_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, bill_id, product_id, product_name,
                quantity, unit_price, total_price, 18
            ))
            print(f"✅ Bill item inserted with ID: {item_id}")
        
        # Step 8: Commit transaction
        conn.commit()
        print("✅ Transaction committed successfully")
        
        conn.close()
        print("✅ Database connection closed")
        
        print("\n🎉 BILLING CREATION TEST PASSED!")
        print(f"📋 Bill Number: {bill_number}")
        print(f"💰 Total Amount: ₹{data['total_amount']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ BILLING CREATION FAILED!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_billing_creation()
    if success:
        print("\n✅ Billing logic is working correctly!")
    else:
        print("\n❌ Billing logic has issues that need fixing!")