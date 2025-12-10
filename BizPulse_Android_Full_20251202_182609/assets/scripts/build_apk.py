#!/usr/bin/env python3
"""
BizPulse APK Builder - Fixed Version
Builds a proper APK using the Android project structure
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

class BizPulseAPKBuilder:
    def __init__(self):
        self.project_root = os.getcwd()
        self.android_dir = "android"
        self.assets_dir = "android/app/src/main/assets"
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def check_prerequisites(self):
        """Check if required tools are available"""
        self.log("🔍 Checking prerequisites...")
        
        # Check if Android directory exists
        if not os.path.exists(self.android_dir):
            self.log("❌ Android directory not found!")
            return False
            
        # Check if gradlew exists
        gradlew = os.path.join(self.android_dir, "gradlew.bat" if os.name == 'nt' else "gradlew")
        if not os.path.exists(gradlew):
            self.log("❌ Gradle wrapper not found!")
            return False
            
        self.log("✅ Prerequisites check passed")
        return True
        
    def prepare_assets(self):
        """Prepare web assets for the APK"""
        self.log("📱 Preparing web assets...")
        
        # Ensure assets directory exists
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Copy the mobile web app as index.html
        if os.path.exists("mobile_web_app.html"):
            shutil.copy2("mobile_web_app.html", f"{self.assets_dir}/index.html")
            self.log("✅ Copied mobile_web_app.html to assets/index.html")
        else:
            self.log("❌ mobile_web_app.html not found!")
            return False
            
        # Copy additional assets if they exist
        assets_to_copy = [
            ("build/manifest.json", "manifest.json"),
            ("build/icon-192.png", "icon-192.png"),
            ("build/icon-512.png", "icon-512.png"),
            ("build/sw.js", "sw.js")
        ]
        
        for src, dst in assets_to_copy:
            if os.path.exists(src):
                dst_path = f"{self.assets_dir}/{dst}"
                shutil.copy2(src, dst_path)
                self.log(f"✅ Copied {src} to assets/{dst}")
            else:
                self.log(f"⚠️  {src} not found, skipping...")
                
        return True
        
    def update_server_url(self):
        """Update server URL in the mobile app"""
        self.log("🌐 Updating server URL...")
        
        index_path = f"{self.assets_dir}/index.html"
        if not os.path.exists(index_path):
            return False
            
        try:
            # Get current IP
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Read and update the HTML file
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace the server URL
            old_url = "SERVER_URL: 'http://192.168.31.75:5000'"
            new_url = f"SERVER_URL: 'http://{local_ip}:5000'"
            
            if old_url in content:
                content = content.replace(old_url, new_url)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.log(f"✅ Updated server URL to {local_ip}:5000")
            else:
                self.log("⚠️  Server URL pattern not found, using default")
                
        except Exception as e:
            self.log(f"⚠️  Could not update server URL: {e}")
            
        return True
        
    def build_apk(self):
        """Build the APK using Gradle"""
        self.log("🔨 Building APK...")
        
        # Change to Android directory
        original_dir = os.getcwd()
        os.chdir(self.android_dir)
        
        try:
            # Determine the correct gradlew command
            gradlew_cmd = "gradlew.bat" if os.name == 'nt' else "./gradlew"
            
            # Clean and build
            self.log("🧹 Cleaning previous build...")
            result = subprocess.run([gradlew_cmd, "clean"], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"❌ Clean failed: {result.stderr}")
                return False
                
            self.log("🔨 Building debug APK...")
            result = subprocess.run([gradlew_cmd, "assembleDebug"], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"❌ Build failed: {result.stderr}")
                return False
                
            self.log("✅ APK build completed successfully!")
            return True
            
        except Exception as e:
            self.log(f"❌ Build error: {e}")
            return False
            
        finally:
            os.chdir(original_dir)
            
    def copy_apk(self):
        """Copy the built APK to project root"""
        self.log("📦 Copying APK...")
        
        # Find the built APK
        apk_path = "android/app/build/outputs/apk/debug/app-debug.apk"
        
        if os.path.exists(apk_path):
            # Copy to project root with a better name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"BizPulse_Fixed_{timestamp}.apk"
            shutil.copy2(apk_path, new_name)
            
            # Get file size
            size = os.path.getsize(new_name)
            size_mb = size / (1024 * 1024)
            
            self.log(f"✅ APK copied to: {new_name}")
            self.log(f"📊 APK size: {size_mb:.2f} MB ({size:,} bytes)")
            
            return new_name
        else:
            self.log("❌ Built APK not found!")
            return None
            
    def build(self):
        """Main build process"""
        self.log("🚀 Starting BizPulse APK Build...")
        self.log("=" * 60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
            
        # Prepare assets
        if not self.prepare_assets():
            return False
            
        # Update server URL
        self.update_server_url()
        
        # Build APK
        if not self.build_apk():
            return False
            
        # Copy APK
        apk_file = self.copy_apk()
        if not apk_file:
            return False
            
        # Success message
        self.log("=" * 60)
        self.log("✅ APK BUILD SUCCESSFUL!")
        self.log(f"📱 APK File: {apk_file}")
        self.log("=" * 60)
        
        print("\n🔧 INSTALLATION INSTRUCTIONS:")
        print("1. Enable 'Unknown Sources' in Android Settings")
        print("2. Transfer the APK to your Android device")
        print("3. Tap the APK file to install")
        print("4. Launch 'BizPulse ERP' from your app drawer")
        print("5. The app will load your mobile web interface")
        
        print("\n🌐 NETWORK SETUP:")
        print("1. Start your Flask server: python app.py")
        print("2. Ensure your device and computer are on the same WiFi")
        print("3. The app will automatically connect to your server")
        
        return True

def main():
    """Main function"""
    print("🛒 BizPulse APK Builder - Fixed Version")
    print("Building proper APK with WebView integration...")
    print()
    
    builder = BizPulseAPKBuilder()
    success = builder.build()
    
    if success:
        print("\n🎉 Your BizPulse APK is ready!")
        print("The APK now includes:")
        print("  ✅ Proper WebView configuration")
        print("  ✅ File access permissions enabled")
        print("  ✅ Console logging for debugging")
        print("  ✅ Correct asset loading path")
        print("  ✅ Your mobile web app interface")
    else:
        print("\n❌ Build failed. Check the logs above for details.")
        print("\n💡 Common issues:")
        print("  - Android SDK not installed")
        print("  - Java/Gradle not configured")
        print("  - Missing mobile_web_app.html file")
        sys.exit(1)

if __name__ == "__main__":
    main()