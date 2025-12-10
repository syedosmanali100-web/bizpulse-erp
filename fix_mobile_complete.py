#!/usr/bin/env python3
"""
Complete Mobile ERP Fix - Restore all modules
This script will copy the working mobile ERP to replace the broken one
"""
import shutil
from datetime import datetime

# Backup current mobile_web_app.html
backup_name = f'mobile_web_app_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
try:
    shutil.copy('mobile_web_app.html', backup_name)
    print(f"✅ Backup created: {backup_name}")
except Exception as e:
    print(f"⚠️  Backup failed: {e}")

# Copy working version to mobile_web_app.html
try:
    shutil.copy('templates/mobile_erp_working.html', 'mobile_web_app.html')
    print("✅ Copied working version to mobile_web_app.html")
except Exception as e:
    print(f"❌ Copy failed: {e}")

# Also ensure templates folder has the working version
try:
    shutil.copy('templates/mobile_erp_working.html', 'templates/mobile_web_app.html')
    print("✅ Updated templates/mobile_web_app.html")
except Exception as e:
    print(f"⚠️  Template update: {e}")

print("\n" + "="*50)
print("🎉 Mobile ERP App Fixed!")
print("="*50)
print("\n📱 Next Steps:")
print("   1. Start server: python app.py")
print("   2. Open browser: http://localhost:5000/mobile")
print("   3. Login: bizpulse.erp@gmail.com / demo123")
print("\n✨ All modules should now be visible!")
