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
        """Get all sales/bills with optional date filtering - returns bill-level data"""
        conn = get_db_connection()
        
        # Query bills table for accurate bill-level data
        base_query = """
            SELECT 
                b.id,
                b.id as bill_id,
                b.bill_number,
                b.customer_id,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name,
                b.total_amount,
                b.total_amount as total_price,
                b.subtotal,
                b.tax_amount,
                b.discount_amount,
                b.payment_method,
                b.payment_status,
                b.is_credit,
                b.credit_balance,
                b.credit_paid_amount,
                DATE(b.created_at) as sale_date,
                TIME(b.created_at) as sale_time,
                b.created_at,
                b.business_type,
                b.status,
                COALESCE(
                    (SELECT GROUP_CONCAT(bi.product_name, ', ') FROM bill_items bi WHERE bi.bill_id = b.id),
                    'Multiple Items'
                ) as products,
                (SELECT SUM(bi.quantity) FROM bill_items bi WHERE bi.bill_id = b.id) as quantity,
                (SELECT COUNT(*) FROM bill_items bi WHERE bi.bill_id = b.id) as items_count,
                CASE 
                    WHEN b.is_credit = 1 AND b.credit_balance > 0 THEN 'due'
                    WHEN b.payment_method = 'partial' THEN 'partial'
                    WHEN b.payment_method = 'credit' THEN 'due'
                    ELSE 'completed'
                END as transaction_status
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
        """
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(b.created_at) = ?
                    ORDER BY b.created_at DESC
                """, (today,)).fetchall()
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(b.created_at) = ?
                    ORDER BY b.created_at DESC
                """, (yesterday,)).fetchall()
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(b.created_at) >= ?
                    ORDER BY b.created_at DESC
                """, (week_ago,)).fetchall()
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                sales = conn.execute(base_query + """
                    WHERE DATE(b.created_at) >= ?
                    ORDER BY b.created_at DESC
                """, (month_ago,)).fetchall()
            else:
                # Custom date
                sales = conn.execute(base_query + """
                    WHERE DATE(b.created_at) = ?
                    ORDER BY b.created_at DESC
                """, (date_filter,)).fetchall()
        else:
            # All sales
            sales = conn.execute(base_query + """
                ORDER BY b.created_at DESC
                LIMIT 500
            """).fetchall()
        
        conn.close()
        
        # Convert to list of dicts with proper field names matching frontend expectations
        result = []
        for index, row in enumerate(sales, 1):
            sale = dict(row)
            
            # Fix S.NO - frontend expects 'serial_no'
            sale['serial_no'] = index
            sale['sno'] = index
            sale['serial_number'] = index
            
            # Fix product names - frontend expects 'product_list'
            products_list = sale.get('products', '')
            if products_list and products_list != 'None' and products_list != 'Multiple Items':
                sale['product_list'] = products_list
                sale['product_name'] = products_list
                sale['products_display'] = products_list
            else:
                # Fallback to get product names from bill_items
                sale['product_list'] = 'Multiple Items'
                sale['product_name'] = 'Multiple Items'
                sale['products_display'] = 'Multiple Items'
            
            # Fix status for credit bills - frontend expects proper status
            if sale.get('is_credit') == 1 and sale.get('credit_balance', 0) > 0:
                sale['status'] = 'DUE'
                sale['status_display'] = 'DUE'
                sale['status_class'] = 'due'
                sale['transaction_status'] = 'due'
            elif sale.get('payment_method') == 'partial':
                sale['status'] = 'PARTIAL'
                sale['status_display'] = 'PARTIAL'
                sale['status_class'] = 'partial'
                sale['transaction_status'] = 'partial'
            else:
                sale['status'] = 'COMPLETED'
                sale['status_display'] = 'COMPLETED'
                sale['status_class'] = 'completed'
                sale['transaction_status'] = 'completed'
            
            # Add fields for frontend compatibility
            sale['date'] = sale.get('sale_date', sale.get('created_at', ''))
            sale['total_items'] = sale.get('items_count', 1)
            sale['total_quantity'] = sale.get('quantity', 1)
            
            # Add CSS class for credit transactions (red color for amounts)
            if sale.get('is_credit') == 1 or sale.get('payment_method') in ['credit', 'partial']:
                sale['css_class'] = 'credit-transaction'
                sale['is_credit_transaction'] = True
                sale['amount_class'] = 'text-danger'  # Red color for amounts
            else:
                sale['css_class'] = ''
                sale['is_credit_transaction'] = False
                sale['amount_class'] = 'text-success'  # Green color for completed
                
            result.append(sale)
        
        return result
    
    def get_sales_summary(self, date_filter=None):
        """Get sales summary with totals - counts unique bills, not individual items"""
        conn = get_db_connection()
        
        # Build date condition
        date_condition = ""
        params = []
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                date_condition = "WHERE DATE(created_at) = ?"
                params = [today]
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                date_condition = "WHERE DATE(created_at) = ?"
                params = [yesterday]
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                date_condition = "WHERE DATE(created_at) >= ?"
                params = [week_ago]
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                date_condition = "WHERE DATE(created_at) >= ?"
                params = [month_ago]
            else:
                # Custom date
                date_condition = "WHERE DATE(created_at) = ?"
                params = [date_filter]
        
        # Get summary from BILLS table for accurate totals
        query = f"""
            SELECT 
                COUNT(*) as total_sales,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(AVG(total_amount), 0) as avg_sale_value,
                COALESCE(SUM(CASE WHEN is_credit = 1 THEN credit_balance ELSE 0 END), 0) as total_receivables
            FROM bills 
            {date_condition}
        """
        
        summary = conn.execute(query, params).fetchone()
        
        # Get total items from sales table
        items_query = f"""
            SELECT COALESCE(SUM(quantity), 0) as total_items
            FROM sales 
            {date_condition.replace('created_at', 'sale_date')}
        """
        items_result = conn.execute(items_query, params).fetchone()
        
        conn.close()
        
        if summary:
            return {
                "total_sales": summary['total_sales'] or 0,
                "total_revenue": round(float(summary['total_revenue'] or 0), 2),
                "total_items": items_result['total_items'] if items_result else 0,
                "avg_sale_value": round(float(summary['avg_sale_value'] or 0), 2),
                "total_receivables": round(float(summary['total_receivables'] or 0), 2)
            }
        else:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "total_items": 0,
                "avg_sale_value": 0.0,
                "total_receivables": 0.0
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