"""
Retail models
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection

class RetailModels:
    
    @staticmethod
    def get_today_revenue(date):
        """Get today's revenue excluding credit bills"""
        conn = get_db_connection()
        try:
            result = conn.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as revenue,
                       COUNT(*) as transactions
                FROM bills 
                WHERE DATE(created_at) = ?
                AND NOT EXISTS (
                    SELECT 1 FROM sales s 
                    WHERE s.bill_id = bills.id 
                    AND s.payment_method = 'credit'
                )
            ''', (date,)).fetchone()
            return dict(result)
        finally:
            conn.close()
    
    @staticmethod
    def get_today_sales(date):
        """Get today's sales including credit bills"""
        conn = get_db_connection()
        try:
            result = conn.execute('''
                SELECT COALESCE(SUM(s.total_price), 0) as sales,
                       COUNT(DISTINCT s.bill_id) as bills
                FROM sales s
                WHERE s.sale_date = ?
            ''', (date,)).fetchone()
            return dict(result)
        finally:
            conn.close()
    
    @staticmethod
    def get_profit_data(date):
        """Get profit data for today"""
        conn = get_db_connection()
        try:
            result = conn.execute('''
                SELECT 
                    COALESCE(SUM(s.total_price), 0) as total_sales,
                    COALESCE(SUM(s.quantity * p.cost), 0) as total_cost
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                WHERE s.sale_date = ?
                AND s.payment_method != 'credit'
            ''', (date,)).fetchone()
            return dict(result)
        finally:
            conn.close()
    
    @staticmethod
    def get_inventory_stats(user_id=None):
        """Get inventory statistics - filtered by user_id for data isolation"""
        conn = get_db_connection()
        try:
            if user_id:
                total_products = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)', (user_id,)).fetchone()['count']
                low_stock = conn.execute('SELECT COUNT(*) as count FROM products WHERE stock > 0 AND stock <= min_stock AND is_active = 1 AND (user_id = ? OR user_id IS NULL)', (user_id,)).fetchone()['count']
                out_of_stock = conn.execute('SELECT COUNT(*) as count FROM products WHERE stock = 0 AND is_active = 1 AND (user_id = ? OR user_id IS NULL)', (user_id,)).fetchone()['count']
            else:
                total_products = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1').fetchone()['count']
                low_stock = conn.execute('SELECT COUNT(*) as count FROM products WHERE stock > 0 AND stock <= min_stock AND is_active = 1').fetchone()['count']
                out_of_stock = conn.execute('SELECT COUNT(*) as count FROM products WHERE stock = 0 AND is_active = 1').fetchone()['count']
            
            return {
                'total_products': total_products,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock
            }
        finally:
            conn.close()
    
    @staticmethod
    def get_customer_count(user_id=None):
        """Get total customer count - filtered by user_id for data isolation"""
        conn = get_db_connection()
        try:
            if user_id:
                count = conn.execute('SELECT COUNT(*) as count FROM customers WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)', (user_id,)).fetchone()['count']
            else:
                count = conn.execute('SELECT COUNT(*) as count FROM customers WHERE is_active = 1').fetchone()['count']
            return count
        finally:
            conn.close()
    
    @staticmethod
    def get_recent_sales(date, limit=10):
        """Get recent sales for today"""
        conn = get_db_connection()
        try:
            sales = conn.execute('''
                SELECT 
                    b.bill_number,
                    b.total_amount,
                    b.created_at,
                    COALESCE(c.name, 'Walk-in Customer') as customer_name,
                    strftime('%H:%M', b.created_at) as time
                FROM bills b
                LEFT JOIN customers c ON b.customer_id = c.id
                WHERE DATE(b.created_at) = ?
                ORDER BY b.created_at DESC
                LIMIT ?
            ''', (date, limit)).fetchall()
            return [dict(row) for row in sales]
        finally:
            conn.close()
    
    @staticmethod
    def get_top_products(date, limit=5):
        """Get top selling products for today"""
        conn = get_db_connection()
        try:
            products = conn.execute('''
                SELECT 
                    s.product_name,
                    SUM(s.quantity) as total_quantity,
                    SUM(s.total_price) as total_sales,
                    COUNT(DISTINCT s.bill_id) as times_sold
                FROM sales s
                WHERE s.sale_date = ?
                GROUP BY s.product_id, s.product_name
                ORDER BY total_quantity DESC
                LIMIT ?
            ''', (date, limit)).fetchall()
            return [dict(row) for row in products]
        finally:
            conn.close()
    
    @staticmethod
    def get_week_revenue():
        """Get this week's revenue"""
        conn = get_db_connection()
        try:
            revenue = conn.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as revenue
                FROM bills 
                WHERE DATE(created_at) >= DATE('now', 'weekday 0', '-6 days')
            ''').fetchone()['revenue']
            return float(revenue)
        finally:
            conn.close()
    
    @staticmethod
    def get_month_revenue():
        """Get this month's revenue"""
        conn = get_db_connection()
        try:
            revenue = conn.execute('''
                SELECT COALESCE(SUM(total_amount), 0) as revenue
                FROM bills 
                WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            ''').fetchone()['revenue']
            return float(revenue)
        finally:
            conn.close()