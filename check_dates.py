from datetime import datetime, timedelta

today = datetime.now()
print(f'Today: {today.strftime("%Y-%m-%d")}')

thirty_days_ago = today - timedelta(days=30)
print(f'30 days ago: {thirty_days_ago.strftime("%Y-%m-%d")}')

# Check sales in this range
import sqlite3
conn = sqlite3.connect('billing.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT COUNT(*) FROM sales 
    WHERE sale_date BETWEEN ? AND ?
''', (thirty_days_ago.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")))

count = cursor.fetchone()[0]
print(f'\nSales in last 30 days: {count}')

# Check all sales dates
cursor.execute('SELECT DISTINCT sale_date FROM sales ORDER BY sale_date DESC LIMIT 10')
dates = cursor.fetchall()
print('\nRecent sale dates:')
for date in dates:
    print(date[0])

conn.close()
