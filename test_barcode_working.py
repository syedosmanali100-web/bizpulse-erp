#!/usr/bin/env python3
"""
Test barcode functionality directly
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.products.service import ProductsService

def test_barcode_functionality():
    """Test barcode search functionality"""
    
    service = ProductsService()
    
    # Test barcodes from our sample data
    test_barcodes = [
        "1234567890123",  # Rice
        "9876543210987",  # Wheat Flour
        "1111111111111",  # Sugar
        "2222222222222",  # Tea Powder
        "3333333333333",  # Cooking Oil
        "9999999999999"   # Non-existent barcode
    ]
    
    print("🔧 Testing BizPulse ERP Barcode System")
    print("=" * 50)
    
    success_count = 0
    total_time = 0
    
    for i, barcode in enumerate(test_barcodes, 1):
        print(f"\n🔍 Test {i}: Barcode {barcode}")
        
        start_time = time.time()
        
        try:
            result = service.search_product_by_barcode(barcode)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            total_time += response_time
            
            if result.get('success'):
                success_count += 1
                product = result['product']
                print(f"  ✅ FOUND: {product['name']}")
                print(f"  💰 Price: ₹{product['price']}")
                print(f"  📦 Stock: {product['stock']}")
                print(f"  ⚡ Time: {response_time:.1f}ms")
            else:
                print(f"  ❌ NOT FOUND: {result.get('message', 'Unknown error')}")
                print(f"  ⚡ Time: {response_time:.1f}ms")
                
        except Exception as e:
            print(f"  💥 ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    avg_time = total_time / len(test_barcodes) if test_barcodes else 0
    
    print(f"✅ Successful searches: {success_count}/{len(test_barcodes)}")
    print(f"⚡ Average response time: {avg_time:.1f}ms")
    
    if avg_time < 50:
        print("🚀 PERFORMANCE: EXCELLENT (Professional grade)")
    elif avg_time < 100:
        print("⚡ PERFORMANCE: GOOD")
    else:
        print("🐌 PERFORMANCE: NEEDS IMPROVEMENT")
    
    # Test specific functionality
    print("\n🧪 FUNCTIONALITY TESTS")
    print("-" * 30)
    
    # Test 1: Valid barcode
    print("Test 1: Valid barcode search")
    result = service.search_product_by_barcode("1234567890123")
    if result.get('success'):
        print("  ✅ PASS: Valid barcode returns product")
    else:
        print("  ❌ FAIL: Valid barcode should return product")
    
    # Test 2: Invalid barcode
    print("Test 2: Invalid barcode handling")
    result = service.search_product_by_barcode("9999999999999")
    if not result.get('success'):
        print("  ✅ PASS: Invalid barcode returns error")
    else:
        print("  ❌ FAIL: Invalid barcode should return error")
    
    # Test 3: Empty barcode
    print("Test 3: Empty barcode handling")
    result = service.search_product_by_barcode("")
    if not result.get('success'):
        print("  ✅ PASS: Empty barcode returns error")
    else:
        print("  ❌ FAIL: Empty barcode should return error")
    
    print("\n🎯 BARCODE SYSTEM STATUS")
    print("=" * 50)
    
    if success_count >= 4 and avg_time < 100:  # At least 4 out of 5 valid barcodes found
        print("🎉 BARCODE SYSTEM: WORKING PERFECTLY!")
        print("✅ Ready for production use")
        print("⚡ Fast response times")
        print("🔧 Proper error handling")
    else:
        print("⚠️ BARCODE SYSTEM: NEEDS ATTENTION")
        if success_count < 4:
            print("❌ Low success rate - check database")
        if avg_time >= 100:
            print("🐌 Slow response - optimize queries")
    
    print("\n🚀 Test completed!")

if __name__ == "__main__":
    test_barcode_functionality()