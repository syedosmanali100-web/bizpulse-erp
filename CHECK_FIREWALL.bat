@echo off
color 0B
echo ========================================
echo   Checking Firewall Status
echo ========================================
echo.

echo Checking if port 5000 is allowed...
echo.

netsh advfirewall firewall show rule name=all | findstr /i "5000" > nul
if %errorlevel% equ 0 (
    echo ✅ Port 5000 has firewall rules
    echo.
    netsh advfirewall firewall show rule name=all | findstr /i "5000"
) else (
    echo ❌ No firewall rules for port 5000
    echo.
    echo You need to add firewall rule!
    echo Run: FIX_MOBILE_ACCESS.bat as Administrator
)

echo.
echo ========================================
echo.

echo Checking Python firewall rules...
echo.

netsh advfirewall firewall show rule name=all | findstr /i "python" > nul
if %errorlevel% equ 0 (
    echo ✅ Python has firewall rules
) else (
    echo ❌ Python not allowed through firewall
    echo.
    echo Fix:
    echo 1. Control Panel ^> Firewall
    echo 2. Allow an app through firewall
    echo 3. Find Python and check both boxes
)

echo.
echo ========================================
pause
