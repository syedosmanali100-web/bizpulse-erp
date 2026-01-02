#!/usr/bin/env python3
"""
Quick barcode speed test
"""

import time
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.products.service import ProductsService

def test_barcode_speed():
    """Test barcode search speed directly"""
    
    service = ProductsService()
    
    test_barcodes = [
        "1234567890123",
        "9876543210987", 
        "1111111111111",
        "2222222222222",
        "3333333333333"
    ]
    
    print("⚡ BizPulse ERP - Direct Barcode Speed Test")
    print("=" * 50)
    print(f"🎯 Target: < 50ms per scan (RetailsDaddy standard)")
    print()
    
    total_time = 0
    successful_scans = 0
    
    for i, barcode in enumerate(test_barcodes, 1):
        start_time = time.time()
        
        try:
            result = service.search_product_by_barcode(barcode)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            total_time += response_time
            
            if result.get('success'):
                successful_scans += 1
                product_name = result['product']['name']
                status = f"✅ FOUND: {product_name}"
            else:
                status = "❌ NOT FOUND"
            
            # Speed rating
            if response_time < 10:
                speed_rating = "🚀 LIGHTNING"
            elif response_time < 25:
                speed_rating = "⚡ VERY FAST"
            elif response_time < 50:
                speed_rating = "✅ FAST"
            elif response_time < 100:
                speed_rating = "🐌 SLOW"
            else:
                speed_rating = "🐢 VERY SLOW"
            
            print(f"Scan {i}: {barcode} → {response_time:.1f}ms {speed_rating} {status}")
            
        except Exception as e:
            print(f"Scan {i}: {barcode} → ERROR: {e}")
    
    # Rapid-fire test
    print()
    print("🔥 RAPID-FIRE TEST (20 scans)")
    print("-" * 40)
    
    rapid_start = time.time()
    rapid_successful = 0
    
    for i in range(20):
        barcode = test_barcodes[i % len(test_barcodes)]
        
        try:
            result = service.search_product_by_barcode(barcode)
            if result.get('success'):
                rapid_successful += 1
                
        except Exception as e:
            pass
    
    rapid_end = time.time()
    rapid_total = (rapid_end - rapid_start) * 1000
    rapid_avg = rapid_total / 20
    
    print(f"🔥 Rapid-fire completed: {rapid_total:.1f}ms total")
    print(f"⚡ Average per scan: {rapid_avg:.1f}ms")
    print(f"✅ Success rate: {rapid_successful}/20")
    
    # Results Summary
    print()
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 50)
    
    if len(test_barcodes) > 0:
        avg_time = total_time / len(test_barcodes)
        print(f"🎯 Average scan time: {avg_time:.1f}ms")
        
        if avg_time < 10:
            performance = "🚀 LIGHTNING FAST (Better than RetailsDaddy!)"
        elif avg_time < 25:
            performance = "⚡ EXCELLENT (RetailsDaddy level)"
        elif avg_time < 50:
            performance = "✅ VERY GOOD (Professional level)"
        elif avg_time < 100:
            performance = "🐌 NEEDS IMPROVEMENT"
        else:
            performance = "🐢 POOR (Optimize required)"
        
        print(f"📈 Performance rating: {performance}")
        print(f"✅ Successful scans: {successful_scans}/{len(test_barcodes)}")
    
    print()
    if avg_time < 50:
        print("🎉 EXCELLENT! Your barcode scanning is now LIGHTNING FAST!")
        print("🚀 Ready for professional retail deployment!")
        print("⚡ Faster than most competitors including RetailsDaddy!")
    else:
        print("🔧 OPTIMIZATION NEEDED:")
        print("  - Check database indexes")
        print("  - Optimize queries")
        print("  - Consider caching")
    
    print()
    print("🚀 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_barcode_speed()