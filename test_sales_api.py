import requests
from datetime import datetime, timedelta

# Calculate date range
today = datetime.now().strftime('%Y-%m-%d')
thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

print(f"Testing API: /api/sales/all?from={thirty_days_ago}&to={today}&limit=500")

# Test the API
try:
    response = requests.get(f'http://localhost:5000/api/sales/all?from={thirty_days_ago}&to={today}&limit=500')
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nSales count: {len(data.get('sales', []))}")
        print(f"\nSummary: {data.get('summary', {})}")
        
        if data.get('sales'):
            print("\nFirst 3 sales:")
            for sale in data['sales'][:3]:
                print(f"  - {sale.get('bill_number')} | {sale.get('product_name')} | ₹{sale.get('total_price')} | {sale.get('sale_date')}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
