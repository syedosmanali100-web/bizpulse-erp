#!/usr/bin/env python3
"""
Test script to verify billing integration
Tests: Bill creation → Sales entry → Stock reduction
"""

import sqlite3
from datetime import datetime

def test_billing_integration():
    print("🧪 Testing Billing Integration")
    print("=" * 60)
    
    conn = sqlite3.connect('billing.db')
    conn.row_factory = sqlite3.Row
    
    # Test 1: Check if sales table exists
    print("\n📋 Test 1: Check Sales Table")
    try:
        result = conn.execute("SELECT COUNT(*) as count FROM sales").fetchone()
        print(f"✅ Sales table exists with {result['count']} entries")
    except Exception as e:
        print(f"❌ Sales table error: {e}")
    
    # Test 2: Check recent bills
    print("\n📋 Test 2: Check Recent Bills")
    try:
        bills = conn.execute("""
            SELECT id, bill_number, total_amount, created_at 
            FROM bills 
            ORDER BY created_at DESC 
            LIMIT 5
        """).fetchall()
        
        if bills:
            print(f"✅ Found {len(bills)} recent bills:")
            for bill in bills:
                print(f"   - {bill['bill_number']}: ₹{bill['total_amount']} ({bill['created_at']})")
        else:
            print("⚠️  No bills found")
    except Exception as e:
        print(f"❌ Bills query error: {e}")
    
    # Test 3: Check if sales entries match bills
    print("\n📋 Test 3: Check Sales Entries for Recent Bills")
    try:
        if bills:
            latest_bill = bills[0]
            sales = conn.execute("""
                SELECT * FROM sales WHERE bill_id = ?
            """, (latest_bill['id'],)).fetchall()
            
            if sales:
                print(f"✅ Found {len(sales)} sales entries for bill {latest_bill['bill_number']}")
                for sale in sales:
                    print(f"   - {sale['product_name']}: Qty {sale['quantity']} @ ₹{sale['unit_price']}")
            else:
                print(f"❌ No sales entries found for bill {latest_bill['bill_number']}")
                print("   This means sales integration is broken!")
    except Exception as e:
        print(f"❌ Sales query error: {e}")
    
    # Test 4: Check product stock
    print("\n📋 Test 4: Check Product Stock")
    try:
        products = conn.execute("""
            SELECT id, name, stock, min_stock 
            FROM products 
            ORDER BY stock ASC 
            LIMIT 5
        """).fetchall()
        
        if products:
            print(f"✅ Found {len(products)} products:")
            for product in products:
                status = "🔴 Low" if product['stock'] <= product['min_stock'] else "✅ OK"
                print(f"   {status} {product['name']}: Stock {product['stock']}")
        else:
            print("⚠️  No products found")
    except Exception as e:
        print(f"❌ Products query error: {e}")
    
    # Test 5: Check API endpoints availability
    print("\n📋 Test 5: Check Database Schema")
    try:
        # Check bills table columns
        bills_schema = conn.execute("PRAGMA table_info(bills)").fetchall()
        print(f"✅ Bills table has {len(bills_schema)} columns")
        
        # Check sales table columns
        sales_schema = conn.execute("PRAGMA table_info(sales)").fetchall()
        print(f"✅ Sales table has {len(sales_schema)} columns")
        
        # Check if required columns exist in sales
        sales_cols = [col['name'] for col in sales_schema]
        required_cols = ['bill_id', 'product_id', 'quantity', 'unit_price', 'total_price']
        missing = [col for col in required_cols if col not in sales_cols]
        
        if missing:
            print(f"❌ Missing columns in sales table: {missing}")
        else:
            print(f"✅ All required columns present in sales table")
            
    except Exception as e:
        print(f"❌ Schema check error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    # Count totals
    total_bills = conn.execute("SELECT COUNT(*) as count FROM bills").fetchone()['count']
    total_sales = conn.execute("SELECT COUNT(*) as count FROM sales").fetchone()['count']
    total_products = conn.execute("SELECT COUNT(*) as count FROM products").fetchone()['count']
    
    print(f"Total Bills: {total_bills}")
    print(f"Total Sales Entries: {total_sales}")
    print(f"Total Products: {total_products}")
    
    if total_bills > 0 and total_sales == 0:
        print("\n❌ ISSUE FOUND: Bills exist but no sales entries!")
        print("   This means the billing integration is broken.")
        print("   Solution: Check create_bill() function in app.py")
    elif total_bills > 0 and total_sales > 0:
        ratio = total_sales / total_bills
        print(f"\n✅ Sales/Bill Ratio: {ratio:.2f}")
        if ratio < 1:
            print("   ⚠️  Warning: Some bills may not have sales entries")
        else:
            print("   ✅ Integration looks good!")
    else:
        print("\n⚠️  No data to test. Create a bill first!")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🔧 Next Steps:")
    print("=" * 60)
    print("1. Start server: python app.py")
    print("2. Create a test bill in billing module")
    print("3. Check if it appears in:")
    print("   - Invoice module (/retail/invoices)")
    print("   - Sales module (/retail/sales)")
    print("4. Verify product stock decreased")
    print("\n✅ Test Complete!")

if __name__ == "__main__":
    test_billing_integration()
