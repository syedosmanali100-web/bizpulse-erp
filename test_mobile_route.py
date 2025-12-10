"""Test mobile ERP route"""
import requests

# Test mobile routes
routes = [
    'http://localhost:5000/mobile',
    'http://localhost:5000/mobile-simple',
    'http://localhost:5000/mobile-v1'
]

print("=" * 60)
print("TESTING MOBILE ERP ROUTES")
print("=" * 60)

for route in routes:
    try:
        response = requests.get(route, timeout=5)
        status = "✅ OK" if response.status_code == 200 else f"❌ ERROR {response.status_code}"
        print(f"\n{route}")
        print(f"Status: {status}")
        print(f"Content Length: {len(response.text)} bytes")
        
        if response.status_code != 200:
            print(f"Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"\n{route}")
        print(f"❌ FAILED: {e}")

print("\n" + "=" * 60)
