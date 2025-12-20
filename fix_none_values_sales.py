#!/usr/bin/env python3
"""
Fix None values in sales data that are causing display issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_db_connection

def fix_none_values_in_sales():
    """Fix None values in sales data"""
    
    print("🔧 Fixing None Values in Sales Data")
    print("=" * 50)
    
    conn = get_db_connection()
    
    # Find sales with None values
    sales_with_none = conn.execute('''
        SELECT s.id, s.bill_id, s.bill_number, s.product_name, s.total_price,
               bi.product_name as correct_name, bi.total_price as correct_price
        FROM sales s
        LEFT JOIN bill_items bi ON s.bill_id = bi.bill_id
        WHERE s.product_name IS NULL OR s.total_price IS NULL 
           OR s.product_name = 'None' OR s.total_price = 'None'
    ''').fetchall()
    
    if not sales_with_none:
        print("✅ No None values found in sales data")
        conn.close()
        return
    
    print(f"Found {len(sales_with_none)} sales records with None values")
    
    try:
        conn.execute('BEGIN TRANSACTION')
        
        fixed_count = 0
        deleted_count = 0
        
        for sale in sales_with_none:
            if sale['correct_name'] and sale['correct_price']:
                # Fix with correct values
                conn.execute('''
                    UPDATE sales 
                    SET product_name = ?, total_price = ?
                    WHERE id = ?
                ''', (sale['correct_name'], sale['correct_price'], sale['id']))
                
                print(f"✅ Fixed: {sale['bill_number']} - {sale['correct_name']} - ₹{sale['correct_price']}")
                fixed_count += 1
                
            else:
                # Delete invalid records that can't be fixed
                conn.execute('DELETE FROM sales WHERE id = ?', (sale['id'],))
                print(f"🗑️ Deleted invalid record: {sale['bill_number']} - {sale['id'][:8]}...")
                deleted_count += 1
        
        conn.commit()
        print(f"\n🎉 Successfully fixed {fixed_count} records and deleted {deleted_count} invalid records")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to fix None values: {str(e)}")
    
    conn.close()

def verify_sales_data():
    """Verify sales data after fix"""
    
    print(f"\n🔍 Verifying Sales Data After Fix")
    print("=" * 40)
    
    conn = get_db_connection()
    
    # Check for remaining None values
    none_count = conn.execute('''
        SELECT COUNT(*) as count FROM sales 
        WHERE product_name IS NULL OR total_price IS NULL 
           OR product_name = 'None' OR total_price = 'None'
    ''').fetchone()['count']
    
    print(f"Remaining None values: {none_count}")
    
    # Check today's data
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    today_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_price), 0) as total
        FROM sales 
        WHERE DATE(created_at) = ? AND total_price IS NOT NULL AND total_price != 'None'
    ''', (today,)).fetchone()
    
    print(f"Today's valid sales: {today_sales['count']} records, ₹{today_sales['total']} total")
    
    # Test API response
    from app import app
    with app.test_client() as client:
        response = client.get('/api/sales/all?filter=today')
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                api_count = len(data.get('sales', []))
                api_total = data.get('summary', {}).get('total_sales', 0)
                print(f"API response: {api_count} records, ₹{api_total} total")
            else:
                print("❌ API returned success=false")
        else:
            print(f"❌ API failed: {response.status_code}")
    
    conn.close()

if __name__ == "__main__":
    fix_none_values_in_sales()
    verify_sales_data()