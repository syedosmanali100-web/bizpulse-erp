#!/usr/bin/env python3
"""
Simple API test without authentication
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import app
import json

def test_barcode_api():
    """Test barcode API endpoints without authentication"""
    print("🚀 Testing Barcode API (No Auth)")
    print("=" * 50)
    
    # Create test client
    app.config['TESTING'] = True
    client = app.test_client()
    
    # Initialize database
    from modules.shared.database import init_db
    init_db()
    
    # Test data
    TEST_BARCODE = "5555555555555"
    
    print(f"\n🧪 Test 1: GET /api/products (List products)")
    
    # Test 1: List products (no auth required)
    response = client.get('/api/products')
    print(f"📤 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        products = response.get_json()
        print(f"✅ Found {len(products)} products")
    else:
        print(f"❌ Failed to list products")
        return False
    
    print(f"\n🧪 Test 2: GET /api/products/search/barcode/{TEST_BARCODE} (Search non-existent barcode)")
    
    # Test 2: Search for non-existent barcode
    response = client.get(f'/api/products/search/barcode/{TEST_BARCODE}')
    print(f"📤 Status Code: {response.status_code}")
    print(f"📤 Response: {response.get_data(as_text=True)}")
    
    if response.status_code == 404:
        result = response.get_json()
        if not result.get('success'):
            print(f"✅ Correctly returned 'not found' for non-existent barcode")
        else:
            print(f"❌ Should have returned 'not found'")
            return False
    else:
        print(f"❌ Expected 404, got {response.status_code}")
        return False
    
    print(f"\n🧪 Test 3: GET /api/test/barcode/{TEST_BARCODE} (Test barcode route)")
    
    # Test 3: Test the barcode test route
    response = client.get(f'/api/test/barcode/{TEST_BARCODE}')
    print(f"📤 Status Code: {response.status_code}")
    print(f"📤 Response: {response.get_data(as_text=True)}")
    
    if response.status_code == 200:
        result = response.get_json()
        if result.get('success'):
            print(f"✅ Barcode test route working")
        else:
            print(f"❌ Barcode test route failed")
            return False
    else:
        print(f"❌ Barcode test route error: {response.status_code}")
        return False
    
    print(f"\n🧪 Test 4: GET /api/products/debug (Debug products)")
    
    # Test 4: Debug products endpoint
    response = client.get('/api/products/debug')
    print(f"📤 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.get_json()
        if result.get('success'):
            print(f"✅ Debug endpoint working - {result.get('total_products', 0)} products")
        else:
            print(f"❌ Debug endpoint failed")
            return False
    else:
        print(f"❌ Debug endpoint error: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎯 BARCODE API TESTS PASSED!")
    print("✅ Product listing: WORKING")
    print("✅ Barcode search (not found): WORKING")
    print("✅ Barcode test route: WORKING")
    print("✅ Debug endpoint: WORKING")
    
    return True

if __name__ == "__main__":
    try:
        test_barcode_api()
    except Exception as e:
        print(f"❌ API Test failed with error: {e}")
        import traceback
        traceback.print_exc()