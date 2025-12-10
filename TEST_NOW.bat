@echo off
cls
echo ============================================================
echo TESTING MOBILE ERP - FRESH RESTORE
echo ============================================================
echo.
echo Files restored from: mobile_backup_20251207_203654
echo.
echo IMPORTANT: Clear browser cache!
echo   1. Press Ctrl+Shift+Delete
echo   2. Select "Cached images and files"
echo   3. Click "Clear data"
echo.
echo OR use Incognito/Private mode
echo.
echo ============================================================
echo Starting server...
echo ============================================================
echo.
echo Open: http://localhost:5000/mobile
echo.
echo Login:
echo   Email: bizpulse.erp@gmail.com
echo   Password: demo123
echo.
echo Then click the three lines (hamburger menu)
echo.
echo ============================================================
python app.py
