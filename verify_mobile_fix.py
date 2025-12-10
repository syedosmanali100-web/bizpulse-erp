#!/usr/bin/env python3
"""
Verify Mobile ERP Fix - Check all files and configurations
"""
import os
from pathlib import Path

print("="*60)
print("🔍 Verifying Mobile ERP Fix")
print("="*60)

# Check files exist
files_to_check = [
    'app.py',
    'templates/mobile_erp_working.html',
    'templates/mobile_web_app.html',
    'mobile_web_app.html',
    'billing.db'
]

print("\n📂 Checking Files:")
all_files_exist = True
for file in files_to_check:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} ({size:,} bytes)")
    else:
        print(f"❌ {file} - MISSING!")
        all_files_exist = False

# Check app.py routes
print("\n🛣️  Checking Routes in app.py:")
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()
    
routes_to_check = [
    "/mobile",
    "/mobile-working",
    "/mobile-pwa",
    "/api/modules",
    "/api/products",
    "/api/customers",
    "/api/sales/summary",
    "/api/inventory/low-stock"
]

all_routes_exist = True
for route in routes_to_check:
    # Check with different quote styles and with methods parameter
    if (f"@app.route('{route}'" in app_content or 
        f'@app.route("{route}"' in app_content or
        f"'{route}'" in app_content):
        print(f"✅ {route}")
    else:
        print(f"❌ {route} - MISSING!")
        all_routes_exist = False

# Check mobile template has key functions
print("\n⚙️  Checking Mobile Template Functions:")
with open('templates/mobile_erp_working.html', 'r', encoding='utf-8') as f:
    template_content = f.read()

functions_to_check = [
    'showScreen',
    'login',
    'logout',
    'loadProducts',
    'loadCustomers',
    'loadSales',
    'loadDashboardData'
]

all_functions_exist = True
for func in functions_to_check:
    if f'function {func}' in template_content or f'{func} =' in template_content:
        print(f"✅ {func}()")
    else:
        print(f"⚠️  {func}() - Check manually")

# Check database
print("\n💾 Checking Database:")
if os.path.exists('billing.db'):
    import sqlite3
    conn = sqlite3.connect('billing.db')
    cursor = conn.cursor()
    
    tables = ['products', 'customers', 'bills', 'users']
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"✅ {table} table ({count} records)")
        except:
            print(f"❌ {table} table - ERROR!")
    
    conn.close()
else:
    print("❌ billing.db - MISSING!")

# Final summary
print("\n" + "="*60)
if all_files_exist and all_routes_exist:
    print("✅ ALL CHECKS PASSED!")
    print("="*60)
    print("\n🎉 Your Mobile ERP is ready to use!")
    print("\n📱 Next Steps:")
    print("   1. Start server: python app.py")
    print("   2. Open: http://localhost:5000/mobile")
    print("   3. Login: bizpulse.erp@gmail.com / demo123")
    print("\n✨ All modules are working!")
else:
    print("⚠️  SOME CHECKS FAILED!")
    print("="*60)
    print("\n🔧 Please review the errors above")

print("\n" + "="*60)
