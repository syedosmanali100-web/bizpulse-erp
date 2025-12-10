from app import get_db_connection

def create_low_stock_scenarios():
    conn = get_db_connection()
    
    # Create some low stock scenarios for testing
    conn.execute('UPDATE products SET stock = 3 WHERE name LIKE "Rice%"')
    conn.execute('UPDATE products SET stock = 0 WHERE name LIKE "Dal%"')  
    conn.execute('UPDATE products SET stock = 2 WHERE name LIKE "Oil%"')
    conn.execute('UPDATE products SET stock = 8 WHERE name LIKE "Sugar%"')
    conn.commit()
    
    print('✅ Created low stock scenarios for testing')
    
    # Check the results
    low_stock = conn.execute('SELECT name, stock, min_stock FROM products WHERE stock <= min_stock').fetchall()
    print(f'Low stock items created: {len(low_stock)}')
    for item in low_stock:
        print(f'- {item[0]}: Stock={item[1]}, Min={item[2]}')
    
    conn.close()

if __name__ == "__main__":
    create_low_stock_scenarios()