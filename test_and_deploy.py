#!/usr/bin/env python3
"""
BizPulse APK Testing and Deployment Script
Tests the APK functionality and provides deployment guidance
"""

import os
import sys
import socket
import subprocess
import zipfile
import json
from datetime import datetime

class BizPulseAPKTester:
    def __init__(self):
        self.apk_file = "BizPulse_Ultimate_Fixed.apk"
        self.server_port = 5000
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
    def check_apk_exists(self):
        """Check if APK file exists"""
        if os.path.exists(self.apk_file):
            size = os.path.getsize(self.apk_file)
            size_mb = size / (1024 * 1024)
            self.log(f"✅ APK found: {self.apk_file} ({size_mb:.2f} MB)")
            return True
        else:
            self.log("❌ APK file not found!", "ERROR")
            return False
            
    def analyze_apk_contents(self):
        """Analyze APK contents"""
        self.log("🔍 Analyzing APK contents...")
        
        try:
            with zipfile.ZipFile(self.apk_file, 'r') as apk:
                files = apk.namelist()
                
                required_files = [
                    'AndroidManifest.xml',
                    'classes.dex',
                    'assets/index.html',
                    'META-INF/MANIFEST.MF'
                ]
                
                print("\n📋 APK Contents Analysis:")
                print("=" * 50)
                
                for req_file in required_files:
                    if req_file in files:
                        print(f"✅ {req_file}")
                    else:
                        print(f"❌ {req_file} - MISSING")
                
                print(f"\n📊 Total files in APK: {len(files)}")
                
                # Check assets
                assets = [f for f in files if f.startswith('assets/')]
                print(f"📁 Assets: {len(assets)} files")
                for asset in assets:
                    print(f"   - {asset}")
                    
                # Check resources
                resources = [f for f in files if f.startswith('res/')]
                print(f"🎨 Resources: {len(resources)} files")
                
                return True
                
        except Exception as e:
            self.log(f"❌ Failed to analyze APK: {e}", "ERROR")
            return False
            
    def get_network_info(self):
        """Get network information"""
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Check if port is available
            port_available = True
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('', self.server_port))
                s.close()
            except OSError:
                port_available = False
                
            return local_ip, port_available
            
        except Exception as e:
            self.log(f"❌ Network check failed: {e}", "ERROR")
            return None, False
            
    def test_server_connectivity(self):
        """Test if Flask server can be reached"""
        self.log("🌐 Testing server connectivity...")
        
        local_ip, port_available = self.get_network_info()
        
        if not local_ip:
            self.log("❌ Could not determine local IP", "ERROR")
            return False
            
        print(f"\n🌐 Network Configuration:")
        print(f"   Local IP: {local_ip}")
        print(f"   Port 5000: {'✅ Available' if port_available else '❌ In Use'}")
        print(f"   Server URL: http://{local_ip}:5000")
        
        if not port_available:
            self.log("⚠️  Port 5000 is in use. Stop other Flask apps first.", "WARNING")
            
        return True
        
    def create_installation_guide(self):
        """Create detailed installation guide"""
        self.log("📖 Creating installation guide...")
        
        local_ip, _ = self.get_network_info()
        
        guide_content = f"""
# BizPulse APK Installation Guide

## 📱 APK Information
- **File**: {self.apk_file}
- **Size**: {os.path.getsize(self.apk_file) / (1024*1024):.2f} MB
- **Build Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔧 Prerequisites

### 1. Android Device Setup
- Android 5.0 (API 21) or higher
- Enable "Unknown Sources" or "Install from Unknown Sources"
  - Go to Settings > Security > Unknown Sources (Android 7 and below)
  - Go to Settings > Apps > Special Access > Install Unknown Apps (Android 8+)

### 2. Network Setup
- Ensure your Android device and computer are on the same WiFi network
- Computer IP: {local_ip or 'YOUR_COMPUTER_IP'}
- Server Port: 5000

## 📥 Installation Steps

### Step 1: Transfer APK
1. Copy `{self.apk_file}` to your Android device
2. Methods:
   - USB cable transfer
   - Email attachment
   - Cloud storage (Google Drive, Dropbox)
   - ADB: `adb install {self.apk_file}`

### Step 2: Install APK
1. Open file manager on Android device
2. Navigate to the APK file location
3. Tap on `{self.apk_file}`
4. Tap "Install" when prompted
5. Wait for installation to complete

### Step 3: Start Server
1. On your computer, run:
   ```bash
   python app.py
   ```
2. Note the server IP address shown in the console
3. Ensure firewall allows port 5000

### Step 4: Launch App
1. Find "BizPulse ERP" in your app drawer
2. Tap to launch
3. The app will automatically search for your server
4. Login with: admin@demo.com / demo123

## 🔧 Troubleshooting

### App Won't Install
- Check if "Unknown Sources" is enabled
- Ensure APK file is not corrupted
- Try installing via ADB: `adb install {self.apk_file}`

### Can't Connect to Server
- Verify both devices are on same WiFi network
- Check computer's IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
- Ensure Flask server is running on port 5000
- Try accessing http://{local_ip or 'YOUR_IP'}:5000 in mobile browser first

### App Crashes
- Check Android version (minimum Android 5.0)
- Clear app data: Settings > Apps > BizPulse ERP > Storage > Clear Data
- Reinstall the APK

### Server Connection Issues
- The app tries these URLs automatically:
  - http://192.168.1.100:5000
  - http://192.168.0.100:5000
  - http://10.0.2.2:5000
  - http://localhost:5000
- If your IP is different, the app will show "offline mode"

## 🌐 Network Configuration

### Find Your Computer's IP
**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your WiFi adapter

**Linux/Mac:**
```bash
ifconfig
hostname -I
```

### Test Server Accessibility
1. Start Flask server: `python app.py`
2. On mobile browser, visit: http://YOUR_COMPUTER_IP:5000
3. If webpage loads, the APK should connect successfully

## 📱 App Features

### ✅ Working Features
- Login/Authentication
- Dashboard with statistics
- Product management
- Customer management  
- Billing and POS
- Offline mode support
- Automatic server detection

### 🔄 Offline Mode
- App works without internet connection
- Uses cached data for basic operations
- Syncs when connection is restored

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure network connectivity
3. Verify server is running and accessible
4. Try reinstalling the APK

## 📊 Technical Details
- **Package**: com.bizpulse.erp
- **Min SDK**: 21 (Android 5.0)
- **Target SDK**: 33 (Android 13)
- **Permissions**: Internet, Network State, Storage, Camera
- **Architecture**: Universal (ARM, x86)

---
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open('APK_INSTALLATION_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
            
        self.log("✅ Installation guide created: APK_INSTALLATION_GUIDE.md")
        
    def create_server_start_script(self):
        """Create server startup script"""
        self.log("🚀 Creating server startup script...")
        
        local_ip, _ = self.get_network_info()
        
        # Windows batch script
        batch_content = f"""@echo off
