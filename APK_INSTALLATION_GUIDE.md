
# BizPulse APK Installation Guide

## 📱 APK Information
- **File**: BizPulse_Ultimate_Fixed.apk
- **Size**: 0.01 MB
- **Build Date**: 2025-12-02 17:36:16

## 🔧 Prerequisites

### 1. Android Device Setup
- Android 5.0 (API 21) or higher
- Enable "Unknown Sources" or "Install from Unknown Sources"
  - Go to Settings > Security > Unknown Sources (Android 7 and below)
  - Go to Settings > Apps > Special Access > Install Unknown Apps (Android 8+)

### 2. Network Setup
- Ensure your Android device and computer are on the same WiFi network
- Computer IP: 192.168.31.75
- Server Port: 5000

## 📥 Installation Steps

### Step 1: Transfer APK
1. Copy `BizPulse_Ultimate_Fixed.apk` to your Android device
2. Methods:
   - USB cable transfer
   - Email attachment
   - Cloud storage (Google Drive, Dropbox)
   - ADB: `adb install BizPulse_Ultimate_Fixed.apk`

### Step 2: Install APK
1. Open file manager on Android device
2. Navigate to the APK file location
3. Tap on `BizPulse_Ultimate_Fixed.apk`
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
- Try installing via ADB: `adb install BizPulse_Ultimate_Fixed.apk`

### Can't Connect to Server
- Verify both devices are on same WiFi network
- Check computer's IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)
- Ensure Flask server is running on port 5000
- Try accessing http://192.168.31.75:5000 in mobile browser first

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
Generated on: 2025-12-02 17:36:16
