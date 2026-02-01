@echo off
echo.
echo ========================================
echo   BizPulse ERP - Open Android Studio
echo ========================================
echo.

echo 🔧 Syncing Capacitor first...
call npx cap sync android
if %errorlevel% neq 0 (
    echo ❌ Capacitor sync failed!
    pause
    exit /b 1
)

echo.
echo 📱 Opening Android Studio...
echo.
echo 📝 Instructions:
echo    1. Wait for Gradle sync to complete
echo    2. Click: Build → Build Bundle(s) / APK(s) → Build APK(s)
echo    3. APK will be at: android\app\build\outputs\apk\debug\app-debug.apk
echo.

REM Try to find and open Android Studio
set "STUDIO_PATH=C:\Program Files\Android\Android Studio\bin\studio64.exe"
if exist "%STUDIO_PATH%" (
    start "" "%STUDIO_PATH%" "%CD%\android"
    echo ✅ Android Studio opened!
) else (
    echo ⚠️  Android Studio not found at default location
    echo    Please open Android Studio manually and open the 'android' folder
    start explorer "%CD%\android"
)

echo.
pause
