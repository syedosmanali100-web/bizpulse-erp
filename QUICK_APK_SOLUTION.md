# Quick APK Build Solution

## Problem
Gradle build failing due to OneDrive sync locking files.

## Solution 1: Disable OneDrive Sync (Recommended)

### Step 1: Pause OneDrive
1. Right-click OneDrive icon in system tray
2. Click "Pause syncing" → "2 hours"

### Step 2: Build APK
```bash
cd android
.\gradlew.bat assembleDebug --no-daemon
```

### Step 3: Resume OneDrive
- OneDrive will auto-resume after 2 hours

---

## Solution 2: Move Project Outside OneDrive

### Step 1: Copy Project
```bash
# Copy entire project to C:\Projects
xcopy "C:\Users\osman\OneDrive\Desktop\Mobile-ERP" "C:\Projects\Mobile-ERP" /E /I /H
```

### Step 2: Build from New Location
```bash
cd C:\Projects\Mobile-ERP\android
.\gradlew.bat assembleDebug
```

---

## Solution 3: Use Existing APK (If Available)

Check if APK already exists:
```
android\app\build\outputs\apk\debug\app-debug.apk
```

If exists, use it directly!

---

## Solution 4: Online Build Service

### Using EAS Build (Expo)
```bash
npm install -g eas-cli
eas build --platform android
```

### Using AppCenter
1. Go to: https://appcenter.ms
2. Create new app
3. Connect GitHub repo
4. Configure Android build
5. Download APK

---

## Recommended: Solution 1 (Pause OneDrive)

**Easiest and fastest!**

1. Pause OneDrive (2 hours)
2. Run: `cd android && .\gradlew.bat assembleDebug`
3. Wait 5-10 minutes
4. APK ready!

---

## After APK is Built

### Install on Phone:
```bash
adb install android\app\build\outputs\apk\debug\app-debug.apk
```

### Or Share APK:
- Copy APK file to phone via WhatsApp/Email
- Open and install on phone

---

## Backend Already Working!

Remember:
- ✅ Backend deployed on Render
- ✅ Bill creation optimized (instant)
- ✅ App configured to use Render URL
- ✅ Backend changes auto-reflect (no APK rebuild needed)

**Just need to build APK once!**
