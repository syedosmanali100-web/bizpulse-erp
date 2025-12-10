@echo off
echo ================================================
echo 🚀 BizPulse Website Deployment Package Creator
echo ================================================
echo.

set DEPLOY_FOLDER=BizPulse_Website_Deploy_%date:~-4,4%%date:~-10,2%%date:~-7,2%

echo 📁 Creating deployment folder: %DEPLOY_FOLDER%
mkdir "%DEPLOY_FOLDER%"

echo.
echo 📋 Copying essential files...

echo ✅ Copying main server file...
copy "app.py" "%DEPLOY_FOLDER%\"

echo ✅ Copying requirements...
copy "requirements.txt" "%DEPLOY_FOLDER%\"

echo ✅ Copying database...
copy "billing.db" "%DEPLOY_FOLDER%\"

echo ✅ Copying environment config...
copy ".env.example" "%DEPLOY_FOLDER%\"

echo ✅ Copying templates folder...
xcopy "templates" "%DEPLOY_FOLDER%\templates\" /E /I /Q

echo ✅ Copying static files...
xcopy "static" "%DEPLOY_FOLDER%\static\" /E /I /Q

echo ✅ Copying services...
xcopy "services" "%DEPLOY_FOLDER%\services\" /E /I /Q

echo ✅ Copying translations...
xcopy "translations" "%DEPLOY_FOLDER%\translations\" /E /I /Q

echo ✅ Copying scheduler...
copy "scheduler.py" "%DEPLOY_FOLDER%\"

echo ✅ Copying startup scripts...
copy "START_WHATSAPP_REPORTS.bat" "%DEPLOY_FOLDER%\"

echo.
echo 📄 Creating deployment instructions...
echo # BizPulse Website Deployment > "%DEPLOY_FOLDER%\README.md"
echo. >> "%DEPLOY_FOLDER%\README.md"
echo ## Quick Start: >> "%DEPLOY_FOLDER%\README.md"
echo 1. Install Python 3.8+ >> "%DEPLOY_FOLDER%\README.md"
echo 2. Run: pip install -r requirements.txt >> "%DEPLOY_FOLDER%\README.md"
echo 3. Run: python app.py >> "%DEPLOY_FOLDER%\README.md"
echo 4. Open: http://localhost:5000 >> "%DEPLOY_FOLDER%\README.md"
echo. >> "%DEPLOY_FOLDER%\README.md"
echo ## Features: >> "%DEPLOY_FOLDER%\README.md"
echo - Complete ERP System >> "%DEPLOY_FOLDER%\README.md"
echo - Client Management >> "%DEPLOY_FOLDER%\README.md"
echo - WhatsApp Reports >> "%DEPLOY_FOLDER%\README.md"
echo - Mobile App >> "%DEPLOY_FOLDER%\README.md"
echo. >> "%DEPLOY_FOLDER%\README.md"
echo ## Support: 7093635305 >> "%DEPLOY_FOLDER%\README.md"

echo.
echo 📊 Creating deployment info...
echo Deployment Package Created: %date% %time% > "%DEPLOY_FOLDER%\DEPLOYMENT_INFO.txt"
echo Total Files: >> "%DEPLOY_FOLDER%\DEPLOYMENT_INFO.txt"
dir "%DEPLOY_FOLDER%" /s /-c >> "%DEPLOY_FOLDER%\DEPLOYMENT_INFO.txt"

echo.
echo ================================================
echo ✅ Deployment package created successfully!
echo ================================================
echo.
echo 📁 Package Location: %DEPLOY_FOLDER%
echo 📄 Size: 
dir "%DEPLOY_FOLDER%" | find "File(s)"
echo.
echo 🚀 To deploy:
echo 1. Copy the '%DEPLOY_FOLDER%' folder to your server
echo 2. Install Python 3.8+
echo 3. Run: pip install -r requirements.txt
echo 4. Run: python app.py
echo 5. Access: http://YOUR_SERVER_IP:5000
echo.
echo 📱 Mobile Access: http://YOUR_SERVER_IP:5000/mobile-simple
echo 👥 Client Management: http://YOUR_SERVER_IP:5000/client-management
echo 📊 WhatsApp Reports: http://YOUR_SERVER_IP:5000/whatsapp-sender
echo.
echo 📞 Support: 7093635305
echo.
pause
explorer "%DEPLOY_FOLDER%"