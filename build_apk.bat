@echo off
echo.
echo ========================================
echo   BizPulse ERP - APK Builder
echo ========================================
echo.

echo 🔧 Step 1: Syncing Capacitor...
call npx cap sync android
if %errorlevel% neq 0 (
    echo ❌ Capacitor sync failed!
    pause
    exit /b 1
)

echo.
echo 📱 Step 2: Building APK...
cd android
call gradlew assembleDebug
if %errorlevel% neq 0 (
    echo ❌ APK build failed!
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ✅ APK Built Successfully!
echo.
echo 📦 APK Location:
echo    android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo 📲 Install on device:
echo    adb install android\app\build\outputs\apk\debug\app-debug.apk
echo.
pause
