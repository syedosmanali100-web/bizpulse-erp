"""
Retail service
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection
from datetime import datetime

class RetailService:
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics with real-time data"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Today's Revenue (from bills - EXCLUDING credit bills)
        today_revenue = cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as revenue,
                   COUNT(*) as transactions
            FROM bills 
            WHERE DATE(created_at) = ?
            AND NOT EXISTS (
                SELECT 1 FROM sales s 
                WHERE s.bill_id = bills.id 
                AND s.payment_method = 'credit'
            )
        ''', (today,)).fetchone()
        
        # Today's Sales (INCLUDING credit bills for sales count)
        today_sales = cursor.execute('''
            SELECT COALESCE(SUM(s.total_price), 0) as sales,
                   COUNT(DISTINCT s.bill_id) as bills
            FROM sales s
            WHERE s.sale_date = ?
        ''', (today,)).fetchone()
        
        # Today's Cost & Profit (from sales with product cost - EXCLUDING credit bills from profit)
        today_profit_data = cursor.execute('''
            SELECT 
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(s.quantity * p.cost), 0) as total_cost
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE s.sale_date = ?
            AND s.payment_method != 'credit'
        ''', (today,)).fetchone()
        
        total_sales = float(today_profit_data['total_sales'])
        total_cost = float(today_profit_data['total_cost'])
        today_profit = total_sales - total_cost
        profit_margin = (today_profit / total_sales * 100) if total_sales > 0 else 0
        
        # Total Products
        total_products = cursor.execute('''
            SELECT COUNT(*) as count FROM products WHERE is_active = 1
        ''').fetchone()['count']
        
        # Low Stock Products (excluding out of stock)
        low_stock = cursor.execute('''
            SELECT COUNT(*) as count FROM products 
            WHERE stock > 0 AND stock <= min_stock AND is_active = 1
        ''').fetchone()['count']
        
        # Out of Stock Products
        out_of_stock = cursor.execute('''
            SELECT COUNT(*) as count FROM products 
            WHERE stock = 0 AND is_active = 1
        ''').fetchone()['count']
        
        # Total Customers
        total_customers = cursor.execute('''
            SELECT COUNT(*) as count FROM customers WHERE is_active = 1
        ''').fetchone()['count']
        
        # Recent Sales (Last 10)
        recent_sales = cursor.execute('''
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
            LIMIT 10
        ''', (today,)).fetchall()
        
        # Top Selling Products Today
        top_products = cursor.execute('''
            SELECT 
                s.product_name,
                SUM(s.quantity) as total_quantity,
                SUM(s.total_price) as total_sales,
                COUNT(DISTINCT s.bill_id) as times_sold
            FROM sales s
            WHERE s.sale_date = ?
            GROUP BY s.product_id, s.product_name
            ORDER BY total_quantity DESC
            LIMIT 5
        ''', (today,)).fetchall()
        
        # This Week's Revenue
        week_revenue = cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as revenue
            FROM bills 
            WHERE DATE(created_at) >= DATE('now', 'weekday 0', '-6 days')
        ''').fetchone()['revenue']
        
        # This Month's Revenue
        month_revenue = cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as revenue
            FROM bills 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        ''').fetchone()['revenue']
        
        conn.close()
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            # Frontend expects these keys
            'today_revenue': float(today_revenue['revenue']),
            'today_sales': float(today_sales['sales']),  # NEW: Total sales including credit
            'today_orders': today_sales['bills'],  # Use total bills count including credit
            'today_profit': round(today_profit, 2),
            'today_cost': round(total_cost, 2),
            'profit_margin': round(profit_margin, 2),
            'week_revenue': float(week_revenue),
            'month_revenue': float(month_revenue),
            'total_products': total_products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_customers': total_customers,
            # Also keep nested format for compatibility
            'today': {
                'revenue': float(today_revenue['revenue']),  # Excludes credit
                'sales': float(today_sales['sales']),        # Includes credit
                'transactions': today_sales['bills'],        # Total bills including credit
                'profit': round(today_profit, 2),
                'cost': round(total_cost, 2),
                'profit_margin': round(profit_margin, 2)
            },
            'week': {
                'revenue': float(week_revenue)
            },
            'month': {
                'revenue': float(month_revenue)
            },
            'inventory': {
                'total_products': total_products,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock
            },
            'customers': {
                'total': total_customers
            },
            'recent_sales': [dict(row) for row in recent_sales],
            'top_products': [dict(row) for row in top_products]
        }
    
    def get_recent_activity(self):
        """Get recent activity for dashboard"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Recent bills/transactions
        recent_bills = cursor.execute('''
            SELECT 
                b.id,
                b.bill_number,
                b.total_amount,
                b.created_at,
                b.payment_method,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            ORDER BY b.created_at DESC
            LIMIT 20
        ''').fetchall()
        
        # Recent products added
        recent_products = cursor.execute('''
            SELECT id, name, price, stock, created_at
            FROM products
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        
        # Recent customers
        recent_customers = cursor.execute('''
            SELECT id, name, phone, created_at
            FROM customers
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return {
            'success': True,
            'recent_bills': [dict(row) for row in recent_bills],
            'recent_products': [dict(row) for row in recent_products],
            'recent_customers': [dict(row) for row in recent_customers]
        }