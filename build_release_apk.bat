@echo off
echo.
echo ========================================
echo   BizPulse ERP - Release APK Builder
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
echo 📱 Step 2: Building Release APK...
cd android
call gradlew assembleRelease
if %errorlevel% neq 0 (
    echo ❌ Release APK build failed!
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ✅ Release APK Built Successfully!
echo.
echo 📦 APK Location:
echo    android\app\build\outputs\apk\release\app-release-unsigned.apk
echo.
echo ⚠️  Note: This APK is unsigned. For production:
echo    1. Sign the APK with your keystore
echo    2. Or use: gradlew bundleRelease for Play Store
echo.
pause
