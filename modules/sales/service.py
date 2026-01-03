"""
Sales service - Handle all sales data and analytics
"""

from modules.shared.database import get_db_connection
from datetime import datetime, timedelta
import sqlite3

class SalesService:
    
    def get_sales_by_date_range(self, from_date=None, to_date=None, limit=100):
        """Get sales within a date range"""
        conn = get_db_connection()
        
        if from_date and to_date:
            sales = conn.execute("""
                SELECT s.*,
                       COALESCE(s.product_name, p.name) as product_name,
                       COALESCE(s.customer_name, c.name, 'Walk-in Customer') as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE DATE(s.sale_date) >= ? AND DATE(s.sale_date) <= ?
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (from_date, to_date, limit)).fetchall()
        elif from_date:
            sales = conn.execute("""
                SELECT s.*,
                       COALESCE(s.product_name, p.name) as product_name,
                       COALESCE(s.customer_name, c.name, 'Walk-in Customer') as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE DATE(s.sale_date) >= ?
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (from_date, limit)).fetchall()
        else:
            sales = conn.execute("""
                SELECT s.*,
                       COALESCE(s.product_name, p.name) as product_name,
                       COALESCE(s.customer_name, c.name, 'Walk-in Customer') as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        
        conn.close()
        return [dict(row) for row in sales]
    
    def get_all_sales(self, date_filter=None):
        """Get all sales with optional date filtering"""
        conn = get_db_connection()
        
        base_query = """
            SELECT s.*,
                   COALESCE(s.product_name, p.name) as product_name,
                   COALESCE(s.customer_name, c.name, 'Walk-in Customer') as customer_name
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            LEFT JOIN customers c ON s.customer_id = c.id
        """
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(s.sale_date) = ?
                    ORDER BY s.created_at DESC
                """, (today,)).fetchall()
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(s.sale_date) = ?
                    ORDER BY s.created_at DESC
                """, (yesterday,)).fetchall()
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(s.sale_date) >= ?
                    ORDER BY s.created_at DESC
                """, (week_ago,)).fetchall()
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(s.sale_date) >= ?
                    ORDER BY s.created_at DESC
                """, (month_ago,)).fetchall()
            else:
                # Custom date
                sales = conn.execute(base_query + """
                    WHERE DATE(s.sale_date) = ?
                    ORDER BY s.created_at DESC
                """, (date_filter,)).fetchall()
        else:
            # All sales - no limit for full data
            sales = conn.execute(base_query + """
                ORDER BY s.created_at DESC
                LIMIT 500
            """).fetchall()
        
        conn.close()
        return [dict(row) for row in sales]
    
    def get_sales_summary(self, date_filter=None):
        """Get sales summary with totals"""
        conn = get_db_connection()
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(total_price) as total_revenue,
                        SUM(quantity) as total_items,
                        AVG(total_price) as avg_sale_value
                    FROM sales 
                    WHERE DATE(sale_date) = ?
                """, (today,)).fetchone()
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(total_price) as total_revenue,
                        SUM(quantity) as total_items,
                        AVG(total_price) as avg_sale_value
                    FROM sales 
                    WHERE DATE(sale_date) = ?
                """, (yesterday,)).fetchone()
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(total_price) as total_revenue,
                        SUM(quantity) as total_items,
                        AVG(total_price) as avg_sale_value
                    FROM sales 
                    WHERE DATE(sale_date) >= ?
                """, (week_ago,)).fetchone()
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(total_price) as total_revenue,
                        SUM(quantity) as total_items,
                        AVG(total_price) as avg_sale_value
                    FROM sales 
                    WHERE DATE(sale_date) >= ?
                """, (month_ago,)).fetchone()
            else:
                # Custom date
                summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(total_price) as total_revenue,
                        SUM(quantity) as total_items,
                        AVG(total_price) as avg_sale_value
                    FROM sales 
                    WHERE DATE(sale_date) = ?
                """, (date_filter,)).fetchone()
        else:
            # All time
            summary = conn.execute("""
                SELECT 
                    COUNT(*) as total_sales,
                    SUM(total_price) as total_revenue,
                    SUM(quantity) as total_items,
                    AVG(total_price) as avg_sale_value
                FROM sales
            """).fetchone()
        
        conn.close()
        
        if summary:
            return {
                "total_sales": summary['total_sales'] or 0,
                "total_revenue": float(summary['total_revenue'] or 0),
                "total_items": summary['total_items'] or 0,
                "avg_sale_value": float(summary['avg_sale_value'] or 0)
            }
        else:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "total_items": 0,
                "avg_sale_value": 0.0
            }
    
    def get_top_products(self, limit=10, date_filter=None):
        """Get top selling products"""
        conn = get_db_connection()
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                products = conn.execute("""
                    SELECT 
                        product_name,
                        SUM(quantity) as total_quantity,
                        SUM(total_price) as total_revenue,
                        COUNT(*) as sale_count
                    FROM sales 
                    WHERE DATE(sale_date) = ?
                    GROUP BY product_id, product_name
                    ORDER BY total_revenue DESC
                    LIMIT ?
                """, (today, limit)).fetchall()
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                products = conn.execute("""
                    SELECT 
                        product_name,
                        SUM(quantity) as total_quantity,
                        SUM(total_price) as total_revenue,
                        COUNT(*) as sale_count
                    FROM sales 
                    WHERE DATE(sale_date) >= ?
                    GROUP BY product_id, product_name
                    ORDER BY total_revenue DESC
                    LIMIT ?
                """, (week_ago, limit)).fetchall()
            else:
                # Custom date
                products = conn.execute("""
                    SELECT 
                        product_name,
                        SUM(quantity) as total_quantity,
                        SUM(total_price) as total_revenue,
                        COUNT(*) as sale_count
                    FROM sales 
                    WHERE DATE(sale_date) = ?
                    GROUP BY product_id, product_name
                    ORDER BY total_revenue DESC
                    LIMIT ?
                """, (date_filter, limit)).fetchall()
        else:
            # All time
            products = conn.execute("""
                SELECT 
                    product_name,
                    SUM(quantity) as total_quantity,
                    SUM(total_price) as total_revenue,
                    COUNT(*) as sale_count
                FROM sales 
                GROUP BY product_id, product_name
                ORDER BY total_revenue DESC
                LIMIT ?
            """, (limit,)).fetchall()
        
        conn.close()
        return [dict(row) for row in products]
    
    def get_daily_sales_chart(self, days=7):
        """Get daily sales data for chart"""
        conn = get_db_connection()
        
        # Get sales for last N days
        start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
        
        sales_data = conn.execute("""
            SELECT 
                DATE(sale_date) as sale_date,
                SUM(total_price) as daily_revenue,
                COUNT(*) as daily_sales
            FROM sales 
            WHERE DATE(sale_date) >= ?
            GROUP BY DATE(sale_date)
            ORDER BY sale_date ASC
        """, (start_date,)).fetchall()
        
        conn.close()
        
        # Fill in missing dates with zero values
        chart_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
            found = False
            for row in sales_data:
                if row['sale_date'] == date:
                    chart_data.append({
                        'date': date,
                        'revenue': float(row['daily_revenue']),
                        'sales_count': row['daily_sales']
                    })
                    found = True
                    break
            if not found:
                chart_data.append({
                    'date': date,
                    'revenue': 0.0,
                    'sales_count': 0
                })
        
        return chart_data
    
    def check_database_health(self):
        """Check if sales data is being stored properly"""
        conn = get_db_connection()
        
        # Check total sales count
        total_sales = conn.execute("SELECT COUNT(*) as count FROM sales").fetchone()
        
        # Check recent sales (last 24 hours)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        recent_sales = conn.execute("""
            SELECT COUNT(*) as count FROM sales 
            WHERE created_at >= ?
        """, (yesterday,)).fetchone()
        
        # Check if bills are creating sales entries
        total_bills = conn.execute("SELECT COUNT(*) as count FROM bills").fetchone()
        
        conn.close()
        
        return {
            "total_sales_records": total_sales['count'] if total_sales else 0,
            "recent_sales_24h": recent_sales['count'] if recent_sales else 0,
            "total_bills": total_bills['count'] if total_bills else 0,
            "database_status": "healthy" if total_sales and total_sales['count'] > 0 else "no_data"
        }