@echo off
echo ================================================
echo 🚀 BizPulse ERP Website Starting...
echo ================================================
echo.

echo 📋 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🌐 Starting website server...
echo.
echo ✅ Website will be available at:
echo    🖥️  Local: http://localhost:5000
echo    📱 Mobile: http://localhost:5000/mobile-simple
echo    👥 Client Management: http://localhost:5000/client-management
echo    📊 WhatsApp Reports: http://localhost:5000/whatsapp-sender
echo.
echo 🔑 Default Login:
echo    Email: bizpulse.erp@gmail.com
echo    Password: demo123
echo.
echo ⚠️  Keep this window open while using the website
echo    Press Ctrl+C to stop the server
echo.

python app.py

pause