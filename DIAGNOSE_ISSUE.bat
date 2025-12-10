@echo off
color 0C
echo ========================================
echo   DIAGNOSING MOBILE ISSUE
echo ========================================
echo.

echo [CHECK 1] Is server running?
netstat -an | findstr :5000 > nul
if %errorlevel% equ 0 (
    echo   ✅ YES - Server is running on port 5000
) else (
    echo   ❌ NO - Server is NOT running!
    echo   ^> This is the problem!
    echo   ^> Run: python app.py
    goto :end
)
echo.

echo [CHECK 2] Your laptop IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "192.168"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo   Your IP: %IP%
echo.

echo [CHECK 3] Can laptop access its own server?
curl -s http://localhost:5000/api/version > nul 2>&1
if %errorlevel% equ 0 (
    echo   ✅ YES - Laptop can access server
) else (
    echo   ❌ NO - Server not responding
    echo   ^> Check if Flask is running
    goto :end
)
echo.

echo ========================================
echo   DIAGNOSIS COMPLETE
echo ========================================
echo.
echo Your mobile URL should be:
echo   http://%IP%:5000/mobile-simple
echo.
echo NEXT STEPS:
echo   1. Make sure server is running: python app.py
echo   2. Open mobile browser
echo   3. Type: %IP%:5000/mobile-simple
echo   4. If still fails, try diagnostic: %IP%:5000/mobile-diagnostic
echo.

:end
pause
