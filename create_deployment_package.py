"""
Create deployment package for PythonAnywhere
Sirf zaruri files ko ZIP me pack karega
"""

import os
import zipfile
import shutil
from datetime import datetime

def create_deployment_package():
    print("=" * 60)
    print("  📦 DEPLOYMENT PACKAGE BANA RAHE HAIN")
    print("=" * 60)
    print()
    
    # Package name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"bizpulse_deployment_{timestamp}"
    package_folder = package_name
    zip_filename = f"{package_name}.zip"
    
    # Create package folder
    if os.path.exists(package_folder):
        shutil.rmtree(package_folder)
    os.makedirs(package_folder)
    
    print("✅ Package folder created:", package_folder)
    print()
    
    # Files to include
    files_to_copy = {
        'app.py': 'Main Flask application',
        'requirements.txt': 'Python dependencies',
        'billing.db': 'Database file'
    }
    
    # Folders to include
    folders_to_copy = {
        'templates': 'HTML templates',
        'static': 'CSS, JS, Images'
    }
    
    print("📁 COPYING FILES:")
    print("-" * 60)
    
    # Copy individual files
    for filename, description in files_to_copy.items():
        if os.path.exists(filename):
            shutil.copy2(filename, os.path.join(package_folder, filename))
            print(f"✅ {filename:20} - {description}")
        else:
            print(f"⚠️  {filename:20} - NOT FOUND (skipping)")
    
    print()
    print("📂 COPYING FOLDERS:")
    print("-" * 60)
    
    # Copy folders
    for foldername, description in folders_to_copy.items():
        if os.path.exists(foldername):
            dest_folder = os.path.join(package_folder, foldername)
            shutil.copytree(foldername, dest_folder)
            
            # Count files
            file_count = sum([len(files) for r, d, files in os.walk(dest_folder)])
            print(f"✅ {foldername:20} - {description} ({file_count} files)")
        else:
            print(f"⚠️  {foldername:20} - NOT FOUND (skipping)")
    
    print()
    print("🗜️  CREATING ZIP FILE:")
    print("-" * 60)
    
    # Create ZIP file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_folder)
                zipf.write(file_path, arcname)
                print(f"  Adding: {arcname}")
    
    # Get ZIP size
    zip_size = os.path.getsize(zip_filename) / (1024 * 1024)  # MB
    
    print()
    print("=" * 60)
    print("  ✅ DEPLOYMENT PACKAGE READY!")
    print("=" * 60)
    print()
    print(f"📦 ZIP File: {zip_filename}")
    print(f"📊 Size: {zip_size:.2f} MB")
    print()
    
    # Cleanup temp folder
    shutil.rmtree(package_folder)
    
    print("=" * 60)
    print("  📋 NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Yeh ZIP file upload karo PythonAnywhere pe")
    print(f"   File: {zip_filename}")
    print()
    print("2. PythonAnywhere pe extract karo:")
    print(f"   unzip {zip_filename}")
    print()
    print("3. Web app configure karo (guide dekho)")
    print()
    print("4. Done! Camera chalega! 📷✨")
    print()
    print("=" * 60)
    
    return zip_filename

if __name__ == "__main__":
    try:
        zip_file = create_deployment_package()
        print()
        print(f"🎉 SUCCESS! Upload karo: {zip_file}")
        print()
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
