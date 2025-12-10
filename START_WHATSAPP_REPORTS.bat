@echo off
echo ================================================
echo 🚀 BizPulse FREE WhatsApp Reports System
echo ================================================
echo.

echo 🎉 NO API KEYS REQUIRED - COMPLETELY FREE!
echo.

echo [1/3] Testing system...
python test_whatsapp_reports.py
echo.

echo [2/3] Starting main server...
echo ✅ Server will start at http://localhost:5000
echo 📱 Mobile access: http://YOUR_IP:5000/mobile-simple
echo 📊 WhatsApp Reports: http://localhost:5000/whatsapp-sender
echo.
start "BizPulse Server" python app.py

timeout /t 3 /nobreak >nul

echo [3/3] Starting scheduler...
echo ⏰ Scheduler will run daily reports at 11:55 PM
echo.
start "BizPulse Scheduler" python scheduler.py

timeout /t 2 /nobreak >nul

echo.
echo ================================================
echo ✅ System started successfully!
echo ================================================
echo.
echo 🖥️  Main Server: http://localhost:5000
echo 📱 Mobile App: http://localhost:5000/mobile-simple  
echo 📊 WhatsApp Reports: http://localhost:5000/whatsapp-sender
echo.
echo 🎯 QUICK START:
echo 1. Open http://localhost:5000/whatsapp-sender
echo 2. Click "Test System" 
echo 3. Generate your first report!
echo.
echo 📞 Support: +91 7093635305
echo 📧 Email: bizpulse.erp@gmail.com
echo.
echo Press any key to open WhatsApp Reports dashboard...
pause >nul
start http://localhost:5000/whatsapp-sender