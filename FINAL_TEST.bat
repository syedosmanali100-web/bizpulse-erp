@echo off
cls
echo ============================================================
echo FINAL TEST - CLEAN MOBILE ERP
echo ============================================================
echo.
echo ✅ Clean version created (no minified code)
echo ✅ Console logs added for debugging
echo ✅ All functions readable
echo.
echo ============================================================
echo IMPORTANT STEPS:
echo ============================================================
echo.
echo 1. CLEAR BROWSER CACHE (MUST DO!)
echo    - Press: Ctrl + Shift + Delete
echo    - Select: "Cached images and files"
echo    - Click: "Clear data"
echo.
echo 2. OR use Incognito/Private window
echo.
echo 3. Open: http://localhost:5000/mobile
echo.
echo 4. Login:
echo    Email: bizpulse.erp@gmail.com
echo    Password: demo123
echo.
echo 5. Open Console (F12) to see logs:
echo    - "📱 Mobile ERP Loading..."
echo    - "✅ Loader hidden"
echo    - "✅ Login screen shown"
echo    - "🔐 Login attempt..."
echo    - "✅ Login successful"
echo.
echo 6. Click hamburger menu (three lines)
echo.
echo ============================================================
echo Starting server...
echo ============================================================
echo.
python app.py
