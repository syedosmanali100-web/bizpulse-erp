@echo off
echo ========================================
echo BizPulse ERP - Auto Deploy Script
echo ========================================
echo.

echo Step 1: Checking Git status...
git status
echo.

echo Step 2: Opening GitHub Desktop (if installed)...
start github
timeout /t 2 /nobreak >nul
echo.

echo Step 3: Opening GitHub repository in browser...
start https://github.com/syedosmanali/bizpulse-erp
timeout /t 2 /nobreak >nul
echo.

echo Step 4: Opening Render dashboard in browser...
start https://render.com/login
timeout /t 2 /nobreak >nul
echo.

echo ========================================
echo MANUAL STEPS REQUIRED:
echo ========================================
echo.
echo 1. GitHub Desktop should be open now
echo    - Click "Push origin" button
echo    - OR use browser to upload files
echo.
echo 2. Render dashboard should be open
echo    - Login with GitHub
echo    - Click "New +" then "Blueprint"
echo    - Select: syedosmanali/bizpulse-erp
echo    - Click "Apply"
echo.
echo 3. Wait 5-10 minutes for deployment
echo.
echo ========================================
echo ALTERNATIVE: Use VS Code
echo ========================================
echo.
echo If you have VS Code:
echo 1. Open VS Code
echo 2. Press Ctrl+Shift+G (Source Control)
echo 3. Click "..." menu
echo 4. Click "Push"
echo.
echo ========================================

pause
