#!/usr/bin/env python3
"""
Final test of date filters after fixing the frontend
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_date_filters_final():
    """Test all date filters after the fix"""
    
    print("🧪 Testing Date Filters After Fix")
    print("=" * 50)
    
    with app.test_client() as client:
        
        filters_to_test = [
            ('today', 'Today Filter'),
            ('yesterday', 'Yesterday Filter'),
            ('week', 'This Week Filter'),
            ('month', 'This Month Filter'),
            ('all', 'All Data Filter')
        ]
        
        for filter_value, filter_name in filters_to_test:
            print(f"\n📋 Testing {filter_name}...")
            
            response = client.get(f'/api/sales/all?filter={filter_value}')
            
            if response.status_code == 200:
                data = response.get_json()
                
                if data.get('success'):
                    sales_count = len(data.get('sales', []))
                    summary = data.get('summary', {})
                    total_sales = summary.get('total_sales', 0)
                    total_bills = summary.get('total_bills', 0)
                    
                    print(f"✅ {filter_name}: Working")
                    print(f"   📊 Sales Records: {sales_count}")
                    print(f"   💰 Total Sales: ₹{total_sales}")
                    print(f"   📋 Total Bills: {total_bills}")
                    
                    # Show sample data
                    if sales_count > 0:
                        sample_sales = data['sales'][:3]
                        print(f"   📝 Sample Records:")
                        for i, sale in enumerate(sample_sales, 1):
                            bill_num = sale.get('bill_number', 'N/A')
                            product = sale.get('product_name', 'N/A')
                            amount = sale.get('total_amount', 0)
                            date = sale.get('date', sale.get('created_at', 'N/A'))
                            print(f"      {i}. {bill_num} - {product} - ₹{amount} - {date}")
                    
                else:
                    print(f"❌ {filter_name}: API returned success=false")
                    
            else:
                print(f"❌ {filter_name}: HTTP {response.status_code}")

def test_sales_page():
    """Test if sales page loads correctly"""
    
    print(f"\n🧪 Testing Sales Page")
    print("=" * 30)
    
    with app.test_client() as client:
        response = client.get('/retail/sales')
        
        if response.status_code == 200:
            print("✅ Sales page loads successfully")
            
            content = response.get_data(as_text=True)
            
            # Check for important elements
            checks = [
                ('filterSales()', 'Filter function'),
                ('loadSales()', 'Load function'),
                ('currentFilters', 'Filter state'),
                ('dateRange', 'Date filter dropdown'),
                ('salesTable', 'Sales table')
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    print(f"   ✅ {description}: Found")
                else:
                    print(f"   ❌ {description}: Missing")
                    
        else:
            print(f"❌ Sales page failed to load: {response.status_code}")

if __name__ == "__main__":
    test_date_filters_final()
    test_sales_page()
    
    print(f"\n🎉 Date Filter Testing Complete!")
    print(f"\n📋 Summary:")
    print(f"- Fixed duplicate filterSales() functions")
    print(f"- Removed invalid sales records with None values")
    print(f"- Enhanced renderSales() to filter out invalid data")
    print(f"- All date filters should now work correctly")
    print(f"\n🌐 Test the sales module at:")
    print(f"- Local: http://localhost:5000/retail/sales")
    print(f"- Production: https://bizpulse24.com/retail/sales")