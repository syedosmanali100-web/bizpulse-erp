@echo off
echo 🚀 Installing Node.js for BizPulse APK Build
echo.

echo 📥 Downloading Node.js...
echo Please follow these steps:
echo.
echo 1. Go to: https://nodejs.org/
echo 2. Click "Download Node.js (LTS)" - the green button
echo 3. Run the downloaded .msi file as Administrator
echo 4. During installation, make sure "Add to PATH" is checked
echo 5. Restart this terminal after installation
echo.

echo 🌐 Opening Node.js download page...
start https://nodejs.org/

echo.
echo After installing Node.js:
echo 1. Close this window
echo 2. Open a NEW Command Prompt
echo 3. Run: python build_apk.py
echo.
pause