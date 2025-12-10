import sqlite3

conn = sqlite3.connect('billing.db')
cursor = conn.cursor()

# Check sales count
cursor.execute('SELECT COUNT(*) FROM sales')
count = cursor.fetchone()[0]
print(f'Total sales entries: {count}')

# Check recent sales
cursor.execute('SELECT id, bill_number, product_name, quantity, total_price, sale_date FROM sales ORDER BY created_at DESC LIMIT 5')
rows = cursor.fetchall()
print('\nRecent sales:')
for row in rows:
    print(row)

# Check recent bills
cursor.execute('SELECT COUNT(*) FROM bills')
bill_count = cursor.fetchone()[0]
print(f'\nTotal bills: {bill_count}')

cursor.execute('SELECT id, bill_number, total_amount, created_at FROM bills ORDER BY created_at DESC LIMIT 5')
bills = cursor.fetchall()
print('\nRecent bills:')
for bill in bills:
    print(bill)

conn.close()
