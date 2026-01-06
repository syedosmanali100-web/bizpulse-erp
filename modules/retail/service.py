"""
Retail service
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection
from datetime import datetime, timedelta

class RetailService:
    
    def get_dashboard_stats(self, user_id=None):
        """Get comprehensive dashboard statistics with real-time data - Filtered by user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Build user filter condition
        user_filter = ""
        user_params = []
        if user_id:
            user_filter = "AND (business_owner_id = ? OR business_owner_id IS NULL)"
            user_params = [user_id]
        
        # Today's Sales (ALL bills including credit/partial)
        today_sales_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(total_amount), 0) as total_sales,
                COUNT(*) as transactions
            FROM bills 
            WHERE DATE(created_at) = ? {user_filter}
        ''', [today] + user_params).fetchone()
        
        # Today's Revenue (only PAID amounts - exclude unpaid credit)
        today_revenue_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(CASE 
                    WHEN is_credit = 0 OR payment_status = 'paid' THEN total_amount
                    WHEN is_credit = 1 AND payment_status != 'paid' THEN credit_paid_amount
                    ELSE 0
                END), 0) as revenue
            FROM bills 
            WHERE DATE(created_at) = ? {user_filter}
        ''', [today] + user_params).fetchone()
        
        # Today's Receivable (unpaid credit balance) - includes partial payments
        today_receivable_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(credit_balance), 0) as receivable
            FROM bills 
            WHERE DATE(created_at) = ? {user_filter}
            AND is_credit = 1
            AND credit_balance > 0
        ''', [today] + user_params).fetchone()
        
        # 🔥 TOTAL Receivable (ALL pending credit bills - not just today)
        total_receivable_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(credit_balance), 0) as total_receivable,
                COUNT(*) as pending_bills
            FROM bills 
            WHERE is_credit = 1
            AND credit_balance > 0 {user_filter}
        ''', user_params).fetchone()
        
        
        # Yesterday's Sales for comparison
        yesterday_sales_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(total_amount), 0) as total_sales
            FROM bills 
            WHERE DATE(created_at) = ? {user_filter}
        ''', [yesterday] + user_params).fetchone()
        
        # Yesterday's Revenue for comparison
        yesterday_revenue_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(CASE 
                    WHEN is_credit = 0 OR payment_status = 'paid' THEN total_amount
                    WHEN is_credit = 1 AND payment_status != 'paid' THEN credit_paid_amount
                    ELSE 0
                END), 0) as revenue
            FROM bills 
            WHERE DATE(created_at) = ? {user_filter}
        ''', [yesterday] + user_params).fetchone()
        
        # Yesterday's orders for comparison
        yesterday_orders = cursor.execute(f'''
            SELECT COUNT(*) as bills
            FROM bills
            WHERE DATE(created_at) = ? {user_filter}
        ''', [yesterday] + user_params).fetchone()
        
        # Today's Cost & Profit (from paid revenue only - proportional for partial payments)
        today_profit_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN b.is_credit = 0 OR b.payment_status = 'paid' THEN bi.total_price
                        WHEN b.is_credit = 1 AND b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.total_price * b.credit_paid_amount / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_sales,
                COALESCE(SUM(
                    CASE 
                        WHEN b.is_credit = 0 OR b.payment_status = 'paid' THEN bi.quantity * COALESCE(p.cost, 0)
                        WHEN b.is_credit = 1 AND b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.quantity * COALESCE(p.cost, 0) * b.credit_paid_amount / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_cost
            FROM bill_items bi
            LEFT JOIN products p ON bi.product_id = p.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE DATE(b.created_at) = ? {user_filter}
        ''', [today] + user_params).fetchone()
        
        # Receivable Profit (profit from unpaid portion - includes partial payments)
        today_receivable_profit_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN b.payment_status = 'unpaid' THEN bi.total_price
                        WHEN b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.total_price * b.credit_balance / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_sales,
                COALESCE(SUM(
                    CASE 
                        WHEN b.payment_status = 'unpaid' THEN bi.quantity * COALESCE(p.cost, 0)
                        WHEN b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.quantity * COALESCE(p.cost, 0) * b.credit_balance / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_cost
            FROM bill_items bi
            LEFT JOIN products p ON bi.product_id = p.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE DATE(b.created_at) = ? {user_filter}
            AND b.is_credit = 1
            AND b.credit_balance > 0
        ''', [today] + user_params).fetchone()
        
        # 🔥 TOTAL Receivable Profit (ALL pending credit bills - not just today)
        total_receivable_profit_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(
                    CASE 
                        WHEN b.payment_status = 'unpaid' THEN bi.total_price
                        WHEN b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.total_price * b.credit_balance / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_sales,
                COALESCE(SUM(
                    CASE 
                        WHEN b.payment_status = 'unpaid' THEN bi.quantity * COALESCE(p.cost, 0)
                        WHEN b.payment_status = 'partial' AND b.total_amount > 0 THEN 
                            (bi.quantity * COALESCE(p.cost, 0) * b.credit_balance / b.total_amount)
                        ELSE 0
                    END
                ), 0) as total_cost
            FROM bill_items bi
            LEFT JOIN products p ON bi.product_id = p.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE b.is_credit = 1
            AND b.credit_balance > 0 {user_filter}
        ''', user_params).fetchone()
        
        
        # Yesterday's Cost & Profit for comparison
        yesterday_profit_data = cursor.execute(f'''
            SELECT 
                COALESCE(SUM(bi.total_price), 0) as total_sales,
                COALESCE(SUM(bi.quantity * COALESCE(p.cost, 0)), 0) as total_cost
            FROM bill_items bi
            LEFT JOIN products p ON bi.product_id = p.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE DATE(b.created_at) = ? {user_filter}
            AND (b.is_credit = 0 OR b.payment_status = 'paid')
        ''', [yesterday] + user_params).fetchone()
        
        total_sales = float(today_profit_data['total_sales'])
        total_cost = float(today_profit_data['total_cost'])
        today_profit = total_sales - total_cost
        profit_margin = (today_profit / total_sales * 100) if total_sales > 0 else 0
        
        # Calculate today's receivable profit
        receivable_sales = float(today_receivable_profit_data['total_sales'])
        receivable_cost = float(today_receivable_profit_data['total_cost'])
        receivable_profit = receivable_sales - receivable_cost
        
        # 🔥 Calculate TOTAL receivable profit (all pending bills)
        total_receivable_sales = float(total_receivable_profit_data['total_sales'])
        total_receivable_cost = float(total_receivable_profit_data['total_cost'])
        total_receivable_profit = total_receivable_sales - total_receivable_cost
        
        yesterday_total_sales = float(yesterday_profit_data['total_sales'])
        yesterday_total_cost = float(yesterday_profit_data['total_cost'])
        yesterday_profit = yesterday_total_sales - yesterday_total_cost
        
        # Calculate percentage changes
        today_sales_value = float(today_sales_data['total_sales'])
        yesterday_sales_value = float(yesterday_sales_data['total_sales'])
        today_revenue_value = float(today_revenue_data['revenue'])
        yesterday_revenue_value = float(yesterday_revenue_data['revenue'])
        today_receivable_value = float(today_receivable_data['receivable'])
        total_receivable_value = float(total_receivable_data['total_receivable'])
        total_pending_bills = int(total_receivable_data['pending_bills'])
        
        # Debug logging (after all variables are defined)
        print(f"📊 [DASHBOARD] Today's Stats:")
        print(f"   Sales (Total): ₹{today_sales_value:.2f}")
        print(f"   Revenue (Paid): ₹{today_revenue_value:.2f}")
        print(f"   Receivable (Today): ₹{today_receivable_value:.2f}")
        print(f"   Receivable (TOTAL): ₹{total_receivable_value:.2f} ({total_pending_bills} bills)")
        print(f"   Profit (on Paid): ₹{today_profit:.2f}")
        print(f"   Receivable Profit (Today): ₹{receivable_profit:.2f}")
        print(f"   Receivable Profit (TOTAL): ₹{total_receivable_profit:.2f}")
        
        sales_change = 0
        if yesterday_sales_value > 0:
            sales_change = ((today_sales_value - yesterday_sales_value) / yesterday_sales_value) * 100
        elif today_sales_value > 0:
            sales_change = 100  # If no sales yesterday but sales today, it's 100% increase
            
        revenue_change = 0
        if yesterday_revenue_value > 0:
            revenue_change = ((today_revenue_value - yesterday_revenue_value) / yesterday_revenue_value) * 100
        elif today_revenue_value > 0:
            revenue_change = 100
            
        profit_change = 0
        if yesterday_profit > 0:
            profit_change = ((today_profit - yesterday_profit) / yesterday_profit) * 100
        elif today_profit > 0:
            profit_change = 100
            
        orders_change = 0
        today_orders_count = int(today_sales_data['transactions'])
        yesterday_orders_count = int(yesterday_orders['bills'])
        
        if yesterday_orders_count > 0:
            orders_change = ((today_orders_count - yesterday_orders_count) / yesterday_orders_count) * 100
        elif today_orders_count > 0:
            orders_change = 100
        
        # Total Products
        if user_id:
            total_products = cursor.execute('''
                SELECT COUNT(*) as count FROM products WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)
            ''', (user_id,)).fetchone()['count']
            
            # Low Stock Products (excluding out of stock)
            low_stock = cursor.execute('''
                SELECT COUNT(*) as count FROM products 
                WHERE stock > 0 AND stock <= min_stock AND is_active = 1 AND (user_id = ? OR user_id IS NULL)
            ''', (user_id,)).fetchone()['count']
            
            # Out of Stock Products
            out_of_stock = cursor.execute('''
                SELECT COUNT(*) as count FROM products 
                WHERE stock = 0 AND is_active = 1 AND (user_id = ? OR user_id IS NULL)
            ''', (user_id,)).fetchone()['count']
            
            # Total Customers
            total_customers = cursor.execute('''
                SELECT COUNT(*) as count FROM customers WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)
            ''', (user_id,)).fetchone()['count']
        else:
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
        recent_sales = cursor.execute(f'''
            SELECT 
                b.bill_number,
                b.total_amount,
                b.created_at,
                COALESCE(c.name, 'Walk-in Customer') as customer_name,
                strftime('%H:%M', b.created_at) as time
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE DATE(b.created_at) = ? {user_filter}
            ORDER BY b.created_at DESC
            LIMIT 10
        ''', [today] + user_params).fetchall()
        
        # Top Selling Products Today
        top_products = cursor.execute(f'''
            SELECT 
                s.product_name,
                SUM(s.quantity) as total_quantity,
                SUM(s.total_price) as total_sales,
                COUNT(DISTINCT s.bill_id) as times_sold
            FROM sales s
            WHERE s.sale_date = ? {user_filter.replace('business_owner_id', 's.business_owner_id')}
            GROUP BY s.product_id, s.product_name
            ORDER BY total_quantity DESC
            LIMIT 5
        ''', [today] + user_params).fetchall()
        
        # This Week's Revenue
        week_revenue = cursor.execute(f'''
            SELECT COALESCE(SUM(total_amount), 0) as revenue
            FROM bills 
            WHERE DATE(created_at) >= DATE('now', 'weekday 0', '-6 days') {user_filter}
        ''', user_params).fetchone()['revenue']
        
        # This Month's Revenue
        month_revenue = cursor.execute(f'''
            SELECT COALESCE(SUM(total_amount), 0) as revenue
            FROM bills 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now') {user_filter}
        ''', user_params).fetchone()['revenue']
        
        conn.close()
        
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            # Frontend expects these keys
            'today_sales': float(today_sales_value),  # Total sales including credit
            'today_revenue': float(today_revenue_value),  # Only paid amounts
            'today_receivable': float(today_receivable_value),  # TODAY's unpaid credit balance ONLY
            'total_receivable': float(total_receivable_value),  # 🔥 TOTAL receivable (ALL pending bills)
            'total_pending_bills': total_pending_bills,  # 🔥 Count of pending bills
            'today_orders': int(today_sales_data['transactions']),  # Total bills count
            'today_profit': round(today_profit, 2),
            'today_receivable_profit': round(receivable_profit, 2),  # TODAY's profit from unpaid credit ONLY
            'total_receivable_profit': round(total_receivable_profit, 2),  # 🔥 TOTAL receivable profit
            'today_cost': round(total_cost, 2),
            'profit_margin': round(profit_margin, 2),
            'week_revenue': float(week_revenue),
            'month_revenue': float(month_revenue),
            'total_products': total_products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'total_customers': total_customers,
            # Percentage changes for dashboard
            'sales_change_percent': round(sales_change, 1),
            'revenue_change_percent': round(revenue_change, 1),
            'orders_change_percent': round(orders_change, 1),
            'profit_change_percent': round(profit_change, 1),
            'profit_margin_percent': round(profit_margin, 1),
            # Also keep nested format for compatibility
            'today': {
                'sales': float(today_sales_value),  # Includes ALL bills
                'revenue': float(today_revenue_value),  # Only PAID amounts
                'receivable': float(today_receivable_value),  # TODAY's unpaid credit balance ONLY
                'transactions': int(today_sales_data['transactions']),
                'profit': round(today_profit, 2),
                'receivable_profit': round(receivable_profit, 2),  # TODAY's profit from unpaid credit ONLY
                'cost': round(total_cost, 2),
                'profit_margin': round(profit_margin, 2)
            },
            'total': {
                'receivable': float(total_receivable_value),  # 🔥 TOTAL receivable (ALL pending bills)
                'receivable_profit': round(total_receivable_profit, 2),  # 🔥 TOTAL receivable profit
                'pending_bills': total_pending_bills  # 🔥 Count of pending bills
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
        """Get recent activity for dashboard - FORMATTED FOR FRONTEND"""
        try:
            # Use the dashboard service to get properly formatted activities
            from modules.dashboard.service import DashboardService
            activities = DashboardService.get_recent_activities_only(limit=10)
            
            return {
                'success': True,
                'activities': activities,
                'count': len(activities)
            }
        except Exception as e:
            print(f"Error in get_recent_activity: {e}")
            # Fallback to manual formatting if dashboard service fails
            return self._get_recent_activity_fallback()
    
    def _get_recent_activity_fallback(self):
        """Fallback method to format activities manually"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        activities = []
        
        # Get recent bills and format as activities
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
            WHERE b.status = 'completed'
            ORDER BY b.created_at DESC
            LIMIT 8
        ''').fetchall()
        
        for bill in recent_bills:
            amount = float(bill['total_amount']) if bill['total_amount'] else 0
            activities.append({
                'id': f"sale-{bill['id']}",
                'title': 'Sale completed successfully',
                'description': f"₹{amount:,.0f} - {bill['customer_name']}",
                'amount': amount,
                'timestamp': bill['created_at'],
                'type': 'sale',
                'icon': '💰'
            })
        
        # Get recent products and format as activities
        recent_products = cursor.execute('''
            SELECT id, name, price, category, created_at
            FROM products
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        ''').fetchall()
        
        for product in recent_products:
            price = float(product['price']) if product['price'] else 0
            activities.append({
                'id': f"product-{product['id']}",
                'title': f"New product added: {product['name']}",
                'description': f"{product.get('category', 'General')} - ₹{price:,.0f}",
                'amount': 0,
                'timestamp': product['created_at'],
                'type': 'product',
                'icon': '📦'
            })
        
        # Get recent customers and format as activities
        recent_customers = cursor.execute('''
            SELECT id, name, phone, created_at
            FROM customers
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        ''').fetchall()
        
        for customer in recent_customers:
            phone_display = f" - {customer['phone']}" if customer['phone'] else ""
            activities.append({
                'id': f"customer-{customer['id']}",
                'title': 'New customer registered',
                'description': f"{customer['name']}{phone_display}",
                'amount': 0,
                'timestamp': customer['created_at'],
                'type': 'customer',
                'icon': '👤'
            })
        
        conn.close()
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            'success': True,
            'activities': activities[:10],  # Limit to 10 most recent
            'count': len(activities[:10])
        }