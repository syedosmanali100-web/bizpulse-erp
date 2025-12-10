import sqlite3

conn = sqlite3.connect('billing.db')
cursor = conn.cursor()

print("All products:")
products = cursor.execute('SELECT id, name, cost, price FROM products ORDER BY id').fetchall()
for p in products:
    print(f"  ID: {p[0]}, Name: {p[1]}, Cost: {p[2]}, Price: {p[3]}")

print("\nProduct IDs used in recent sales:")
sales = cursor.execute('SELECT DISTINCT product_id, product_name FROM sales ORDER BY created_at DESC LIMIT 10').fetchall()
for s in sales:
    print(f"  ID: {s[0]}, Name: {s[1]}")
    # Check if this product exists
    product = cursor.execute('SELECT cost, price FROM products WHERE id = ?', (s[0],)).fetchone()
    if product:
        print(f"    -> Found in products: Cost={product[0]}, Price={product[1]}")
    else:
        print(f"    -> NOT FOUND in products table!")

conn.close()
