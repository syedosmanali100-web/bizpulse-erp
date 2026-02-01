# Android Studio APK Build - Step by Step

## ✅ Android Studio is Opening...

---

## STEP 1: Pause OneDrive (IMPORTANT!)

**Before building, do this:**

1. Look at bottom-right of screen (system tray)
2. Find OneDrive cloud icon ☁️
3. Right-click on it
4. Click **"Pause syncing"** → **"2 hours"**
5. ✅ Done!

**Why?** OneDrive locks files during sync, causing build to fail.

---

## STEP 2: Wait for Android Studio to Load

**You'll see:**
- "Opening Project..."
- "Indexing..."
- "Gradle Sync" (bottom-right)

**Wait until:**
- ✅ "Gradle sync finished" appears (bottom status bar)
- ⏱️ Takes 3-5 minutes first time

---

## STEP 3: Open Terminal in Android Studio

**Two ways:**

### Method A: Bottom Tab
1. Look at bottom of Android Studio window
2. Click **"Terminal"** tab
3. Terminal opens at bottom

### Method B: Menu
1. Click **"View"** menu (top)
2. Click **"Tool Windows"** → **"Terminal"**

---

## STEP 4: Run Build Command

**In the Terminal, type:**

```bash
gradlew assembleDebug
```

**Press Enter**

**You'll see:**
- "Downloading dependencies..." (first time)
- "BUILD SUCCESSFUL" (after 5-10 minutes)

---

## STEP 5: Find Your APK

**APK Location:**
```
app\build\outputs\apk\debug\app-debug.apk
```

**To open folder:**
1. In Android Studio, click **"Build"** menu
2. Click **"Build Bundle(s) / APK(s)"** → **"Build APK(s)"**
3. When done, click **"locate"** link in notification
4. APK folder opens!

---

## STEP 6: Install APK on Phone

### Method 1: USB Cable
```bash
adb install app\build\outputs\apk\debug\app-debug.apk
```

### Method 2: Share File
1. Copy `app-debug.apk` to phone (WhatsApp/Email)
2. Open file on phone
3. Click "Install"
4. Done!

---

## Troubleshooting

### ❌ "Gradle sync failed"
**Solution:**
1. Click **"File"** → **"Invalidate Caches"**
2. Select **"Invalidate and Restart"**
3. Wait for restart and sync

### ❌ "Build failed: Unable to delete directory"
**Solution:**
1. **Pause OneDrive** (see Step 1)
2. In Terminal: `gradlew clean`
3. Then: `gradlew assembleDebug`

### ❌ "Java version error"
**Solution:**
- You have Java 25 ✅
- Should work fine
- If error persists, install JDK 17

### ❌ Terminal not showing
**Solution:**
1. Press **Alt + F12** (keyboard shortcut)
2. Or: View → Tool Windows → Terminal

---

## Quick Commands Reference

```bash
# Clean build
gradlew clean

# Build debug APK
gradlew assembleDebug

# Build release APK
gradlew assembleRelease

# Install on connected device
gradlew installDebug

# List all tasks
gradlew tasks
```

---

## What Happens After Build?

1. ✅ APK created at: `app\build\outputs\apk\debug\app-debug.apk`
2. 📱 Install on phone
3. 🚀 App connects to: `https://bizpulse-erp.onrender.com`
4. ✅ Backend changes auto-reflect (no rebuild needed!)

---

## Current Status

- ✅ Backend deployed on Render
- ✅ Bill creation optimized (instant)
- ✅ App configured to use Render URL
- ⏳ Building APK in Android Studio...

---

**Need Help?**
- Check bottom status bar for progress
- Look for "BUILD SUCCESSFUL" message
- APK size: ~10-15 MB
