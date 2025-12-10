"""
Test script to verify invoice routes are working
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def test_routes():
    print("=" * 60)
    print("🧪 Testing Invoice Routes")
    print("=" * 60)
    
    tests = [
        {
            "name": "Invoice List Page",
            "url": f"{BASE_URL}/retail/invoices",
            "expected": "retail_invoices.html"
        },
        {
            "name": "Invoice Demo Page",
            "url": f"{BASE_URL}/invoice-demo",
            "expected": "Invoice Module Demo"
        },
        {
            "name": "Retail Dashboard",
            "url": f"{BASE_URL}/retail/dashboard",
            "expected": "Retail Management Dashboard"
        }
    ]
    
    all_passed = True
    
    for test in tests:
        print(f"\n📋 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        
        try:
            response = requests.get(test['url'], timeout=5)
            
            if response.status_code == 200:
                if test['expected'] in response.text:
                    print(f"   ✅ PASSED - Status: {response.status_code}")
                else:
                    print(f"   ⚠️  WARNING - Page loaded but expected content not found")
                    print(f"   Expected: {test['expected']}")
                    all_passed = False
            else:
                print(f"   ❌ FAILED - Status: {response.status_code}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ FAILED - Cannot connect to server")
            print(f"   Make sure server is running: python app.py")
            all_passed = False
            break
        except Exception as e:
            print(f"   ❌ FAILED - Error: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
        print("\n📝 Next Steps:")
        print("   1. Open browser")
        print("   2. Go to: http://localhost:5000/retail/dashboard")
        print("   3. Click 'Invoices' in sidebar")
        print("   4. Should redirect to invoice list page")
    else:
        print("❌ Some tests failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure server is running: python app.py")
        print("   2. Check if templates/retail_invoices.html exists")
        print("   3. Clear browser cache (Ctrl + Shift + Delete)")
        print("   4. Try direct URL: http://localhost:5000/retail/invoices")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = test_routes()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
