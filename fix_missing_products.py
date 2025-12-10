import sqlite3

conn = sqlite3.connect('billing.db')
cursor = conn.cursor()

# Check if prod-* products exist
existing = cursor.execute("SELECT id FROM products WHERE id LIKE 'prod-%'").fetchall()
print(f"Found {len(existing)} products with prod- IDs")

if len(existing) == 0:
    print("\nAdding missing sample products...")
    
    # Sample products with proper cost and price
    sample_products = [
        ('prod-1', 'P001', 'Rice (1kg)', 'Flour & Grains', 80.0, 70.0, 100, 10, 'kg', 'retail'),
        ('prod-2', 'P002', 'Wheat Flour (1kg)', 'Flour & Grains', 45.0, 40.0, 50, 5, 'kg', 'retail'),
        ('prod-3', 'P003', 'Sugar (1kg)', 'Groceries', 55.0, 50.0, 30, 5, 'kg', 'retail'),
        ('prod-4', 'P004', 'Tea Powder (250g)', 'Tea & Coffee', 120.0, 100.0, 25, 3, 'packet', 'retail'),
        ('prod-5', 'P005', 'Cooking Oil (1L)', 'Groceries', 150.0, 140.0, 20, 2, 'liter', 'retail'),
        ('prod-6', 'P006', 'Milk (1L)', 'Dairy', 60.0, 55.0, 15, 2, 'liter', 'retail'),
        ('prod-7', 'P007', 'Bread', 'Bakery', 25.0, 20.0, 40, 5, 'piece', 'retail'),
        ('prod-8', 'P008', 'Eggs (12 pcs)', 'Dairy', 84.0, 75.0, 30, 3, 'dozen', 'retail'),
        ('prod-9', 'P009', 'Onions (1kg)', 'Vegetables', 35.0, 30.0, 50, 5, 'kg', 'retail'),
        ('prod-10', 'P010', 'Potatoes (1kg)', 'Vegetables', 25.0, 20.0, 60, 10, 'kg', 'retail'),
        ('prod-11', 'P011', 'Biscuits', 'Biscuits', 30.0, 25.0, 40, 5, 'packet', 'retail'),
        ('prod-12', 'P012', 'Namkeen', 'Namkeen', 40.0, 35.0, 30, 5, 'packet', 'retail'),
    ]
    
    for product in sample_products:
        try:
            cursor.execute('''
                INSERT INTO products (id, code, name, category, price, cost, stock, min_stock, unit, business_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
            print(f"  ✅ Added: {product[2]} (ID: {product[0]}, Cost: ₹{product[5]}, Price: ₹{product[4]})")
        except sqlite3.IntegrityError as e:
            print(f"  ⚠️  Skipped {product[2]}: {e}")
    
    conn.commit()
    print("\n✅ Products added successfully!")
else:
    print("\nUpdating existing prod-* products with cost/price...")
    
    updates = [
        ('prod-1', 70.0, 80.0),
        ('prod-2', 40.0, 45.0),
        ('prod-3', 50.0, 55.0),
        ('prod-4', 100.0, 120.0),
        ('prod-5', 140.0, 150.0),
        ('prod-6', 55.0, 60.0),
        ('prod-7', 20.0, 25.0),
        ('prod-8', 75.0, 84.0),
        ('prod-9', 30.0, 35.0),
        ('prod-10', 20.0, 25.0),
    ]
    
    for prod_id, cost, price in updates:
        cursor.execute('UPDATE products SET cost = ?, price = ? WHERE id = ?', (cost, price, prod_id))
        print(f"  ✅ Updated: {prod_id} (Cost: ₹{cost}, Price: ₹{price})")
    
    conn.commit()
    print("\n✅ Products updated successfully!")

# Verify
print("\nVerifying products:")
products = cursor.execute("SELECT id, name, cost, price FROM products WHERE id LIKE 'prod-%' ORDER BY id").fetchall()
for p in products:
    print(f"  {p[0]}: {p[1]} - Cost: ₹{p[2]}, Price: ₹{p[3]}")

conn.close()
