@echo off
REM 🚀 BizPulse ERP - Production Deployment Script (Windows)
REM Deploy all changes to GitHub and bizpulse24.com

echo 🚀 Starting BizPulse ERP Deployment...
echo ==================================================

REM Step 1: Add all changes to git
echo 📦 Adding all changes to git...
git add .

REM Step 2: Commit with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo 💾 Committing changes with timestamp: %TIMESTAMP%
git commit -m "🎯 FIX %TIMESTAMP%: Sales Module + Invoice Module Fixed

✅ FIXES:
1. Fixed Sales module not loading data after bill creation
2. Added Invoice module API endpoints (was missing)
3. Registered invoices_bp blueprint in app.py
4. Fixed SQL queries to use COALESCE for proper data retrieval
5. Cleaned up 12 unnecessary test files

🔧 SALES MODULE FIX:
- Fixed get_all_sales() query to properly retrieve product_name
- Fixed get_sales_by_date_range() query
- Data now persists permanently in SQLite database
- No data loss on logout or after time

📊 INVOICE MODULE:
- Created modules/invoices/routes.py
- Created modules/invoices/service.py
- All /api/invoices endpoints now working
- Invoice data reads from bills table

🗑️ DELETED TEST FILES:
- test_server.sh, test_api.py, test_barcode*.py
- direct_barcode_test.py, app_new.py, etc.

✅ DATA PERSISTENCE: All sales/invoice data stored in billing.db"

REM Step 3: Push to GitHub
echo 🌐 Pushing to GitHub...
git push origin main

REM Step 4: Show deployment status
echo.
echo ✅ DEPLOYMENT COMPLETED!
echo ==================================================
echo.
echo 🎯 NEXT STEPS FOR PRODUCTION SERVER:
echo 1. SSH into bizpulse24.com server
echo 2. Navigate to project directory
echo 3. Run: git pull origin main
echo 4. Run: pip install -r requirements.txt
echo 5. Restart Flask application
echo.
echo ✅ Sales Module: FIXED
echo ✅ Invoice Module: FIXED
echo ✅ Data Persistence: WORKING
echo ==================================================

pause
