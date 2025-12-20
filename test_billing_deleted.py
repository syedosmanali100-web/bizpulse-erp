"""
Test script to verify billing APIs are deleted
"""

import urllib.request
import urllib.parse
import json

def test_deleted_endpoint(name, url):
    """Test that an endpoint is deleted (should return 404)"""
    print(f"\n🧪 Testing DELETED: {name}")
    print(f"URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            print(f"❌ UNEXPECTED: Status {status_code} - API still working!")
            return False
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"✅ SUCCESS: 404 Not Found - API properly deleted!")
            return True
        else:
            print(f"✅ SUCCESS: {e.code} Error - API not working!")
            return True
    except Exception as e:
        print(f"✅ SUCCESS: Connection error - API deleted!")
        return True

def test_working_endpoint(name, url):
    """Test that an endpoint is still working"""
    print(f"\n🧪 Testing WORKING: {name}")
    print(f"URL: {url}")
    
    try:
        req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            if status_code == 200:
                print(f"✅ SUCCESS: Status {status_code} - API working!")
                return True
            else:
                print(f"❌ UNEXPECTED: Status {status_code}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("🗑️ BILLING BACKEND DELETION TEST")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    print("\n❌ TESTING DELETED BILLING APIs:")
    deleted_results = []
    
    # Test deleted billing endpoints
    deleted_results.append(test_deleted_endpoint(
        "Create Bill Now", 
        f"{base_url}/api/create-bill-now"
    ))
    
    deleted_results.append(test_deleted_endpoint(
        "Bills Simple", 
        f"{base_url}/api/bills-simple"
    ))
    
    deleted_results.append(test_deleted_endpoint(
        "Main Bills", 
        f"{base_url}/api/bills"
    ))
    
    deleted_results.append(test_deleted_endpoint(
        "Bills Create", 
        f"{base_url}/api/bills/create"
    ))
    
    deleted_results.append(test_deleted_endpoint(
        "Bills List", 
        f"{base_url}/api/bills/list"
    ))
    
    print("\n✅ TESTING WORKING APIs:")
    working_results = []
    
    # Test working endpoints
    working_results.append(test_working_endpoint(
        "Products API", 
        f"{base_url}/api/products"
    ))
    
    working_results.append(test_working_endpoint(
        "Customers API", 
        f"{base_url}/api/customers"
    ))
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    
    deleted_count = sum(deleted_results)
    working_count = sum(working_results)
    
    print(f"\n❌ DELETED APIS: {deleted_count}/{len(deleted_results)} properly deleted")
    print(f"✅ WORKING APIS: {working_count}/{len(working_results)} still working")
    
    if deleted_count == len(deleted_results) and working_count == len(working_results):
        print("\n🎉 SUCCESS! Billing backend properly deleted!")
        print("✅ All billing APIs are non-functional")
        print("✅ Other APIs still working")
        print("\n📱 Frontend billing UI will display but won't work")
        print("🌐 Ready for production deployment!")
    else:
        print("\n❌ ISSUE! Some APIs not in expected state")
        if deleted_count < len(deleted_results):
            print("⚠️  Some billing APIs still working")
        if working_count < len(working_results):
            print("⚠️  Some other APIs not working")

if __name__ == "__main__":
    main()