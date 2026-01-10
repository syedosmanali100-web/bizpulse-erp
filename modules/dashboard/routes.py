"""
Dashboard Routes - API endpoints for dashboard functionality
"""

from flask import Blueprint, jsonify, request, render_template
from modules.dashboard.service import DashboardService
from modules.dashboard.models import ActivityTracker, log_sale_activity, log_product_activity, log_customer_activity, log_order_activity
from modules.shared.auth_decorators import require_auth
import json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Initialize dashboard on first import
DashboardService.initialize()

# ============================================================================
# DASHBOARD API ENDPOINTS
# ============================================================================

@dashboard_bp.route('/premium-sections')
def get_premium_dashboard_sections():
    """Get premium dashboard sections - Recent Sales, Last Product, Last Customer, Last Bulk Order"""
    try:
        client_id = request.args.get('client_id')
        sections = DashboardService.get_premium_dashboard_sections(client_id=client_id)
        
        return jsonify({
            'success': True,
            'sections': sections
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/data')
def get_dashboard_data():
    """Get complete dashboard data including stats and recent activities"""
    try:
        client_id = request.args.get('client_id')
        data = DashboardService.get_dashboard_data(client_id=client_id)
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/recent-activities')
def get_recent_activities():
    """Get recent activities for dashboard widget"""
    try:
        limit = int(request.args.get('limit', 10))
        client_id = request.args.get('client_id')
        
        activities = DashboardService.get_recent_activities_only(limit=limit, client_id=client_id)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/search')
def search_activities():
    """Search activities by query"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 20))
        client_id = request.args.get('client_id')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        activities = DashboardService.search_activities(query, limit=limit, client_id=client_id)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities),
            'query': query
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/type/<activity_type>')
def get_activities_by_type(activity_type):
    """Get activities filtered by type"""
    try:
        limit = int(request.args.get('limit', 10))
        client_id = request.args.get('client_id')
        
        activities = DashboardService.get_activity_by_type(activity_type, limit=limit, client_id=client_id)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'count': len(activities),
            'type': activity_type
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/analytics')
def get_activity_analytics():
    """Get activity analytics for charts and insights"""
    try:
        days = int(request.args.get('days', 30))
        client_id = request.args.get('client_id')
        
        analytics = DashboardService.get_activity_analytics(days=days, client_id=client_id)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period_days': days
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ACTIVITY DROPDOWN ENDPOINTS
# ============================================================================

@dashboard_bp.route('/activities/sales')
def get_recent_sales():
    """Get recent sales for dropdown"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                b.id as bill_id,
                b.bill_number,
                b.total_amount,
                b.created_at,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name,
                b.payment_method
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.status = 'completed'
            ORDER BY b.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        sales = cursor.fetchall()
        conn.close()
        
        sales_data = []
        for sale in sales:
            amount = float(sale['total_amount']) if sale['total_amount'] else 0
            sales_data.append({
                'id': sale['bill_id'],
                'bill_number': sale['bill_number'],
                'amount': amount,
                'customer_name': sale['customer_name'],
                'payment_method': sale['payment_method'],
                'created_at': sale['created_at'],
                'time_ago': ActivityTracker._get_time_ago(sale['created_at'])
            })
        
        return jsonify({
            'success': True,
            'sales': sales_data,
            'count': len(sales_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/products')
def get_recent_products():
    """Get recent products for dropdown"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, price, category, stock, created_at
            FROM products
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        products = cursor.fetchall()
        conn.close()
        
        products_data = []
        for product in products:
            price = float(product['price']) if product['price'] else 0
            products_data.append({
                'id': product['id'],
                'name': product['name'],
                'price': price,
                'category': product['category'],
                'stock': product['stock'],
                'created_at': product['created_at'],
                'time_ago': ActivityTracker._get_time_ago(product['created_at'])
            })
        
        return jsonify({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/customers')
def get_recent_customers():
    """Get recent customers for dropdown"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, phone, address, created_at
            FROM customers
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        customers = cursor.fetchall()
        conn.close()
        
        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer['id'],
                'name': customer['name'],
                'phone': customer['phone'],
                'address': customer['address'],
                'created_at': customer['created_at'],
                'time_ago': ActivityTracker._get_time_ago(customer['created_at'])
            })
        
        return jsonify({
            'success': True,
            'customers': customers_data,
            'count': len(customers_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/inventory')
def get_recent_inventory():
    """Get recent inventory alerts for dropdown"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, stock, min_stock, price, category, created_at
            FROM products
            WHERE stock <= min_stock AND is_active = 1
            ORDER BY stock ASC, created_at DESC
            LIMIT ?
        ''', (limit,))
        
        inventory = cursor.fetchall()
        conn.close()
        
        inventory_data = []
        for item in inventory:
            price = float(item['price']) if item['price'] else 0
            stock_status = "Out of Stock" if item['stock'] == 0 else f"Low Stock ({item['stock']} left)"
            
            inventory_data.append({
                'id': item['id'],
                'name': item['name'],
                'stock': item['stock'],
                'min_stock': item['min_stock'],
                'price': price,
                'category': item['category'],
                'stock_status': stock_status,
                'created_at': item['created_at'],
                'time_ago': ActivityTracker._get_time_ago(item['created_at'])
            })
        
        return jsonify({
            'success': True,
            'inventory': inventory_data,
            'count': len(inventory_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/activities/orders')
def get_recent_orders():
    """Get recent bulk orders for dropdown"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                b.id as bill_id,
                b.bill_number,
                b.total_amount,
                b.created_at,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name,
                COUNT(bi.id) as item_count
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN bill_items bi ON b.id = bi.bill_id
            WHERE b.status = 'completed' AND b.total_amount > 1000
            GROUP BY b.id, b.bill_number, b.total_amount, b.created_at, b.customer_name, c.name
            ORDER BY b.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        orders = cursor.fetchall()
        conn.close()
        
        orders_data = []
        for order in orders:
            amount = float(order['total_amount']) if order['total_amount'] else 0
            orders_data.append({
                'id': order['bill_id'],
                'bill_number': order['bill_number'],
                'amount': amount,
                'customer_name': order['customer_name'],
                'item_count': order['item_count'],
                'created_at': order['created_at'],
                'time_ago': ActivityTracker._get_time_ago(order['created_at'])
            })
        
        return jsonify({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# ACTIVITY LOGGING ENDPOINTS
# ============================================================================

@dashboard_bp.route('/log-activity', methods=['POST'])
def log_activity():
    """Log a new activity (for manual logging or integrations)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('activity_type') or not data.get('title'):
            return jsonify({
                'success': False,
                'error': 'activity_type and title are required'
            }), 400
        
        activity_id = ActivityTracker.log_activity(
            activity_type=data['activity_type'],
            title=data['title'],
            description=data.get('description'),
            amount=float(data.get('amount', 0)),
            reference_id=data.get('reference_id'),
            reference_type=data.get('reference_type'),
            icon_type=data.get('icon_type', 'info'),
            user_id=data.get('user_id'),
            client_id=data.get('client_id'),
            metadata=data.get('metadata')
        )
        
        return jsonify({
            'success': True,
            'activity_id': activity_id,
            'message': 'Activity logged successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/log-sale', methods=['POST'])
def log_sale():
    """Log a sale activity"""
    try:
        data = request.get_json()
        
        if not data or not data.get('bill_id') or not data.get('amount'):
            return jsonify({
                'success': False,
                'error': 'bill_id and amount are required'
            }), 400
        
        log_sale_activity(
            bill_id=data['bill_id'],
            amount=float(data['amount']),
            customer_name=data.get('customer_name')
        )
        
        return jsonify({
            'success': True,
            'message': 'Sale activity logged successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/log-product', methods=['POST'])
def log_product():
    """Log a product activity"""
    try:
        data = request.get_json()
        
        if not data or not data.get('product_id') or not data.get('product_name'):
            return jsonify({
                'success': False,
                'error': 'product_id and product_name are required'
            }), 400
        
        log_product_activity(
            product_id=data['product_id'],
            product_name=data['product_name'],
            action=data.get('action', 'added')
        )
        
        return jsonify({
            'success': True,
            'message': 'Product activity logged successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/log-customer', methods=['POST'])
def log_customer():
    """Log a customer activity"""
    try:
        data = request.get_json()
        
        if not data or not data.get('customer_id') or not data.get('customer_name'):
            return jsonify({
                'success': False,
                'error': 'customer_id and customer_name are required'
            }), 400
        
        log_customer_activity(
            customer_id=data['customer_id'],
            customer_name=data['customer_name'],
            action=data.get('action', 'registered')
        )
        
        return jsonify({
            'success': True,
            'message': 'Customer activity logged successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/log-order', methods=['POST'])
def log_order():
    """Log an order activity"""
    try:
        data = request.get_json()
        
        if not data or not data.get('order_id') or not data.get('amount'):
            return jsonify({
                'success': False,
                'error': 'order_id and amount are required'
            }), 400
        
        log_order_activity(
            order_id=data['order_id'],
            amount=float(data['amount']),
            order_type=data.get('order_type', 'processed')
        )
        
        return jsonify({
            'success': True,
            'message': 'Order activity logged successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# DASHBOARD STATS ENDPOINTS
# ============================================================================

@dashboard_bp.route('/stats/sales')
def get_sales_stats():
    """Get sales statistics"""
    try:
        client_id = request.args.get('client_id')
        days = int(request.args.get('days', 30))
        
        from modules.dashboard.models import DashboardStats
        stats = DashboardStats.get_sales_stats(client_id=client_id, days=days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/stats/customers')
def get_customer_stats():
    """Get customer statistics"""
    try:
        client_id = request.args.get('client_id')
        
        from modules.dashboard.models import DashboardStats
        stats = DashboardStats.get_customer_stats(client_id=client_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/stats/inventory')
def get_inventory_stats():
    """Get inventory statistics"""
    try:
        client_id = request.args.get('client_id')
        
        from modules.dashboard.models import DashboardStats
        stats = DashboardStats.get_inventory_stats(client_id=client_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# DASHBOARD WIDGET ENDPOINTS (for embedding in other pages)
# ============================================================================

@dashboard_bp.route('/widget/recent-activities')
def recent_activities_widget():
    """Get recent activities widget HTML"""
    try:
        limit = int(request.args.get('limit', 5))
        client_id = request.args.get('client_id')
        
        activities = DashboardService.get_recent_activities_only(limit=limit, client_id=client_id)
        
        # Return JSON for AJAX requests, HTML for direct requests
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({
                'success': True,
                'activities': activities
            })
        else:
            return render_template('dashboard_widgets/recent_activities.html', activities=activities)
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            return f"<div class='error'>Error loading activities: {str(e)}</div>", 500

# ============================================================================
# UNIVERSAL SEARCH ENDPOINT
# ============================================================================

@dashboard_bp.route('/search')
def universal_search():
    """Universal search across all data - customers, products, sales, modules"""
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400
        
        from modules.shared.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_results = {
            'customers': [],
            'products': [],
            'sales': [],
            'modules': [],
            'total_results': 0
        }
        
        # 1. Search Customers (by name, phone)
        cursor.execute('''
            SELECT id, name, phone, address, created_at
            FROM customers
            WHERE is_active = 1 
            AND (name LIKE ? OR phone LIKE ? OR address LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        customers = cursor.fetchall()
        for customer in customers:
            search_results['customers'].append({
                'id': customer['id'],
                'type': 'customer',
                'title': customer['name'],
                'subtitle': f"Phone: {customer['phone'] or 'N/A'}",
                'description': customer['address'] or 'No address',
                'icon': '👤',
                'url': f'/customers/{customer["id"]}',
                'created_at': customer['created_at']
            })
        
        # 2. Search Products (by name, category)
        cursor.execute('''
            SELECT id, name, category, price, stock, created_at
            FROM products
            WHERE is_active = 1 
            AND (name LIKE ? OR category LIKE ?)
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        products = cursor.fetchall()
        for product in products:
            price = float(product['price']) if product['price'] else 0
            search_results['products'].append({
                'id': product['id'],
                'type': 'product',
                'title': product['name'],
                'subtitle': f"₹{price:,.0f} • Stock: {product['stock']}",
                'description': product['category'],
                'icon': '📦',
                'url': f'/products/{product["id"]}',
                'created_at': product['created_at']
            })
        
        # 3. Search Sales/Bills (by bill number, customer name, amount)
        cursor.execute('''
            SELECT 
                b.id, b.bill_number, b.total_amount, b.created_at,
                COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.status = 'completed'
            AND (b.bill_number LIKE ? OR b.customer_name LIKE ? OR c.name LIKE ?)
            ORDER BY b.created_at DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
        
        sales = cursor.fetchall()
        for sale in sales:
            amount = float(sale['total_amount']) if sale['total_amount'] else 0
            search_results['sales'].append({
                'id': sale['id'],
                'type': 'sale',
                'title': sale['bill_number'],
                'subtitle': f"₹{amount:,.0f} • {sale['customer_name']}",
                'description': f"Sale completed on {sale['created_at'][:10]}",
                'icon': '💰',
                'url': f'/bills/{sale["id"]}',
                'created_at': sale['created_at']
            })
        
        conn.close()
        
        # 4. Search Modules/Navigation (predefined list)
        modules = [
            {'name': 'dashboard', 'title': 'Dashboard', 'url': '/retail/dashboard', 'icon': '📊'},
            {'name': 'sales', 'title': 'Sales Management', 'url': '/retail/sales', 'icon': '💰'},
            {'name': 'products', 'title': 'Product Management', 'url': '/products', 'icon': '📦'},
            {'name': 'customers', 'title': 'Customer Management', 'url': '/customers', 'icon': '👤'},
            {'name': 'inventory', 'title': 'Inventory Management', 'url': '/retail/inventory', 'icon': '📋'},
            {'name': 'billing', 'title': 'Billing System', 'url': '/billing', 'icon': '🧾'},
            {'name': 'reports', 'title': 'Reports & Analytics', 'url': '/reports', 'icon': '📈'},
            {'name': 'credit', 'title': 'Credit Management', 'url': '/retail/credit', 'icon': '💳'},
            {'name': 'profile', 'title': 'Profile Settings', 'url': '/retail/profile', 'icon': '⚙️'}
        ]
        
        for module in modules:
            if (query.lower() in module['name'].lower() or 
                query.lower() in module['title'].lower()):
                search_results['modules'].append({
                    'id': module['name'],
                    'type': 'module',
                    'title': module['title'],
                    'subtitle': f"Navigate to {module['title']}",
                    'description': f"Go to {module['name']} section",
                    'icon': module['icon'],
                    'url': module['url'],
                    'created_at': None
                })
        
        # Calculate total results
        search_results['total_results'] = (
            len(search_results['customers']) + 
            len(search_results['products']) + 
            len(search_results['sales']) + 
            len(search_results['modules'])
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': search_results,
            'total_results': search_results['total_results']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@dashboard_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'service': 'Dashboard API',
        'status': 'healthy',
        'version': '1.0.0'
    })

@dashboard_bp.route('/activity-types')
def get_activity_types():
    """Get available activity types"""
    return jsonify({
        'success': True,
        'activity_types': [
            {'type': 'sale', 'label': 'Sales', 'icon': 'success'},
            {'type': 'product', 'label': 'Products', 'icon': 'product'},
            {'type': 'customer', 'label': 'Customers', 'icon': 'user'},
            {'type': 'order', 'label': 'Orders', 'icon': 'order'},
            {'type': 'inventory', 'label': 'Inventory', 'icon': 'inventory'},
            {'type': 'payment', 'label': 'Payments', 'icon': 'payment'},
            {'type': 'system', 'label': 'System', 'icon': 'info'}
        ]
    })