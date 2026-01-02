#!/usr/bin/env python3
"""
Add sample products with barcodes for speed testing
"""

import sqlite3
import uuid
from datetime import datetime

def add_sample_products():
    """Add sample products with barcodes for testing"""
    
    conn = sqlite3.connect('billing.db')
    cursor = conn.cursor()
    
    # Sample products with barcodes
    sample_products = [
        {
            'name': 'Rice (1kg)',
            'category': 'Groceries',
            'price': 80.0,
            'cost': 70.0,
            'stock': 100,
            'barcode': '1234567890123'
        },
        {
            'name': 'Wheat Flour (1kg)', 
            'category': 'Groceries',
            'price': 45.0,
            'cost': 40.0,
            'stock': 50,
            'barcode': '9876543210987'
        },
        {
            'name': 'Sugar (1kg)',
            'category': 'Groceries', 
            'price': 55.0,
            'cost': 50.0,
            'stock': 30,
            'barcode': '1111111111111'
        },
        {
            'name': 'Tea Powder (250g)',
            'category': 'Beverages',
            'price': 120.0,
            'cost': 100.0,
            'stock': 25,
            'barcode': '2222222222222'
        },
        {
            'name': 'Cooking Oil (1L)',
            'category': 'Groceries',
            'price': 150.0,
            'cost': 140.0,
            'stock': 20,
            'barcode': '3333333333333'
        }
    ]
    
    print("🔧 Adding sample products with barcodes...")
    
    for product in sample_products:
        # Check if barcode already exists
        existing = cursor.execute("SELECT id FROM products WHERE barcode_data = ?", (product['barcode'],)).fetchone()
        
        if existing:
            print(f"⚠️ Product with barcode {product['barcode']} already exists")
            continue
        
        # Generate product ID and code
        product_id = str(uuid.uuid4())
        product_code = f"P{datetime.now().strftime('%Y%m%d%H%M%S')}{product['barcode'][-3:]}"
        
        # Insert product
        cursor.execute("""INSERT INTO products (
                id, code, name, category, price, cost, stock, min_stock, 
                unit, business_type, barcode_data, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            product_id,
            product_code,
            product['name'],
            product['category'],
            product['price'],
            product['cost'],
            product['stock'],
            5,  # min_stock
            'piece',
            'retail',
            product['barcode'],
            1,  # is_active
            datetime.now().isoformat()
        ))
        
        print(f"✅ Added: {product['name']} (Barcode: {product['barcode']})")
    
    conn.commit()
    conn.close()
    
    print()
    print("🎯 Sample products added successfully!")
    print("🚀 Ready for barcode speed testing!")
    print()
    print("Test barcodes:")
    for product in sample_products:
        print(f"  - {product['barcode']} → {product['name']}")

if __name__ == "__main__":
    add_sample_products()