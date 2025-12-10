@echo off
echo ========================================
echo   CAMERA WORKING SETUP - HTTPS
echo ========================================
echo.
echo Bro, camera ke liye HTTPS chahiye!
echo.
echo Yeh script automatically setup karega:
echo   1. Flask server start karega
echo   2. ngrok HTTPS tunnel banayega
echo   3. Camera perfect kaam karega!
echo.
echo ========================================
echo.

REM Check if ngrok is authenticated
echo Checking ngrok authentication...
ngrok config check >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo   NGROK AUTHENTICATION REQUIRED
    echo ========================================
    echo.
    echo Pehle ngrok setup karo:
    echo.
    echo 1. Jao: https://dashboard.ngrok.com/signup
    echo 2. Sign up karo ^(free hai^)
    echo 3. Authtoken copy karo
    echo 4. Run karo: ngrok config add-authtoken YOUR_TOKEN
    echo.
    echo Phir is script ko dobara run karo!
    echo.
    pause
    exit /b 1
)

echo ngrok authenticated! Starting...
echo.

REM Start Flask server in background
echo Starting Flask server...
start "BizPulse Server" cmd /k "python app.py"
timeout /t 3 /nobreak >nul

REM Start ngrok tunnel
echo Starting ngrok HTTPS tunnel...
echo.
echo ========================================
echo   COPY THE HTTPS URL FROM BELOW
echo ========================================
echo.
ngrok http 5000

REM This will keep running until you close it
