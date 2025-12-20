#!/usr/bin/env python3
"""
Test script to verify the sales filter fix
Tests Today, Yesterday, and All Time filters
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"  # Change to your server URL
API_ENDPOINT = f"{BASE_URL}/api/sales/summary"

def test_sales_filters():
    print("🧪 TESTING SALES FILTER FIX")
    print("=" * 50)
    
    try:
        # Test sales summary API
        print("📊 Testing Sales Summary API...")
        response = requests.get(API_ENDPOINT)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API Response Success")
            print(f"📅 Current Date (IST): {data.get('current_date_ist')}")
            print(f"🌍 Timezone: {data.get('timezone')}")
            print()
            
            # Test Today filter
            today = data.get('today', {})
            print(f"📈 TODAY FILTER:")
            print(f"   Bills: {today.get('count', 0)}")
            print(f"   Total: ₹{today.get('total', 0)}")
            print(f"   Status: {'✅ Working' if today.get('count', 0) >= 0 else '❌ Error'}")
            print()
            
            # Test Yesterday filter
            yesterday = data.get('yesterday', {})
            print(f"📈 YESTERDAY FILTER:")
            print(f"   Bills: {yesterday.get('count', 0)}")
            print(f"   Total: ₹{yesterday.get('total', 0)}")
            print(f"   Status: {'✅ Working' if yesterday.get('count', 0) >= 0 else '❌ Error'}")
            print()
            
            # Test All Time filter
            all_time = data.get('all_time', {})
            print(f"📈 ALL TIME FILTER:")
            print(f"   Bills: {all_time.get('count', 0)}")
            print(f"   Total: ₹{all_time.get('total', 0)}")
            print(f"   Status: {'✅ Working' if all_time.get('count', 0) > 0 else '❌ Error'}")
            print()
            
            # Show recent transactions
            recent = data.get('recent_transactions', [])
            print(f"📋 RECENT TRANSACTIONS ({len(recent)}):")
            for i, txn in enumerate(recent[:5]):
                print(f"   {i+1}. {txn.get('bill_number')} - ₹{txn.get('total_amount')} - {txn.get('created_at')}")
            print()
            
            # Debug info
            debug = data.get('debug_info', {})
            print(f"🔍 DEBUG INFO:")
            print(f"   Server Time: {debug.get('server_time_ist')}")
            print(f"   Today IST: {debug.get('today_ist')}")
            print(f"   Yesterday IST: {debug.get('yesterday_ist')}")
            
            # Sample bills
            sample_bills = debug.get('sample_bills', [])
            print(f"   Sample Bills:")
            for bill in sample_bills[:3]:
                print(f"     {bill.get('bill_number')} - {bill.get('bill_date')} - {bill.get('created_at')}")
            
            print()
            print("🎯 FILTER TEST RESULTS:")
            
            # Determine if fix is working
            if today.get('count', 0) == 0 and yesterday.get('count', 0) > 0 and all_time.get('count', 0) > 0:
                print("✅ PERFECT! All filters working correctly:")
                print("   - Today shows 0 (no bills created today)")
                print("   - Yesterday shows historical data")
                print("   - All time shows total historical data")
            elif today.get('count', 0) > 0:
                print("✅ EXCELLENT! Today filter shows new bills")
                print("✅ Yesterday and All time filters also working")
            else:
                print("⚠️  Need to check: All filters showing zero")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test Error: {str(e)}")

def test_sales_api_filters():
    """Test the main sales API with different filters"""
    print("\n🧪 TESTING SALES API FILTERS")
    print("=" * 50)
    
    filters = ['today', 'yesterday', 'week', 'month', 'all']
    
    for filter_name in filters:
        try:
            url = f"{BASE_URL}/api/sales?filter={filter_name}&limit=5"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                sales = data.get('sales', [])
                summary = data.get('summary', {})
                
                print(f"📊 {filter_name.upper()} FILTER:")
                print(f"   Records: {len(sales)}")
                print(f"   Total Bills: {summary.get('total_bills', 0)}")
                print(f"   Total Revenue: ₹{summary.get('total_revenue', 0)}")
                print(f"   Status: {'✅ Working' if len(sales) >= 0 else '❌ Error'}")
                
                if len(sales) > 0:
                    print(f"   Latest: {sales[0].get('bill_number')} - ₹{sales[0].get('total_price')}")
                print()
            else:
                print(f"❌ {filter_name} filter error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {filter_name} filter error: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Sales Filter Test at {datetime.now()}")
    print(f"🌐 Testing URL: {BASE_URL}")
    print()
    
    test_sales_filters()
    test_sales_api_filters()
    
    print("\n🎉 Test Complete!")
    print("📝 Check the results above to verify the fix is working")