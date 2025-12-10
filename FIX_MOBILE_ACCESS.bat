@echo off
color 0E
cls
echo ========================================
echo   FIX MOBILE ACCESS - Simple Steps
echo ========================================
echo.

echo [STEP 1] Finding your laptop IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "192.168"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo   Your IP: %IP%
echo.

echo [STEP 2] Adding Windows Firewall Rule...
echo   This will allow mobile to connect...
echo.
netsh advfirewall firewall add rule name="BizPulse Flask Server" dir=in action=allow protocol=TCP localport=5000
if %errorlevel% equ 0 (
    echo   ✅ Firewall rule added successfully!
) else (
    echo   ⚠️  Run this as Administrator if failed
)
echo.

echo [STEP 3] Your mobile URL:
echo.
echo   ╔════════════════════════════════════════╗
echo   ║  http://%IP%:5000/mobile-simple  ║
echo   ╚════════════════════════════════════════╝
echo.

echo [STEP 4] Instructions:
echo   1. Make sure server is running (python app.py)
echo   2. Connect mobile to SAME WiFi
echo   3. Open mobile browser
echo   4. Type: %IP%:5000/mobile-simple
echo.

echo ========================================
echo   Press any key to start server...
echo ========================================
pause > nul

python app.py
