@echo off
echo ============================================================
echo 📱 Starting BizPulse Mobile ERP
echo ============================================================
echo.

echo 🔍 Verifying setup...
python verify_mobile_fix.py
echo.

echo ============================================================
echo 🚀 Starting Flask Server...
echo ============================================================
echo.
echo 📱 Mobile App will be available at:
echo    http://localhost:5000/mobile
echo.
echo 🔑 Login Credentials:
echo    Email: bizpulse.erp@gmail.com
echo    Password: demo123
echo.
echo ⚠️  Press Ctrl+C to stop the server
echo ============================================================
echo.

python app.py
