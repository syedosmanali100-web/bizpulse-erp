@echo off
echo ========================================
echo Starting BizPulse ERP with ngrok
echo ========================================
echo.

echo Step 1: Starting Flask Server...
start "Flask Server" cmd /k "python app.py"

echo Waiting for server to start...
timeout /t 5 /nobreak > nul

echo.
echo Step 2: Starting ngrok tunnel...
echo.
echo ========================================
echo Your public URLs will appear below:
echo ========================================
echo.

ngrok http 5000

pause
