@echo off
echo.
echo ========================================
echo   Step 1: Pause OneDrive
echo ========================================
echo.
echo IMPORTANT: Please do this manually:
echo 1. Right-click OneDrive icon in system tray (bottom-right)
echo 2. Click "Pause syncing" -^> "2 hours"
echo.
pause
echo.
echo ========================================
echo   Step 2: Opening Android Studio
echo ========================================
echo.

REM Open Android Studio
set "STUDIO_PATH=C:\Program Files\Android\Android Studio\bin\studio64.exe"
if exist "%STUDIO_PATH%" (
    start "" "%STUDIO_PATH%" "%CD%\android"
    echo ✅ Android Studio opening...
) else (
    echo ⚠️  Opening folder in explorer...
    start explorer "%CD%\android"
)

echo.
echo ========================================
echo   Step 3: In Android Studio Terminal
echo ========================================
echo.
echo Once Android Studio opens:
echo 1. Wait for project to load (2-3 minutes)
echo 2. Click "Terminal" tab at bottom
echo 3. Run this command:
echo.
echo    gradlew assembleDebug
echo.
echo 4. Wait 5-10 minutes for build
echo 5. APK will be at: app\build\outputs\apk\debug\app-debug.apk
echo.
pause
