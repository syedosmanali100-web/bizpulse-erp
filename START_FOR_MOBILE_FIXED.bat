@echo off
color 0A
echo ========================================
echo   BizPulse Mobile ERP - Quick Start
echo ========================================
echo.

echo [Step 1/4] Finding your laptop IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo   Your Laptop IP: %IP%
echo.

echo [Step 2/4] Checking if port 5000 is free...
netstat -an | findstr :5000 > nul
if %errorlevel% equ 0 (
    echo   ⚠️  Port 5000 is already in use!
    echo   Trying to continue anyway...
) else (
    echo   ✅ Port 5000 is available
)
echo.

echo [Step 3/4] Starting Flask server...
echo   Server will run on: http://%IP%:5000
echo.
echo ========================================
echo   MOBILE ACCESS INSTRUCTIONS
echo ========================================
echo.
echo   1. Make sure mobile is on SAME WiFi
echo   2. Open mobile browser
echo   3. Go to: http://%IP%:5000/mobile-simple
echo   4. Login with:
echo      Email: bizpulse.erp@gmail.com
echo      Password: demo123
echo.
echo ========================================
echo   TROUBLESHOOTING
echo ========================================
echo.
echo   If mobile can't connect:
echo   - Check Windows Firewall settings
echo   - Allow Python through firewall
echo   - Make sure both devices on same WiFi
echo.
echo   Alternative: Use ngrok
echo   - Run: ngrok http 5000
echo   - Use the https URL on mobile
echo.
echo ========================================
echo.
echo [Step 4/4] Starting server...
echo   Press Ctrl+C to stop server
echo.
echo ========================================
echo.

python app.py

pause
