import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('billing.db')
conn.row_factory = sqlite3.Row

today = datetime.now().strftime('%Y-%m-%d')
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

print(f'Querying from {thirty_days_ago} to {today}')

query = '''
    SELECT 
        s.*,
        p.cost as purchase_price,
        p.price as selling_price
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.id
    WHERE s.sale_date BETWEEN ? AND ?
    ORDER BY s.created_at DESC
    LIMIT 10
'''

sales = conn.execute(query, (thirty_days_ago, today)).fetchall()

print(f'\nFound {len(sales)} sales')
print('\nFirst 3 sales:')
for sale in sales[:3]:
    s = dict(sale)
    print(f"  Bill: {s['bill_number']}, Date: {s['sale_date']}, Product: {s['product_name']}, Total: {s['total_price']}")
    print(f"    Purchase Price: {s['purchase_price']}, Selling Price: {s['selling_price']}")

# Test summary
summary_query = '''
    SELECT 
        COUNT(DISTINCT bill_id) as total_bills,
        COUNT(*) as total_items,
        SUM(total_price) as total_sales
    FROM sales
    WHERE sale_date BETWEEN ? AND ?
'''

summary = conn.execute(summary_query, (thirty_days_ago, today)).fetchone()
print(f'\nSummary:')
print(f"  Total Bills: {summary['total_bills']}")
print(f"  Total Items: {summary['total_items']}")
print(f"  Total Sales: ₹{summary['total_sales']}")

conn.close()
