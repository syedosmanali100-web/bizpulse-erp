"""
Quick test script to verify CMS APIs are properly defined
"""

import app

# Test that all CMS routes exist
cms_routes = [
    '/cms',
    '/cms/settings',
    '/cms/hero',
    '/cms/features',
    '/cms/pricing',
    '/cms/testimonials',
    '/cms/faqs',
    '/cms/gallery'
]

# Test that all CMS API endpoints exist
cms_api_endpoints = [
    '/api/cms/upload',
    '/api/cms/admin/settings',
    '/api/cms/admin/hero',
    '/api/cms/admin/features',
    '/api/cms/admin/pricing',
    '/api/cms/admin/testimonials',
    '/api/cms/admin/faqs',
    '/api/cms/admin/gallery',
    '/api/cms/settings',
    '/api/cms/hero',
    '/api/cms/features',
    '/api/cms/pricing',
    '/api/cms/testimonials',
    '/api/cms/faqs',
    '/api/cms/gallery'
]

print("🔍 Testing CMS Implementation...")
print("=" * 50)

# Get all registered routes
all_routes = []
for rule in app.app.url_map.iter_rules():
    all_routes.append(str(rule))

print(f"\n✅ Total routes registered: {len(all_routes)}")

# Check CMS routes
print("\n📄 CMS Dashboard Routes:")
for route in cms_routes:
    if route in all_routes:
        print(f"  ✅ {route}")
    else:
        print(f"  ❌ {route} - MISSING!")

# Check CMS API endpoints
print("\n📡 CMS API Endpoints:")
for endpoint in cms_api_endpoints:
    if endpoint in all_routes:
        print(f"  ✅ {endpoint}")
    else:
        print(f"  ❌ {endpoint} - MISSING!")

print("\n" + "=" * 50)
print("✅ CMS Implementation Test Complete!")
print("\n💡 To start the server, run: python app.py")
print("🌐 Then visit: http://localhost:5000/retail/dashboard")
print("🎨 Click 'CMS' in the sidebar to access the CMS dashboard")