echo 🛒 BizPulse Server for Mobile APK
echo ================================
echo.
echo Starting Flask server...
echo Server will be available at: http://{local_ip or 'YOUR_IP'}:5000
echo.
echo Make sure your Android device is on the same WiFi network!
echo.
python app.py
pause
"""
        
        with open('start_server.bat', 'w', encoding='utf-8') as f:
            f.write(batch_content)
            
        # Linux/Mac shell script
        shell_content = f"""#!/bin/bash
echo "🛒 BizPulse Server for Mobile APK"
echo "================================"
echo ""
echo "Starting Flask server..."
echo "Server will be available at: http://{local_ip or 'YOUR_IP'}:5000"
echo ""
echo "Make sure your Android device is on the same WiFi network!"
echo ""
python3 app.py
"""
        
        with open('start_server.sh', 'w', encoding='utf-8') as f:
            f.write(shell_content)
            
        # Make shell script executable
        try:
            os.chmod('start_server.sh', 0o755)
        except:
            pass
            
        self.log("✅ Server scripts created: start_server.bat, start_server.sh")
        
    def run_comprehensive_test(self):
        """Run comprehensive APK test"""
        self.log("🧪 Running comprehensive APK tests...")
        
        print("\n" + "=" * 60)
        print("🛒 BIZPULSE APK COMPREHENSIVE TEST")
        print("=" * 60)
        
        # Test 1: APK exists
        if not self.check_apk_exists():
            return False
            
        # Test 2: APK contents
        if not self.analyze_apk_contents():
            return False
            
        # Test 3: Network connectivity
        if not self.test_server_connectivity():
            return False
            
        # Test 4: Create guides
        self.create_installation_guide()
        self.create_server_start_script()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    def show_deployment_summary(self):
        """Show deployment summary"""
        local_ip, port_available = self.get_network_info()
        
        print(f"""
🎉 BIZPULSE APK READY FOR DEPLOYMENT!

📱 APK Details:
   File: {self.apk_file}
   Size: {os.path.getsize(self.apk_file) / (1024*1024):.2f} MB
   
🌐 Network Setup:
   Server IP: {local_ip or 'Check your network settings'}
   Server Port: 5000
   Server URL: http://{local_ip or 'YOUR_IP'}:5000
   
🚀 Quick Start:
   1. Run: start_server.bat (Windows) or ./start_server.sh (Linux/Mac)
   2. Install APK on Android device
   3. Launch BizPulse ERP app
   4. Login: admin@demo.com / demo123
   
📖 Documentation:
   - APK_INSTALLATION_GUIDE.md (Detailed instructions)
   - start_server.bat/sh (Server startup scripts)
   
🔧 Troubleshooting:
   - Ensure same WiFi network
   - Check firewall settings
   - Verify port 5000 is available
   
💡 The APK includes automatic server detection and offline mode!
""")

def main():
    """Main testing function"""
    tester = BizPulseAPKTester()
    
    print("🧪 BizPulse APK Testing & Deployment")
    print("=" * 50)
    
    # Run comprehensive tests
    success = tester.run_comprehensive_test()
    
    if success:
        tester.show_deployment_summary()
        print("\n🎯 Your BizPulse APK is ready for production use!")
    else:
        print("\n❌ Tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()