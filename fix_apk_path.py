#!/usr/bin/env python3
"""
Quick APK Path Fix
Fixes the file path issue in existing APK by repackaging with correct structure
"""

import zipfile
import os
import shutil
from datetime import datetime

def fix_apk_path():
    """Fix the APK path issue by repackaging"""
    
    print("🔧 BizPulse APK Path Fix")
    print("=" * 40)
    
    apk_file = "BizPulse_Ultimate_Fixed.apk"
    
    if not os.path.exists(apk_file):
        print(f"❌ APK file not found: {apk_file}")
        return False
        
    print(f"📱 Processing: {apk_file}")
    
    # Create temporary directory
    temp_dir = "temp_apk_fix"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Extract APK
        print("📦 Extracting APK...")
        with zipfile.ZipFile(apk_file, 'r') as apk:
            apk.extractall(temp_dir)
            
        # Check current structure
        assets_dir = os.path.join(temp_dir, "assets")
        if os.path.exists(assets_dir):
            files = os.listdir(assets_dir)
            print(f"📁 Current assets: {files}")
            
            # Check if index.html exists
            index_path = os.path.join(assets_dir, "index.html")
            if os.path.exists(index_path):
                print("✅ index.html found in assets/")
                
                # Create the expected zip_22990750 directory structure
                zip_dir = os.path.join(assets_dir, "zip_22990750")
                os.makedirs(zip_dir, exist_ok=True)
                
                # Copy all assets to zip_22990750 directory
                for file in files:
                    src = os.path.join(assets_dir, file)
                    dst = os.path.join(zip_dir, file)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        print(f"📋 Copied {file} to zip_22990750/")
                        
                print("✅ Created zip_22990750 directory structure")
            else:
                print("❌ index.html not found in assets/")
                return False
        else:
            print("❌ Assets directory not found in APK")
            return False
            
        # Repackage APK
        fixed_apk = f"BizPulse_Path_Fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apk"
        print(f"📦 Creating fixed APK: {fixed_apk}")
        
        with zipfile.ZipFile(fixed_apk, 'w', zipfile.ZIP_DEFLATED) as new_apk:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, temp_dir)
                    new_apk.write(file_path, arc_path)
                    
        # Get file sizes
        original_size = os.path.getsize(apk_file) / (1024 * 1024)
        fixed_size = os.path.getsize(fixed_apk) / (1024 * 1024)
        
        print("=" * 40)
        print("✅ APK PATH FIX COMPLETED!")
        print(f"📱 Original APK: {apk_file} ({original_size:.2f} MB)")
        print(f"📱 Fixed APK: {fixed_apk} ({fixed_size:.2f} MB)")
        print("=" * 40)
        
        print("\n🔧 The fixed APK now includes:")
        print("  ✅ assets/index.html (original path)")
        print("  ✅ assets/zip_22990750/index.html (expected path)")
        print("  ✅ Both paths available for compatibility")
        
        print(f"\n📱 Install the fixed APK: {fixed_apk}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing APK: {e}")
        return False
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    fix_apk_path()