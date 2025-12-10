# BizPulse ERP - Dynamic APK (Like Instagram!)
Generated: 2025-12-02 22:44:32

## 🚀 What Makes This Special:
- ✅ APK loads content from YOUR server
- ✅ Changes to web files update automatically
- ✅ No need to rebuild APK for updates
- ✅ Works like Instagram/Facebook apps

## 📱 How It Works:
1. APK is just a "shell" (like Instagram)
2. All content loads from your Python server
3. When you change web files, app updates instantly
4. Users always get the latest version

## 🛠️ Build Instructions:

### Android Studio:
1. Extract this ZIP
2. Open 'android' folder in Android Studio
3. Build > Generate Signed Bundle/APK
4. Install APK on device

### Command Line:
```bash
cd android
./gradlew assembleDebug
```

## 🔄 How to Update Your App:
1. Make changes to your web files (mobile_web_app.html, app.py, etc.)
2. Restart your Python server: `python app.py`
3. App automatically gets updates - NO APK REBUILD NEEDED!

## 📋 Server Requirements:
- Keep `python app.py` running on your computer
- Make sure phone and computer are on same WiFi
- Update IP address in dynamic_mobile_app.html if needed

## 🎯 Key Features:
- Dynamic content loading
- Auto-refresh every 30 seconds
- Offline detection
- Multiple server URL fallbacks
- Instagram-style architecture

Your BizPulse ERP now works like a professional app! 🎉
