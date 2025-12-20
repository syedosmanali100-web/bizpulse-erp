#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

def test_sales_summary():
    print("🔍 QUICK SALES FILTER TEST")
    print("=" * 30)
    
    # Use same logic as API
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Today: {today}")
    print(f"Yesterday: {yesterday}")
    
    conn = sqlite3.connect('billing.db')
    conn.row_factory = sqlite3.Row
    
    # Test today's sales
    today_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE DATE(created_at) = ?
    ''', (today,)).fetchone()
    
    # Test yesterday's sales
    yesterday_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE DATE(created_at) = ?
    ''', (yesterday,)).fetchone()
    
    # Test all time sales
    all_time_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills
    ''').fetchone()
    
    print(f"📊 TODAY: {today_sales['count']} bills, ₹{today_sales['total']}")
    print(f"📊 YESTERDAY: {yesterday_sales['count']} bills, ₹{yesterday_sales['total']}")
    print(f"📊 ALL TIME: {all_time_sales['count']} bills, ₹{all_time_sales['total']}")
    
    if yesterday_sales['count'] > 0 and all_time_sales['count'] > 0:
        print("✅ DATABASE QUERY WORKING!")
        print("✅ Issue might be in API response or frontend")
    else:
        print("❌ Database query issue")
    
    conn.close()

if __name__ == "__main__":
    test_sales_summary()