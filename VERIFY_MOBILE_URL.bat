@echo off
color 0A
echo ========================================
echo   Mobile URL Verification
echo ========================================
echo.

echo [1/5] Checking your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "192.168"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo   Your IP: %IP%
echo.

echo [2/5] Verifying mobile URL...
echo   Expected: 192.168.31.75:5000/mobile-simple
echo   Your IP:  %IP%:5000/mobile-simple
echo.

if "%IP%"=="192.168.31.75" (
    echo   ✅ IP MATCHES! URL is correct!
) else (
    echo   ⚠️  IP DIFFERENT! Use: %IP%:5000/mobile-simple
)
echo.

echo [3/5] Checking if server is running...
netstat -an | findstr :5000 > nul
if %errorlevel% equ 0 (
    echo   ✅ Server is running on port 5000
) else (
    echo   ❌ Server is NOT running!
    echo   Run: python app.py
)
echo.

echo [4/5] Testing localhost access...
curl -s http://localhost:5000/api/version > nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ API is responding
) else (
    echo   ⚠️  API not responding (server may not be running)
)
echo.

echo [5/5] Checking Windows Firewall...
netsh advfirewall firewall show rule name=all | findstr "Python" > nul
if %errorlevel% equ 0 (
    echo   ✅ Python firewall rules exist
) else (
    echo   ⚠️  No Python firewall rules found
    echo   You may need to allow Python through firewall
)
echo.

echo ========================================
echo   MOBILE ACCESS INSTRUCTIONS
echo ========================================
echo.
echo   Your Mobile URL:
echo   http://%IP%:5000/mobile-simple
echo.
echo   Steps:
echo   1. Connect mobile to same WiFi
echo   2. Open mobile browser
echo   3. Type: %IP%:5000/mobile-simple
echo   4. Login: bizpulse.erp@gmail.com / demo123
echo.
echo ========================================
echo   QUICK TESTS
echo ========================================
echo.
echo   Test 1: Open in browser
echo   http://%IP%:5000/mobile-simple
echo.
echo   Test 2: Check API
echo   http://%IP%:5000/api/products
echo.
echo   Test 3: Test page
echo   Open: TEST_MOBILE_URL.html
echo.
echo ========================================
echo.

pause
