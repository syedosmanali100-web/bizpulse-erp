#!/usr/bin/env python3
"""
⚡ BizPulse ERP - Barcode Speed Test
Test barcode scanning performance like RetailsDaddy
"""

import requests
import time
import json
from datetime import datetime

def test_barcode_speed():
    """Test barcode scanning speed - Should be < 100ms like RetailsDaddy"""
    
    base_url = "http://localhost:5000"
    
    # Test barcodes (you can add real barcodes from your products)
    test_barcodes = [
        "1234567890123",
        "9876543210987", 
        "1111111111111",
        "2222222222222",
        "3333333333333"
    ]
    
    print("⚡ BizPulse ERP - Barcode Speed Test")
    print("=" * 50)
    print(f"🎯 Target: < 100ms per scan (RetailsDaddy standard)")
    print(f"🌐 Testing: {base_url}")
    print()
    
    # Test 1: Individual barcode searches
    print("🔍 TEST 1: Individual Barcode Search Speed")
    print("-" * 40)
    
    total_time = 0
    successful_scans = 0
    
    for i, barcode in enumerate(test_barcodes, 1):
        start_time = time.time()
        
        try:
            response = requests.get(f"{base_url}/api/products/search/barcode/{barcode}", timeout=5)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            total_time += response_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    successful_scans += 1
                    status = "✅ FOUND"
                else:
                    status = "❌ NOT FOUND"
            else:
                status = f"❌ ERROR {response.status_code}"
            
            # Speed rating
            if response_time < 50:
                speed_rating = "🚀 LIGHTNING"
            elif response_time < 100:
                speed_rating = "⚡ FAST"
            elif response_time < 200:
                speed_rating = "🐌 SLOW"
            else:
                speed_rating = "🐢 VERY SLOW"
            
            print(f"Scan {i}: {barcode} → {response_time:.1f}ms {speed_rating} {status}")
            
        except requests.exceptions.Timeout:
            print(f"Scan {i}: {barcode} → TIMEOUT ❌")
        except Exception as e:
            print(f"Scan {i}: {barcode} → ERROR: {e}")
    
    # Test 2: Rapid-fire scanning (like real retail environment)
    print()
    print("🔥 TEST 2: Rapid-Fire Scanning (10 scans)")
    print("-" * 40)
    
    rapid_start = time.time()
    rapid_successful = 0
    
    for i in range(10):
        barcode = test_barcodes[i % len(test_barcodes)]
        scan_start = time.time()
        
        try:
            response = requests.get(f"{base_url}/api/products/search/barcode/{barcode}", timeout=2)
            scan_end = time.time()
            
            scan_time = (scan_end - scan_start) * 1000
            
            if response.status_code == 200:
                rapid_successful += 1
                print(f"  Rapid scan {i+1}: {scan_time:.1f}ms ✅")
            else:
                print(f"  Rapid scan {i+1}: {scan_time:.1f}ms ❌")
                
        except Exception as e:
            print(f"  Rapid scan {i+1}: ERROR ❌")
    
    rapid_end = time.time()
    rapid_total = (rapid_end - rapid_start) * 1000
    
    # Test 3: Barcode-to-cart speed (new optimized endpoint)
    print()
    print("🛒 TEST 3: Barcode-to-Cart Speed (New Optimized)")
    print("-" * 40)
    
    for i, barcode in enumerate(test_barcodes[:3], 1):
        start_time = time.time()
        
        try:
            response = requests.post(f"{base_url}/api/products/barcode-to-cart/{barcode}", timeout=5)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cart_item = result.get('cart_item', {})
                    product_name = cart_item.get('product_name', 'Unknown')
                    status = f"✅ ADDED: {product_name}"
                else:
                    status = "❌ FAILED"
            else:
                status = f"❌ ERROR {response.status_code}"
            
            # Speed rating for cart addition
            if response_time < 75:
                speed_rating = "🚀 INSTANT"
            elif response_time < 150:
                speed_rating = "⚡ FAST"
            else:
                speed_rating = "🐌 SLOW"
            
            print(f"Cart {i}: {barcode} → {response_time:.1f}ms {speed_rating} {status}")
            
        except Exception as e:
            print(f"Cart {i}: {barcode} → ERROR: {e}")
    
    # Results Summary
    print()
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    if len(test_barcodes) > 0:
        avg_time = total_time / len(test_barcodes)
        print(f"🎯 Average scan time: {avg_time:.1f}ms")
        
        if avg_time < 50:
            performance = "🚀 EXCELLENT (RetailsDaddy level)"
        elif avg_time < 100:
            performance = "⚡ GOOD (Professional level)"
        elif avg_time < 200:
            performance = "🐌 NEEDS IMPROVEMENT"
        else:
            performance = "🐢 POOR (Optimize required)"
        
        print(f"📈 Performance rating: {performance}")
        print(f"✅ Successful scans: {successful_scans}/{len(test_barcodes)}")
    
    print(f"🔥 Rapid-fire total: {rapid_total:.1f}ms for 10 scans")
    print(f"⚡ Rapid-fire average: {rapid_total/10:.1f}ms per scan")
    print(f"🎯 Rapid-fire success: {rapid_successful}/10")
    
    print()
    print("🎯 OPTIMIZATION RECOMMENDATIONS:")
    if avg_time > 100:
        print("  - ❌ Too slow for professional retail")
        print("  - 🔧 Check database indexes")
        print("  - 🔧 Optimize network connection")
        print("  - 🔧 Add caching layer")
    else:
        print("  - ✅ Speed is acceptable for retail use")
        print("  - 🚀 Ready for production deployment")
    
    print()
    print("🚀 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_barcode_speed()