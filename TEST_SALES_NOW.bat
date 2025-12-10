@echo off
echo ========================================
echo   SALES MODULE - VERIFICATION TEST
echo ========================================
echo.

echo [1/3] Checking database products...
python -c "import sqlite3; conn = sqlite3.connect('billing.db'); products = conn.execute('SELECT COUNT(*) FROM products WHERE id LIKE \"prod-%%\"').fetchone(); print(f'  Products with prod- IDs: {products[0]}'); conn.close()"
echo.

echo [2/3] Checking sales data...
python -c "import sqlite3; conn = sqlite3.connect('billing.db'); sales = conn.execute('SELECT COUNT(*) FROM sales').fetchone(); print(f'  Total sales entries: {sales[0]}'); conn.close()"
echo.

echo [3/3] Testing API query...
python test_sales_api_direct.py
echo.

echo ========================================
echo   TEST COMPLETE!
echo ========================================
echo.
echo Next steps:
echo 1. Start server: python app.py
echo 2. Open: http://localhost:5000/sales-management
echo 3. Check browser console (F12) for logs
echo 4. Sales should display with Purchase/Selling prices
echo.
pause
