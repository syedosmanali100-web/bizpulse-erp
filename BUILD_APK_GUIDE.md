# BizPulse ERP - APK Build Guide

## Quick Build (Recommended)

### Method 1: Using Android Studio (Easiest)

1. **Open Android Studio**
2. **Open Project**: `File` → `Open` → Select `android` folder
3. **Wait for Gradle Sync** (first time will download dependencies)
4. **Build APK**: 
   - `Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`
5. **APK Location**: 
   ```
   android/app/build/outputs/apk/debug/app-debug.apk
   ```

### Method 2: Using Command Line

```bash
# Step 1: Sync Capacitor (updates web assets)
npx cap sync android

# Step 2: Build APK
cd android
gradlew assembleDebug
cd ..
```

APK will be at: `android/app/build/outputs/apk/debug/app-debug.apk`

---

## Configuration

### Backend URL Configuration

The app is configured to connect to your Render deployment:

**File**: `android/app/src/main/assets/capacitor.config.json`

```json
{
  "server": {
    "url": "https://bizpulse-erp.onrender.com"
  }
}
```

### To Change Backend URL:

1. Edit `android/app/src/main/assets/capacitor.config.json`
2. Change `server.url` to your backend URL
3. Run `npx cap sync android`
4. Rebuild APK

---

## Auto-Update on Backend Changes

### How It Works:

1. **Backend deployed on Render** → Changes go live automatically
2. **Mobile app connects to Render URL** → Gets latest data/features
3. **No APK rebuild needed** for backend changes!

### When to Rebuild APK:

- ✅ **Backend API changes**: NO rebuild needed (app uses live API)
- ✅ **Database changes**: NO rebuild needed (app uses live database)
- ✅ **Business logic changes**: NO rebuild needed (server-side)
- ❌ **UI changes**: Rebuild needed (if you change frontend HTML/CSS/JS)
- ❌ **App config changes**: Rebuild needed (if you change capacitor.config.json)
- ❌ **Native features**: Rebuild needed (if you add plugins)

---

## Release APK (For Production)

### Using Android Studio:

1. `Build` → `Generate Signed Bundle / APK`
2. Select `APK`
3. Create/Select Keystore
4. Fill in key details
5. Select `release` build variant
6. Click `Finish`

### Using Command Line:

```bash
cd android
gradlew assembleRelease
```

**Note**: Release APK needs to be signed for installation.

---

## Install APK on Device

### Method 1: USB Cable

```bash
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

### Method 2: Share APK File

1. Copy APK to phone (WhatsApp, Email, USB)
2. Open APK file on phone
3. Allow "Install from Unknown Sources" if prompted
4. Install

---

## Troubleshooting

### Issue: Gradle Build Fails

**Solution**: Open Android Studio and let it download dependencies first.

### Issue: Java Version Error

**Solution**: 
- Install JDK 17: https://adoptium.net/
- Set JAVA_HOME environment variable

### Issue: App Shows "Cannot connect to server"

**Solution**:
1. Check Render deployment is running
2. Verify URL in `capacitor.config.json`
3. Check phone has internet connection

### Issue: Old data showing in app

**Solution**:
1. Clear app data: Settings → Apps → BizPulse ERP → Clear Data
2. Restart app

---

## Development Workflow

### Daily Development:

1. **Make backend changes** (Python/Flask code)
2. **Commit and push** to GitHub
3. **Render auto-deploys** (5-10 minutes)
4. **Open mobile app** → Refresh → See changes!

### No APK rebuild needed for backend changes! 🎉

---

## Build Scripts

### Quick Build (Debug APK):

```bash
build_apk.bat
```

### Release Build:

```bash
build_release_apk.bat
```

---

## Current Configuration

- **App ID**: `com.bizpulse.retail`
- **App Name**: BizPulse ERP
- **Backend URL**: https://bizpulse-erp.onrender.com
- **Version**: 1.0
- **Build Type**: Debug (for testing)

---

## Next Steps

1. ✅ Backend deployed on Render
2. ✅ Mobile app configured to use Render URL
3. ⏳ Build APK using Android Studio
4. ⏳ Install on device and test
5. ⏳ Make backend changes → Auto-reflect in app!

---

**Need Help?**
- Check Render logs: https://dashboard.render.com
- Check app logs: `adb logcat | grep BizPulse`
- Test backend: https://bizpulse-erp.onrender.com/health
