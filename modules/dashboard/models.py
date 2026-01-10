"""
Dashboard Models - Real-time Activity Tracking
"""

from modules.shared.database import get_db_connection, generate_id
from datetime import datetime, timedelta
import json

class ActivityTracker:
    """Track and manage recent activities for dashboard"""
    
    @staticmethod
    def init_activity_table():
        """Initialize the activity tracking table"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_activities (
                id TEXT PRIMARY KEY,
                activity_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                amount REAL DEFAULT 0,
                currency TEXT DEFAULT 'INR',
                reference_id TEXT,
                reference_type TEXT,
                icon_type TEXT DEFAULT 'info',
                user_id TEXT,
                client_id TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def log_activity(activity_type, title, description=None, amount=0, reference_id=None, 
                    reference_type=None, icon_type='info', user_id=None, client_id=None, metadata=None):
        """Log a new activity"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        activity_id = generate_id()
        metadata_json = json.dumps(metadata or {})
        
        cursor.execute('''
            INSERT INTO recent_activities 
            (id, activity_type, title, description, amount, reference_id, reference_type, 
             icon_type, user_id, client_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (activity_id, activity_type, title, description, amount, reference_id, 
              reference_type, icon_type, user_id, client_id, metadata_json, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return activity_id
    
    @staticmethod
    def get_recent_activities(limit=10, client_id=None):
        """Get recent activities"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, activity_type, title, description, amount, currency,
                   reference_id, reference_type, icon_type, created_at
            FROM recent_activities
        '''
        params = []
        
        if client_id:
            query += ' WHERE (client_id = ? OR client_id IS NULL)'
            params.append(client_id)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        activities = cursor.fetchall()
        
        conn.close()
        
        result = []
        for activity in activities:
            activity_dict = dict(activity)
            activity_dict['time_ago'] = ActivityTracker._get_time_ago(activity_dict['created_at'])
            result.append(activity_dict)
        
        return result
    
    @staticmethod
    def get_premium_dashboard_sections(client_id=None):
        """Get 4 premium dashboard sections: Recent Sales, Last Product, Last Customer, Last Bulk Order"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        dashboard_data = {
            'recent_sales': ActivityTracker._get_recent_sales_section(cursor),
            'last_product': ActivityTracker._get_last_product_section(cursor),
            'last_customer': ActivityTracker._get_last_customer_section(cursor),
            'last_bulk_order': ActivityTracker._get_last_bulk_order_section(cursor)
        }
        
        conn.close()
        return dashboard_data
    
    @staticmethod
    def _get_recent_sales_section(cursor):
        """Get recent sales section data"""
        cursor.execute('''
            SELECT 
                b.id as bill_id,
                b.bill_number,
                b.total_amount,
                b.created_at,
                b.payment_method,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name,
                COUNT(bi.id) as item_count
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN bill_items bi ON b.id = bi.bill_id
            WHERE b.status = 'completed'
            GROUP BY b.id, b.bill_number, b.total_amount, b.created_at, b.payment_method, b.customer_name, c.name
            ORDER BY b.created_at DESC
            LIMIT 5
        ''')
        
        sales = cursor.fetchall()
        sales_data = []
        
        for sale in sales:
            amount = float(sale['total_amount']) if sale['total_amount'] else 0
            
            # Determine sale type based on amount
            if amount > 25000:
                sale_type = "Enterprise Sale"
                type_class = "enterprise"
            elif amount > 10000:
                sale_type = "Bulk Sale"
                type_class = "bulk"
            elif sale['payment_method'] == 'credit':
                sale_type = "Credit Sale"
                type_class = "credit"
            else:
                sale_type = "Regular Sale"
                type_class = "regular"
            
            sales_data.append({
                'id': sale['bill_id'],
                'bill_number': sale['bill_number'],
                'amount': amount,
                'customer_name': sale['customer_name'],
                'payment_method': sale['payment_method'],
                'item_count': sale['item_count'],
                'sale_type': sale_type,
                'type_class': type_class,
                'created_at': sale['created_at'],
                'time_ago': ActivityTracker._get_time_ago(sale['created_at'])
            })
        
        return {
            'title': 'Recent Sales',
            'icon': '💰',
            'color': 'success',
            'data': sales_data,
            'total_count': len(sales_data)
        }
    
    @staticmethod
    def _get_last_product_section(cursor):
        """Get last product added section data"""
        cursor.execute('''
            SELECT id, name, price, cost, category, stock, min_stock, created_at
            FROM products
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        product = cursor.fetchone()
        
        if not product:
            return {
                'title': 'Last Product Added',
                'icon': '📦',
                'color': 'primary',
                'data': None,
                'message': 'No products found'
            }
        
        price = float(product['price']) if product['price'] else 0
        cost = float(product['cost']) if product['cost'] else 0
        profit_margin = ((price - cost) / price * 100) if price > 0 else 0
        
        # Determine stock status
        if product['stock'] == 0:
            stock_status = "Out of Stock"
            stock_class = "danger"
        elif product['stock'] <= product['min_stock']:
            stock_status = "Low Stock"
            stock_class = "warning"
        else:
            stock_status = "In Stock"
            stock_class = "success"
        
        return {
            'title': 'Last Product Added',
            'icon': '📦',
            'color': 'primary',
            'data': {
                'id': product['id'],
                'name': product['name'],
                'price': price,
                'cost': cost,
                'category': product['category'],
                'stock': product['stock'],
                'min_stock': product['min_stock'],
                'profit_margin': round(profit_margin, 1),
                'stock_status': stock_status,
                'stock_class': stock_class,
                'created_at': product['created_at'],
                'time_ago': ActivityTracker._get_time_ago(product['created_at'])
            }
        }
    
    @staticmethod
    def _get_last_customer_section(cursor):
        """Get last customer added section data"""
        cursor.execute('''
            SELECT 
                c.id, c.name, c.phone, c.address, c.created_at,
                COUNT(b.id) as total_orders,
                COALESCE(SUM(b.total_amount), 0) as total_spent
            FROM customers c
            LEFT JOIN bills b ON c.id = b.customer_id AND b.status = 'completed'
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.phone, c.address, c.created_at
            ORDER BY c.created_at DESC
            LIMIT 1
        ''')
        
        customer = cursor.fetchone()
        
        if not customer:
            return {
                'title': 'Last Customer Added',
                'icon': '👤',
                'color': 'info',
                'data': None,
                'message': 'No customers found'
            }
        
        total_spent = float(customer['total_spent']) if customer['total_spent'] else 0
        
        # Determine customer type based on spending
        if total_spent > 50000:
            customer_type = "VIP Customer"
            type_class = "vip"
        elif total_spent > 20000:
            customer_type = "Premium Customer"
            type_class = "premium"
        elif total_spent > 5000:
            customer_type = "Regular Customer"
            type_class = "regular"
        else:
            customer_type = "New Customer"
            type_class = "new"
        
        return {
            'title': 'Last Customer Added',
            'icon': '👤',
            'color': 'info',
            'data': {
                'id': customer['id'],
                'name': customer['name'],
                'phone': customer['phone'],
                'address': customer['address'],
                'total_orders': customer['total_orders'],
                'total_spent': total_spent,
                'customer_type': customer_type,
                'type_class': type_class,
                'created_at': customer['created_at'],
                'time_ago': ActivityTracker._get_time_ago(customer['created_at'])
            }
        }
    
    @staticmethod
    def _get_last_bulk_order_section(cursor):
        """Get last bulk order section data"""
        cursor.execute('''
            SELECT 
                b.id as bill_id,
                b.bill_number,
                b.total_amount,
                b.created_at,
                b.payment_method,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name,
                COUNT(bi.id) as item_count,
                SUM(bi.quantity) as total_quantity
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN bill_items bi ON b.id = bi.bill_id
            WHERE b.status = 'completed' AND b.total_amount > 10000
            GROUP BY b.id, b.bill_number, b.total_amount, b.created_at, b.payment_method, b.customer_name, c.name
            ORDER BY b.created_at DESC
            LIMIT 1
        ''')
        
        order = cursor.fetchone()
        
        if not order:
            return {
                'title': 'Last Bulk Order',
                'icon': '🛒',
                'color': 'warning',
                'data': None,
                'message': 'No bulk orders found'
            }
        
        amount = float(order['total_amount']) if order['total_amount'] else 0
        
        # Determine order type based on amount
        if amount > 100000:
            order_type = "Enterprise Order"
            type_class = "enterprise"
        elif amount > 50000:
            order_type = "Wholesale Order"
            type_class = "wholesale"
        else:
            order_type = "Bulk Order"
            type_class = "bulk"
        
        return {
            'title': 'Last Bulk Order',
            'icon': '🛒',
            'color': 'warning',
            'data': {
                'id': order['bill_id'],
                'bill_number': order['bill_number'],
                'amount': amount,
                'customer_name': order['customer_name'],
                'payment_method': order['payment_method'],
                'item_count': order['item_count'],
                'total_quantity': order['total_quantity'],
                'order_type': order_type,
                'type_class': type_class,
                'created_at': order['created_at'],
                'time_ago': ActivityTracker._get_time_ago(order['created_at'])
            }
        }
    
    @staticmethod
    def _get_time_ago(timestamp_str):
        """Calculate time ago from timestamp"""
        try:
            if isinstance(timestamp_str, str):
                # Handle different timestamp formats
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            else:
                timestamp = timestamp_str
            
            now = datetime.now()
            diff = now - timestamp
            
            if diff.days > 0:
                if diff.days == 1:
                    return "1 day ago"
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                if hours == 1:
                    return "1 hour ago"
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                if minutes == 1:
                    return "1 minute ago"
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        except:
            return "Recently"

# Activity logging helper functions
def log_sale_activity(bill_id, amount, customer_name=None):
    """Log a sale completion activity with diverse titles based on amount and customer"""
    customer_display = customer_name or 'Walk-in Customer'
    
    # Diverse titles based on amount and customer type
    if amount > 25000:
        title = "High-value sale completed"
    elif amount > 10000:
        title = "Bulk order completed"
    elif customer_display == 'Walk-in Customer':
        title = "Walk-in sale completed"
    elif 'Corporate' in customer_display or 'Ltd' in customer_display:
        title = "Corporate sale finalized"
    else:
        title = "Sale completed successfully"
    
    description = f"₹{amount:,.0f} - {customer_display}"
    
    ActivityTracker.log_activity(
        activity_type='sale',
        title=title,
        description=description,
        amount=amount,
        reference_id=bill_id,
        reference_type='bill',
        icon_type='success',
        metadata={
            'customer_name': customer_display,
            'formatted_amount': f"₹{amount:,.0f}",
            'is_high_value': amount > 25000,
            'has_dropdown': True,
            'dropdown_type': 'sales'
        }
    )

def log_product_activity(product_id, product_name, action='added', category=None, price=None):
    """Log product-related activity with diverse titles based on category and price"""
    
    # Diverse titles based on category and action
    if category in ['Electronics', 'Computer Accessories']:
        title = f"Tech product {action}: {product_name}"
    elif category in ['Clothing', 'Footwear', 'Sportswear']:
        title = f"Fashion item {action}: {product_name}"
    elif category in ['Groceries', 'Health Foods', 'Beverages']:
        title = f"Fresh stock {action}: {product_name}"
    elif price and price > 5000:
        title = f"Premium product {action}: {product_name}"
    else:
        title = f"New product {action}: {product_name}"
    
    # Create detailed description
    description_parts = []
    if category:
        description_parts.append(category)
    if price:
        description_parts.append(f"₹{price:,.0f}")
    
    description = " - ".join(description_parts) if description_parts else None
    
    ActivityTracker.log_activity(
        activity_type='product',
        title=title,
        description=description,
        reference_id=product_id,
        reference_type='product',
        icon_type='product',
        metadata={
            'action': action,
            'category': category,
            'price': price,
            'is_premium': price and price > 5000,
            'has_dropdown': True,
            'dropdown_type': 'products'
        }
    )

def log_customer_activity(customer_id, customer_name, action='registered', phone=None):
    """Log customer-related activity with diverse titles based on customer type"""
    
    # Diverse titles based on customer characteristics
    if 'Corporate' in customer_name or 'Ltd' in customer_name or 'Pvt' in customer_name:
        title = f"Corporate client {action}"
    elif phone and phone.startswith('9'):
        title = f"Premium customer {action}"
    elif action == 'registered':
        title = "New customer onboarded"
    else:
        title = f"Customer {action}"
    
    # Create detailed description
    description = customer_name
    if phone:
        description += f" - {phone}"
    
    ActivityTracker.log_activity(
        activity_type='customer',
        title=title,
        description=description,
        reference_id=customer_id,
        reference_type='customer',
        icon_type='user',
        metadata={
            'action': action,
            'phone': phone,
            'is_corporate': 'Corporate' in customer_name or 'Ltd' in customer_name,
            'has_dropdown': True,
            'dropdown_type': 'customers'
        }
    )

def log_order_activity(order_id, amount, order_type='processed', customer_name=None, item_count=None):
    """Log order-related activity with diverse titles based on order characteristics"""
    
    # Diverse titles based on amount and type
    if amount > 50000:
        title = f"Enterprise order {order_type}"
    elif amount > 25000:
        title = f"Wholesale order {order_type}"
    elif item_count and item_count > 20:
        title = f"Multi-item order {order_type}"
    else:
        title = f"Bulk order {order_type}"
    
    # Create detailed description
    description_parts = [f"₹{amount:,.0f}"]
    if customer_name:
        description_parts.append(customer_name)
    if item_count:
        description_parts.append(f"({item_count} items)")
    
    description = " - ".join(description_parts)
    
    ActivityTracker.log_activity(
        activity_type='order',
        title=title,
        description=description,
        amount=amount,
        reference_id=order_id,
        reference_type='order',
        icon_type='order',
        metadata={
            'order_type': order_type,
            'customer_name': customer_name,
            'item_count': item_count,
            'is_bulk': True,
            'is_enterprise': amount > 50000,
            'formatted_amount': f"₹{amount:,.0f}",
            'has_dropdown': True,
            'dropdown_type': 'orders'
        }
    )

class DashboardStats:
    """Dashboard statistics and metrics"""
    
    @staticmethod
    def get_sales_stats(client_id=None, days=30):
        """Get sales statistics for dashboard"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Total sales today (ALL bills including credit)
        # Revenue today (only PAID amounts)
        cursor.execute('''
            SELECT 
                COALESCE(SUM(total_amount), 0) as today_sales,
                COALESCE(SUM(CASE 
                    WHEN payment_status = 'COMPLETED' THEN total_amount
                    WHEN payment_status = 'PARTIAL' THEN COALESCE(paid_amount, 0)
                    ELSE 0
                END), 0) as today_revenue,
                COUNT(*) as today_orders
            FROM bills 
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_stats = cursor.fetchone()
        
        # Total sales this month (ALL bills including credit)
        # Revenue this month (only PAID amounts)
        cursor.execute('''
            SELECT 
                COALESCE(SUM(total_amount), 0) as month_sales,
                COALESCE(SUM(CASE 
                    WHEN payment_status = 'COMPLETED' THEN total_amount
                    WHEN payment_status = 'PARTIAL' THEN COALESCE(paid_amount, 0)
                    ELSE 0
                END), 0) as month_revenue,
                COUNT(*) as month_orders
            FROM bills 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        ''')
        month_stats = cursor.fetchone()
        
        # Recent orders
        cursor.execute('''
            SELECT COUNT(*) as pending_orders
            FROM bills 
            WHERE payment_status = 'pending'
        ''')
        pending_orders = cursor.fetchone()
        
        # Low stock products
        cursor.execute('''
            SELECT COUNT(*) as low_stock_count
            FROM products 
            WHERE stock <= min_stock AND is_active = 1
        ''')
        low_stock = cursor.fetchone()
        
        # Top selling products this month
        cursor.execute('''
            SELECT p.name, SUM(bi.quantity) as total_sold, SUM(bi.total_price) as revenue
            FROM bill_items bi
            JOIN products p ON bi.product_id = p.id
            JOIN bills b ON bi.bill_id = b.id
            WHERE strftime('%Y-%m', b.created_at) = strftime('%Y-%m', 'now')
            GROUP BY p.id, p.name
            ORDER BY total_sold DESC
            LIMIT 5
        ''')
        top_products = cursor.fetchall()
        
        conn.close()
        
        return {
            'today': {
                'sales': float(today_stats['today_sales'] or 0),
                'revenue': float(today_stats['today_revenue'] or 0),
                'orders': int(today_stats['today_orders'] or 0)
            },
            'month': {
                'sales': float(month_stats['month_sales'] or 0),
                'revenue': float(month_stats['month_revenue'] or 0),
                'orders': int(month_stats['month_orders'] or 0)
            },
            'pending_orders': int(pending_orders['pending_orders'] or 0),
            'low_stock_count': int(low_stock['low_stock_count'] or 0),
            'top_products': [dict(product) for product in top_products]
        }
    
    @staticmethod
    def get_customer_stats(client_id=None):
        """Get customer statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total customers
        cursor.execute('SELECT COUNT(*) as total FROM customers WHERE is_active = 1')
        total_customers = cursor.fetchone()['total']
        
        # New customers this month
        cursor.execute('''
            SELECT COUNT(*) as new_customers
            FROM customers 
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            AND is_active = 1
        ''')
        new_customers = cursor.fetchone()['new_customers']
        
        # Top customers by purchases
        cursor.execute('''
            SELECT c.name, c.phone, COALESCE(SUM(b.total_amount), 0) as total_purchases
            FROM customers c
            LEFT JOIN bills b ON c.id = b.customer_id AND b.status = 'completed'
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.phone
            ORDER BY total_purchases DESC
            LIMIT 5
        ''')
        top_customers = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_customers': total_customers,
            'new_customers': new_customers,
            'top_customers': [dict(customer) for customer in top_customers]
        }
    
    @staticmethod
    def get_inventory_stats(client_id=None):
        """Get inventory statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total products
        cursor.execute('SELECT COUNT(*) as total FROM products WHERE is_active = 1')
        total_products = cursor.fetchone()['total']
        
        # Low stock products
        cursor.execute('''
            SELECT COUNT(*) as low_stock
            FROM products 
            WHERE stock <= min_stock AND is_active = 1
        ''')
        low_stock_count = cursor.fetchone()['low_stock']
        
        # Out of stock products
        cursor.execute('''
            SELECT COUNT(*) as out_of_stock
            FROM products 
            WHERE stock = 0 AND is_active = 1
        ''')
        out_of_stock = cursor.fetchone()['out_of_stock']
        
        # Total inventory value
        cursor.execute('''
            SELECT COALESCE(SUM(stock * cost), 0) as inventory_value
            FROM products 
            WHERE is_active = 1
        ''')
        inventory_value = cursor.fetchone()['inventory_value']
        
        conn.close()
        
        return {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock': out_of_stock,
            'inventory_value': float(inventory_value or 0)
        }