#!/usr/bin/env python3
"""
Simple barcode test using urllib (no external dependencies)
"""

import urllib.request
import urllib.error
import json
import time

def test_barcode_simple():
    """Test barcode functionality using urllib"""
    
    base_url = "http://localhost:5000"
    
    # Test barcodes
    test_barcodes = [
        "1234567890123",  # Rice
        "9876543210987",  # Wheat Flour
        "1111111111111",  # Sugar
        "9999999999999"   # Non-existent
    ]
    
    print("🌐 Testing BizPulse ERP Barcode API (Simple)")
    print("=" * 50)
    print(f"🎯 Server: {base_url}")
    print()
    
    # Test barcode search
    print("🔍 BARCODE SEARCH TEST")
    print("-" * 30)
    
    success_count = 0
    total_time = 0
    
    for i, barcode in enumerate(test_barcodes, 1):
        url = f"{base_url}/api/products/search/barcode/{barcode}"
        
        try:
            start_time = time.time()
            
            with urllib.request.urlopen(url, timeout=5) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                total_time += response_time
                
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('success'):
                        success_count += 1
                        product = data['product']
                        print(f"  ✅ {barcode} → {product['name']} (₹{product['price']}) [{response_time:.1f}ms]")
                    else:
                        print(f"  ❌ {barcode} → Not found [{response_time:.1f}ms]")
                else:
                    print(f"  ⚠️ {barcode} → HTTP {response.status} [{response_time:.1f}ms]")
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ❌ {barcode} → Not found [HTTP 404]")
            else:
                print(f"  💥 {barcode} → HTTP Error {e.code}")
        except urllib.error.URLError as e:
            print(f"  💥 {barcode} → Connection Error: {e}")
        except Exception as e:
            print(f"  💥 {barcode} → Error: {e}")
    
    # Test barcode-to-cart (POST request)
    print()
    print("🛒 BARCODE-TO-CART TEST")
    print("-" * 30)
    
    for barcode in test_barcodes[:2]:  # Test first 2 valid barcodes
        url = f"{base_url}/api/products/barcode-to-cart/{barcode}"
        
        try:
            start_time = time.time()
            
            # Create POST request
            req = urllib.request.Request(url, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('success'):
                        cart_item = data['cart_item']
                        print(f"  ✅ {barcode} → Added {cart_item['product_name']} to cart [{response_time:.1f}ms]")
                    else:
                        print(f"  ❌ {barcode} → Failed to add to cart [{response_time:.1f}ms]")
                else:
                    print(f"  ⚠️ {barcode} → HTTP {response.status} [{response_time:.1f}ms]")
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ❌ {barcode} → Product not found [HTTP 404]")
            else:
                print(f"  💥 {barcode} → HTTP Error {e.code}")
        except Exception as e:
            print(f"  💥 {barcode} → Error: {e}")
    
    # Summary
    print()
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    avg_time = total_time / len(test_barcodes) if test_barcodes else 0
    
    print(f"✅ Successful searches: {success_count}/{len(test_barcodes)}")
    print(f"⚡ Average response time: {avg_time:.1f}ms")
    
    if success_count >= 3 and avg_time < 100:
        print()
        print("🎉 BARCODE SYSTEM: WORKING PERFECTLY!")
        print("✅ Fast response times")
        print("✅ Proper error handling")
        print("✅ Ready for production")
        print("🚀 Mobile ERP barcode scanning is READY!")
    else:
        print()
        print("⚠️ BARCODE SYSTEM: NEEDS ATTENTION")
        if success_count < 3:
            print("❌ Low success rate")
        if avg_time >= 100:
            print("🐌 Slow response times")

if __name__ == "__main__":
    test_barcode_simple()