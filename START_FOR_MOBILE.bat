@echo off
cls
echo ============================================================
echo STARTING SERVER FOR MOBILE ACCESS
echo ============================================================
echo.
echo Getting your IP address...
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set IP=%%a
    set IP=!IP: =!
    echo Your Computer IP: !IP!
    echo.
    echo ============================================================
    echo OPEN THESE URLs ON YOUR MOBILE:
    echo ============================================================
    echo.
    echo Simple App:  http://!IP!:5000/mobile-simple
    echo Full App:    http://!IP!:5000/mobile
    echo.
    echo ============================================================
    echo.
    goto :start_server
)

:start_server
echo Starting Flask server on all network interfaces...
echo.
python app.py

pause
