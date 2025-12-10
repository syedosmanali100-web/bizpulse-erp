import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('billing.db')
conn.row_factory = sqlite3.Row

# Get date range
today = datetime.now().strftime('%Y-%m-%d')
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

print(f"Checking sales from {thirty_days_ago} to {today}")

# Same query as API
query = '''
    SELECT 
        s.*,
        p.stock as current_stock,
        p.min_stock,
        p.cost as purchase_price,
        p.price as selling_price
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.id
    WHERE s.sale_date BETWEEN ? AND ?
    ORDER BY s.created_at DESC LIMIT 500
'''

cursor = conn.execute(query, (thirty_days_ago, today))
sales = cursor.fetchall()

print(f"\nTotal sales found: {len(sales)}")

if sales:
    print("\nFirst 5 sales:")
    for i, sale in enumerate(sales[:5], 1):
        print(f"{i}. Bill: {sale['bill_number']} | Product: {sale['product_name']} | Qty: {sale['quantity']} | Price: ₹{sale['unit_price']} | Total: ₹{sale['total_price']} | Date: {sale['sale_date']}")

# Check summary
summary_query = '''
    SELECT 
        COUNT(DISTINCT bill_id) as total_bills,
        COUNT(*) as total_items,
        SUM(quantity) as total_quantity,
        SUM(total_price) as total_sales,
        SUM(tax_amount) as total_tax,
        SUM(discount_amount) as total_discount,
        AVG(total_price) as avg_sale_value
    FROM sales
    WHERE sale_date BETWEEN ? AND ?
'''

cursor = conn.execute(summary_query, (thirty_days_ago, today))
summary = cursor.fetchone()

print(f"\nSummary:")
print(f"  Total Bills: {summary['total_bills']}")
print(f"  Total Items: {summary['total_items']}")
print(f"  Total Sales: ₹{summary['total_sales']}")
print(f"  Avg Sale: ₹{summary['avg_sale_value']:.2f}")

conn.close()
