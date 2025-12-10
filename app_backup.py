from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
import uuid
import hashlib
from functools import wraps

app = Flask(__name__)
# Enable CORS for all domains and methods (for mobile app)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Database initialization
def init_db():
    conn = sqlite3.connect('billing.db')
    cursor = conn.cursor()
    
    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            cost REAL,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'piece',
            business_type TEXT DEFAULT 'both',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            credit_limit REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            total_purchases REAL DEFAULT 0,
            customer_type TEXT DEFAULT 'regular',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id TEXT PRIMARY KEY,
            bill_number TEXT UNIQUE,
            customer_id TEXT,
            business_type TEXT,
            subtotal REAL,
            tax_amount REAL,
            discount_amount REAL DEFAULT 0,
            total_amount REAL,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Bill items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id TEXT PRIMARY KEY,
            bill_id TEXT,
            product_id TEXT,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_price REAL,
            tax_rate REAL DEFAULT 18,
            FOREIGN KEY (bill_id) REFERENCES bills (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            bill_id TEXT,
            method TEXT,
            amount REAL,
            reference TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id) REFERENCES bills (id)
        )
    ''')
    
    # Hotel guests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotel_guests (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            id_proof TEXT,
            room_number TEXT,
            room_type TEXT,
            check_in_date DATE,
            check_out_date DATE,
            guest_count INTEGER DEFAULT 1,
            total_bill REAL DEFAULT 0,
            status TEXT DEFAULT 'booked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Hotel services table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotel_services (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            rate REAL,
            description TEXT,
            tax_rate REAL DEFAULT 18,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            business_name TEXT,
            business_address TEXT,
            business_type TEXT DEFAULT 'retail',
            gst_number TEXT,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add sample data
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        # Sample products
        sample_products = [
            ('prod-1', 'P001', 'Rice (1kg)', 'Groceries', 80.0, 70.0, 100, 10, 'kg', 'retail'),
            ('prod-2', 'P002', 'Wheat Flour (1kg)', 'Groceries', 45.0, 40.0, 50, 5, 'kg', 'retail'),
            ('prod-3', 'P003', 'Sugar (1kg)', 'Groceries', 55.0, 50.0, 30, 5, 'kg', 'retail'),
            ('prod-4', 'P004', 'Tea Powder (250g)', 'Beverages', 120.0, 100.0, 25, 3, 'packet', 'retail'),
            ('prod-5', 'P005', 'Cooking Oil (1L)', 'Groceries', 150.0, 140.0, 20, 2, 'liter', 'retail'),
            ('prod-6', 'P006', 'Milk (1L)', 'Dairy', 60.0, 55.0, 15, 2, 'liter', 'retail'),
            ('prod-7', 'P007', 'Bread', 'Bakery', 25.0, 20.0, 40, 5, 'piece', 'retail'),
            ('prod-8', 'P008', 'Eggs (12 pcs)', 'Dairy', 84.0, 75.0, 30, 3, 'dozen', 'retail'),
            ('prod-9', 'P009', 'Onions (1kg)', 'Vegetables', 35.0, 30.0, 50, 5, 'kg', 'retail'),
            ('prod-10', 'P010', 'Potatoes (1kg)', 'Vegetables', 25.0, 20.0, 60, 10, 'kg', 'retail')
        ]
        
        for product in sample_products:
            cursor.execute('''
                INSERT INTO products (id, code, name, category, price, cost, stock, min_stock, unit, business_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)
    
    # Sample customers
    cursor.execute('SELECT COUNT(*) FROM customers')
    if cursor.fetchone()[0] == 0:
        sample_customers = [
            ('cust-1', 'Rajesh Kumar', '+91 9876543210', 'rajesh@email.com', '123 Main Street, City', 5000.0),
            ('cust-2', 'Priya Sharma', '+91 9876543211', 'priya@email.com', '456 Park Avenue, City', 3000.0),
            ('cust-3', 'Amit Singh', '+91 9876543212', 'amit@email.com', '789 Garden Road, City', 2000.0),
            ('cust-4', 'Sunita Devi', '+91 9876543213', 'sunita@email.com', '321 Market Street, City', 4000.0),
            ('cust-5', 'Vikram Patel', '+91 9876543214', 'vikram@email.com', '654 Commercial Area, City', 6000.0)
        ]
        
        for customer in sample_customers:
            cursor.execute('''
                INSERT INTO customers (id, name, phone, email, address, credit_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', customer)
    
    conn.commit()
    conn.close()

# Helper functions
def get_db_connection():
    conn = sqlite3.connect('billing.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_id():
    return str(uuid.uuid4())

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For demo purposes, we'll skip actual JWT validation
        # In production, implement proper JWT token validation
        request.current_user_id = "demo-user-id"
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/mobile-test')
def mobile_test():
    return render_template('mobile_test.html')

# PWA Support Routes
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/offline.html')
def offline():
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BizPulse - Offline</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #F7E8EC; }
        .offline { color: #732C3F; }
        .btn { background: #732C3F; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="offline">
        <h1>🛒 BizPulse</h1>
        <h2>You're offline</h2>
        <p>Please check your internet connection and try again.</p>
        <button class="btn" onclick="window.location.reload()">Try Again</button>
    </div>
</body>
</html>'''

@app.route('/mobile')
def mobile_app():
    return render_template('mobile_app.html')

@app.route('/mobile-fixed')
def mobile_app_fixed():
    return send_from_directory('.', 'mobile_app_fixed.html')

@app.route('/mobile-pwa')
def mobile_pwa():
    response = send_from_directory('.', 'mobile_web_app.html')
    # Add cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/version')
def api_version():
    """API endpoint for version checking - enables auto-updates"""
    return jsonify({
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat(),
        "features": ["billing", "products", "customers", "reports"]
    })

# Retail Management module routes
@app.route('/retail/products')
def retail_products_page():
    return render_template('retail_products.html')

@app.route('/retail/customers')
def retail_customers():
    return render_template('retail_customers.html')

@app.route('/retail/billing')
def retail_billing():
    return render_template('retail_billing.html')

@app.route('/retail/dashboard')
def retail_dashboard():
    return render_template('retail_dashboard.html')

@app.route('/retail/profile')
def retail_profile():
    return render_template('retail_profile.html')

@app.route('/retail/sales')
def retail_sales():
    return render_template('retail_sales.html')

# Hotel module routes
@app.route('/hotel/dashboard')
def hotel_dashboard():
    return render_template('hotel_dashboard.html')

@app.route('/hotel/profile')
def hotel_profile():
    return render_template('hotel_profile.html')

# API Routes
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Demo login - in production, validate against database
    if email == "admin@demo.com" and password == "demo123":
        return jsonify({
            "message": "Login successful",
            "token": "demo-jwt-token",
            "user": {
                "id": "demo-user-id",
                "email": email,
                "business_type": "both"
            }
        })
    
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    user_id = generate_id()
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO users (id, email, password_hash, business_name, business_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id, data['email'], hash_password(data['password']),
            data.get('business_name', ''), data.get('business_type', 'retail')
        ))
        conn.commit()
        return jsonify({"message": "Registration successful", "user_id": user_id})
    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists"}), 400
    finally:
        conn.close()

# Products API
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

@app.route('/api/products', methods=['POST'])
@require_auth
def add_product():
    data = request.json
    product_id = generate_id()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO products (id, code, name, category, price, cost, stock, min_stock, unit, business_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        product_id, data['code'], data['name'], data.get('category', 'General'),
        data['price'], data.get('cost', 0), data.get('stock', 0),
        data.get('min_stock', 0), data.get('unit', 'piece'), data.get('business_type', 'both')
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product added successfully", "id": product_id}), 201

# Customers API
@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in customers])

@app.route('/api/customers', methods=['POST'])
@require_auth
def add_customer():
    data = request.json
    customer_id = generate_id()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO customers (id, name, phone, email, address, credit_limit)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        customer_id, data['name'], data.get('phone'), data.get('email'),
        data.get('address'), data.get('credit_limit', 1000)
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Customer added successfully", "id": customer_id}), 201

# Bills API (Enhanced version with hourly tracking is defined later)

@app.route('/api/bills', methods=['GET'])
def get_bills():
    conn = get_db_connection()
    bills = conn.execute('''
        SELECT b.*, c.name as customer_name 
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in bills])

@app.route('/api/bills/<bill_id>/items', methods=['GET'])
def get_bill_items(bill_id):
    conn = get_db_connection()
    items = conn.execute('''
        SELECT * FROM bill_items WHERE bill_id = ?
    ''', (bill_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in items])

# Reports API
@app.route('/api/reports/sales', methods=['GET'])
def get_sales_report():
    start_date = request.args.get('start_date', '2024-01-01')
    end_date = request.args.get('end_date', '2024-12-31')
    
    conn = get_db_connection()
    
    # Total sales
    total_sales = conn.execute('''
        SELECT SUM(total_amount) as total, COUNT(*) as count
        FROM bills 
        WHERE DATE(created_at) BETWEEN ? AND ?
    ''', (start_date, end_date)).fetchone()
    
    # Daily sales
    daily_sales = conn.execute('''
        SELECT DATE(created_at) as date, SUM(total_amount) as sales, COUNT(*) as transactions
        FROM bills 
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (start_date, end_date)).fetchall()
    
    # Top products
    top_products = conn.execute('''
        SELECT bi.product_name, SUM(bi.quantity) as quantity, SUM(bi.total_price) as sales
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        GROUP BY bi.product_name
        ORDER BY sales DESC
        LIMIT 10
    ''', (start_date, end_date)).fetchall()
    
    conn.close()
    
    return jsonify({
        "total_sales": dict(total_sales) if total_sales else {"total": 0, "count": 0},
        "daily_sales": [dict(row) for row in daily_sales],
        "top_products": [dict(row) for row in top_products]
    })

# Hotel Guests API
@app.route('/api/hotel/guests', methods=['GET'])
def get_hotel_guests():
    conn = get_db_connection()
    guests = conn.execute('SELECT * FROM hotel_guests ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in guests])

@app.route('/api/hotel/guests', methods=['POST'])
@require_auth
def add_hotel_guest():
    data = request.json
    guest_id = generate_id()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO hotel_guests (id, name, phone, email, address, id_proof, guest_count, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        guest_id, data['name'], data.get('phone'), data.get('email'),
        data.get('address'), data.get('id_proof'), data.get('guest_count', 1), 'booked'
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Guest added successfully", "id": guest_id}), 201

# Hotel Services API
@app.route('/api/hotel/services', methods=['GET'])
def get_hotel_services():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM hotel_services WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in services])

# ERP Modules API
@app.route('/api/modules', methods=['GET'])
def get_erp_modules():
    """Get all available ERP modules for the three lines menu"""
    modules = {
        "core_modules": [
            {
                "id": "dashboard",
                "name": "Dashboard",
                "icon": "🏠",
                "description": "Overview & Analytics",
                "route": "dashboard",
                "category": "core"
            },
            {
                "id": "sales",
                "name": "Sales",
                "icon": "💰",
                "description": "Sales Management",
                "route": "sales",
                "category": "core"
            },
            {
                "id": "invoices",
                "name": "Invoices",
                "icon": "📄",
                "description": "Invoice Management",
                "route": "invoices",
                "category": "core"
            },
            {
                "id": "billing",
                "name": "Billing",
                "icon": "🧾",
                "description": "Quick Billing",
                "route": "billing",
                "category": "core"
            }
        ],
        "inventory_modules": [
            {
                "id": "products",
                "name": "Products",
                "icon": "📦",
                "description": "Product Management",
                "route": "products",
                "category": "inventory"
            },
            {
                "id": "inventory",
                "name": "Inventory",
                "icon": "📊",
                "description": "Stock Management",
                "route": "inventory",
                "category": "inventory"
            },
            {
                "id": "suppliers",
                "name": "Suppliers",
                "icon": "🏭",
                "description": "Supplier Management",
                "route": "suppliers",
                "category": "inventory"
            },
            {
                "id": "purchase",
                "name": "Purchase",
                "icon": "🛒",
                "description": "Purchase Orders",
                "route": "purchase",
                "category": "inventory"
            }
        ],
        "customer_modules": [
            {
                "id": "customers",
                "name": "Customers",
                "icon": "👥",
                "description": "Customer Management",
                "route": "customers",
                "category": "customer"
            },
            {
                "id": "crm",
                "name": "CRM",
                "icon": "🤝",
                "description": "Customer Relations",
                "route": "crm",
                "category": "customer"
            },
            {
                "id": "loyalty",
                "name": "Loyalty",
                "icon": "⭐",
                "description": "Loyalty Programs",
                "route": "loyalty",
                "category": "customer"
            }
        ],
        "financial_modules": [
            {
                "id": "accounts",
                "name": "Accounts",
                "icon": "💳",
                "description": "Account Management",
                "route": "accounts",
                "category": "financial"
            },
            {
                "id": "payments",
                "name": "Payments",
                "icon": "💸",
                "description": "Payment Tracking",
                "route": "payments",
                "category": "financial"
            },
            {
                "id": "expenses",
                "name": "Expenses",
                "icon": "📉",
                "description": "Expense Management",
                "route": "expenses",
                "category": "financial"
            },
            {
                "id": "taxes",
                "name": "Taxes",
                "icon": "🏛️",
                "description": "Tax Management",
                "route": "taxes",
                "category": "financial"
            }
        ],
        "reports_modules": [
            {
                "id": "reports",
                "name": "Reports",
                "icon": "📈",
                "description": "Business Reports",
                "route": "reports",
                "category": "reports"
            },
            {
                "id": "analytics",
                "name": "Analytics",
                "icon": "📊",
                "description": "Business Analytics",
                "route": "analytics",
                "category": "reports"
            },
            {
                "id": "insights",
                "name": "Insights",
                "icon": "💡",
                "description": "Business Insights",
                "route": "insights",
                "category": "reports"
            }
        ],
        "settings_modules": [
            {
                "id": "settings",
                "name": "Settings",
                "icon": "⚙️",
                "description": "System Settings",
                "route": "settings",
                "category": "settings"
            },
            {
                "id": "users",
                "name": "Users",
                "icon": "👤",
                "description": "User Management",
                "route": "users",
                "category": "settings"
            },
            {
                "id": "backup",
                "name": "Backup",
                "icon": "💾",
                "description": "Data Backup",
                "route": "backup",
                "category": "settings"
            }
        ]
    }
    
    return jsonify(modules)

@app.route('/api/modules/quick-access', methods=['GET'])
def get_quick_access_modules():
    """Get frequently used modules for quick access"""
    quick_modules = [
        {
            "id": "billing",
            "name": "Quick Bill",
            "icon": "⚡",
            "description": "Create new bill",
            "route": "billing",
            "action": "create"
        },
        {
            "id": "sales",
            "name": "Today's Sales",
            "icon": "💰",
            "description": "View today's sales",
            "route": "sales",
            "action": "today"
        },
        {
            "id": "inventory",
            "name": "Low Stock",
            "icon": "⚠️",
            "description": "Check low stock items",
            "route": "inventory",
            "action": "low-stock"
        },
        {
            "id": "customers",
            "name": "Add Customer",
            "icon": "➕",
            "description": "Add new customer",
            "route": "customers",
            "action": "create"
        }
    ]
    
    return jsonify(quick_modules)

# Sales Module APIs
@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Get sales summary for today, week, month"""
    conn = get_db_connection()
    
    # Today's sales
    today_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE DATE(created_at) = DATE('now')
    ''').fetchone()
    
    # This week's sales
    week_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE DATE(created_at) >= DATE('now', 'weekday 0', '-6 days')
    ''').fetchone()
    
    # This month's sales
    month_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
    ''').fetchone()
    
    # Recent transactions
    recent_transactions = conn.execute('''
        SELECT b.bill_number, b.total_amount, b.created_at, c.name as customer_name
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        ORDER BY b.created_at DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        "today": dict(today_sales) if today_sales else {"total": 0, "count": 0},
        "week": dict(week_sales) if week_sales else {"total": 0, "count": 0},
        "month": dict(month_sales) if month_sales else {"total": 0, "count": 0},
        "recent_transactions": [dict(row) for row in recent_transactions]
    })

# Invoices Module APIs
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices with filtering options"""
    status = request.args.get('status', 'all')
    limit = int(request.args.get('limit', 50))
    
    conn = get_db_connection()
    
    query = '''
        SELECT b.*, c.name as customer_name, c.phone as customer_phone
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
    '''
    
    params = []
    if status != 'all':
        query += ' WHERE b.status = ?'
        params.append(status)
    
    query += ' ORDER BY b.created_at DESC LIMIT ?'
    params.append(limit)
    
    invoices = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in invoices])

@app.route('/api/invoices/<invoice_id>', methods=['GET'])
def get_invoice_details(invoice_id):
    """Get detailed invoice information"""
    conn = get_db_connection()
    
    # Get invoice
    invoice = conn.execute('''
        SELECT b.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ?
    ''', (invoice_id,)).fetchone()
    
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    
    # Get invoice items
    items = conn.execute('''
        SELECT * FROM bill_items WHERE bill_id = ?
    ''', (invoice_id,)).fetchall()
    
    # Get payments
    payments = conn.execute('''
        SELECT * FROM payments WHERE bill_id = ?
    ''', (invoice_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        "invoice": dict(invoice),
        "items": [dict(row) for row in items],
        "payments": [dict(row) for row in payments]
    })

# Hourly Sales Tracking APIs
@app.route('/api/sales/hourly', methods=['GET'])
def get_hourly_sales():
    """Get hourly sales data for today's sales chart"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    # Get hourly sales for the specified date
    hourly_sales = conn.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour
    ''', (date,)).fetchall()
    
    conn.close()
    
    # Create complete 24-hour data (fill missing hours with 0)
    hourly_data = {}
    for row in hourly_sales:
        hourly_data[int(row['hour'])] = {
            'hour': f"{int(row['hour']):02d}:00",
            'transactions': row['transactions'],
            'sales': float(row['sales']),
            'avg_order_value': float(row['avg_order_value'])
        }
    
    # Fill missing hours with zero data
    complete_data = []
    for hour in range(24):
        if hour in hourly_data:
            complete_data.append(hourly_data[hour])
        else:
            complete_data.append({
                'hour': f"{hour:02d}:00",
                'transactions': 0,
                'sales': 0.0,
                'avg_order_value': 0.0
            })
    
    return jsonify({
        'date': date,
        'hourly_data': complete_data,
        'total_sales': sum(item['sales'] for item in complete_data),
        'total_transactions': sum(item['transactions'] for item in complete_data),
        'peak_hour': max(complete_data, key=lambda x: x['sales'])['hour'] if any(item['sales'] > 0 for item in complete_data) else '00:00'
    })

@app.route('/api/sales/live-stats', methods=['GET'])
def get_live_sales_stats():
    """Get real-time sales statistics for dashboard updates"""
    conn = get_db_connection()
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    current_hour = datetime.now().strftime('%H')
    
    # Overall today stats
    today_stats = conn.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
    ''', (today,)).fetchone()
    
    # Current hour stats
    current_hour_stats = conn.execute('''
        SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
    ''', (today, current_hour)).fetchone()
    
    # Recent transactions (last 5)
    recent_transactions = conn.execute('''
        SELECT 
            b.bill_number,
            b.total_amount,
            b.created_at,
            c.name as customer_name,
            strftime('%H:%M', b.created_at) as time
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE DATE(b.created_at) = ?
        ORDER BY b.created_at DESC
        LIMIT 5
    ''', (today,)).fetchall()
    
    conn.close()
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "today": {
            "total_transactions": today_stats['total_transactions'],
            "total_sales": float(today_stats['total_sales']),
            "avg_order_value": float(today_stats['avg_order_value'])
        },
        "current_hour": {
            "hour": f"{current_hour}:00",
            "transactions": current_hour_stats['transactions'],
            "sales": float(current_hour_stats['sales'])
        },
        "recent_transactions": [dict(row) for row in recent_transactions]
    })

# Enhanced Bills API with hourly tracking
@app.route('/api/bills', methods=['POST'])
@require_auth
def create_bill():
    data = request.json
    bill_id = generate_id()
    bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
    
    conn = get_db_connection()
    
    try:
        # Create bill
        conn.execute('''
            INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bill_id, bill_number, data.get('customer_id'), data['business_type'],
            data['subtotal'], data['tax_amount'], data['total_amount']
        ))
        
        # Add bill items
        for item in data['items']:
            item_id = generate_id()
            conn.execute('''
                INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, bill_id, item['product_id'], item['product_name'],
                item['quantity'], item['unit_price'], item['total_price']
            ))
            
            # Update product stock
            conn.execute('''
                UPDATE products SET stock = stock - ? WHERE id = ?
            ''', (item['quantity'], item['product_id']))
        
        # Add payment record
        if 'payment_method' in data:
            payment_id = generate_id()
            conn.execute('''
                INSERT INTO payments (id, bill_id, method, amount)
                VALUES (?, ?, ?, ?)
            ''', (payment_id, bill_id, data['payment_method'], data['total_amount']))
        
        conn.commit()
        
        # Get updated hourly stats for real-time update
        current_hour = datetime.now().strftime('%H')
        today = datetime.now().strftime('%Y-%m-%d')
        
        hourly_stats = conn.execute('''
            SELECT 
                COUNT(*) as transactions,
                COALESCE(SUM(total_amount), 0) as sales
            FROM bills 
            WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
        ''', (today, current_hour)).fetchone()
        
        conn.close()
        
        return jsonify({
            "message": "Bill created successfully",
            "bill_id": bill_id,
            "bill_number": bill_number,
            "hourly_update": {
                "hour": f"{current_hour}:00",
                "transactions": hourly_stats['transactions'],
                "sales": float(hourly_stats['sales']),
                "avg_order_value": float(hourly_stats['sales'] / hourly_stats['transactions']) if hourly_stats['transactions'] > 0 else 0
            }
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Inventory Module APIs
@app.route('/api/inventory/summary', methods=['GET'])
def get_inventory_summary():
    """Get inventory summary with low stock alerts"""
    conn = get_db_connection()
    
    # Total products
    total_products = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1').fetchone()
    
    # Low stock items
    low_stock = conn.execute('''
        SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC
    ''').fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute('''
        SELECT COUNT(*) as count FROM products 
        WHERE is_active = 1 AND stock = 0
    ''').fetchone()
    
    # Total inventory value
    inventory_value = conn.execute('''
        SELECT COALESCE(SUM(stock * cost), 0) as value FROM products WHERE is_active = 1
    ''').fetchone()
    
    conn.close()
    
    return jsonify({
        "total_products": total_products['count'],
        "low_stock_count": len(low_stock),
        "out_of_stock_count": out_of_stock['count'],
        "inventory_value": float(inventory_value['value']),
        "low_stock_items": [dict(row) for row in low_stock]
    })

# Hourly Sales Tracking APIs
@app.route('/api/sales/hourly', methods=['GET'])
def get_hourly_sales():
    """Get hourly sales data for today's sales chart"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    # Get hourly sales for the specified date
    hourly_sales = conn.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour
    ''', (date,)).fetchall()
    
    conn.close()
    
    # Create complete 24-hour data (fill missing hours with 0)
    hourly_data = {}
    for row in hourly_sales:
        hourly_data[int(row['hour'])] = {
            'hour': f"{int(row['hour']):02d}:00",
            'transactions': row['transactions'],
            'sales': float(row['sales']),
            'avg_order_value': float(row['avg_order_value'])
        }
    
    # Fill missing hours with zero data
    complete_data = []
    for hour in range(24):
        if hour in hourly_data:
            complete_data.append(hourly_data[hour])
        else:
            complete_data.append({
                'hour': f"{hour:02d}:00",
                'transactions': 0,
                'sales': 0.0,
                'avg_order_value': 0.0
            })
    
    return jsonify({
        'date': date,
        'hourly_data': complete_data,
        'total_sales': sum(item['sales'] for item in complete_data),
        'total_transactions': sum(item['transactions'] for item in complete_data),
        'peak_hour': max(complete_data, key=lambda x: x['sales'])['hour'] if any(item['sales'] > 0 for item in complete_data) else '00:00'
    })

@app.route('/api/sales/hourly/update', methods=['POST'])
@require_auth
def update_hourly_sales():
    """Update hourly sales when a new bill is created - called automatically after bill creation"""
    try:
        data = request.json
        bill_id = data.get('bill_id')
        
        if not bill_id:
            return jsonify({"error": "Bill ID required"}), 400
        
        conn = get_db_connection()
        
        # Get the bill details to update hourly tracking
        bill = conn.execute('''
            SELECT id, total_amount, created_at 
            FROM bills 
            WHERE id = ?
        ''', (bill_id,)).fetchone()
        
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
        
        # Get current hour's data
        current_hour = datetime.now().strftime('%H')
        today = datetime.now().strftime('%Y-%m-%d')
        
        hourly_stats = conn.execute('''
            SELECT 
                COUNT(*) as transactions,
                COALESCE(SUM(total_amount), 0) as sales
            FROM bills 
            WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
        ''', (today, current_hour)).fetchone()
        
        conn.close()
        
        return jsonify({
            "message": "Hourly sales updated successfully",
            "current_hour": f"{current_hour}:00",
            "hour_stats": {
                "transactions": hourly_stats['transactions'],
                "sales": float(hourly_stats['sales']),
                "avg_order_value": float(hourly_stats['sales'] / hourly_stats['transactions']) if hourly_stats['transactions'] > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales/live-stats', methods=['GET'])
def get_live_sales_stats():
    """Get real-time sales statistics for dashboard updates"""
    conn = get_db_connection()
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    current_hour = datetime.now().strftime('%H')
    
    # Overall today stats
    today_stats = conn.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
    ''', (today,)).fetchone()
    
    # Current hour stats
    current_hour_stats = conn.execute('''
        SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
    ''', (today, current_hour)).fetchone()
    
    # Last hour stats for comparison
    last_hour = str(int(current_hour) - 1).zfill(2) if int(current_hour) > 0 else '23'
    last_hour_date = today if int(current_hour) > 0 else (datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    last_hour_stats = conn.execute('''
        SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
    ''', (last_hour_date, last_hour)).fetchone()
    
    # Recent transactions (last 5)
    recent_transactions = conn.execute('''
        SELECT 
            b.bill_number,
            b.total_amount,
            b.created_at,
            c.name as customer_name,
            strftime('%H:%M', b.created_at) as time
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE DATE(b.created_at) = ?
        ORDER BY b.created_at DESC
        LIMIT 5
    ''', (today,)).fetchall()
    
    conn.close()
    
    # Calculate trends
    current_hour_sales = float(current_hour_stats['sales'])
    last_hour_sales = float(last_hour_stats['sales'])
    hour_trend = ((current_hour_sales - last_hour_sales) / last_hour_sales * 100) if last_hour_sales > 0 else 0
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "today": {
            "total_transactions": today_stats['total_transactions'],
            "total_sales": float(today_stats['total_sales']),
            "avg_order_value": float(today_stats['avg_order_value'])
        },
        "current_hour": {
            "hour": f"{current_hour}:00",
            "transactions": current_hour_stats['transactions'],
            "sales": current_hour_sales,
            "trend_vs_last_hour": round(hour_trend, 1)
        },
        "recent_transactions": [dict(row) for row in recent_transactions]
    })

# Enhanced Bills API with hourly tracking
@app.route('/api/bills', methods=['POST'])
@require_auth
def create_bill():
    data = request.json
    bill_id = generate_id()
    bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
    
    conn = get_db_connection()
    
    try:
        # Create bill
        conn.execute('''
            INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bill_id, bill_number, data.get('customer_id'), data['business_type'],
            data['subtotal'], data['tax_amount'], data['total_amount']
        ))
        
        # Add bill items
        for item in data['items']:
            item_id = generate_id()
            conn.execute('''
                INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, bill_id, item['product_id'], item['product_name'],
                item['quantity'], item['unit_price'], item['total_price']
            ))
            
            # Update product stock
            conn.execute('''
                UPDATE products SET stock = stock - ? WHERE id = ?
            ''', (item['quantity'], item['product_id']))
        
        # Add payment record
        if 'payment_method' in data:
            payment_id = generate_id()
            conn.execute('''
                INSERT INTO payments (id, bill_id, method, amount)
                VALUES (?, ?, ?, ?)
            ''', (payment_id, bill_id, data['payment_method'], data['total_amount']))
        
        conn.commit()
        
        # Get updated hourly stats for real-time update
        current_hour = datetime.now().strftime('%H')
        today = datetime.now().strftime('%Y-%m-%d')
        
        hourly_stats = conn.execute('''
            SELECT 
                COUNT(*) as transactions,
                COALESCE(SUM(total_amount), 0) as sales
            FROM bills 
            WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?
        ''', (today, current_hour)).fetchone()
        
        conn.close()
        
        return jsonify({
            "message": "Bill created successfully",
            "bill_id": bill_id,
            "bill_number": bill_number,
            "hourly_update": {
                "hour": f"{current_hour}:00",
                "transactions": hourly_stats['transactions'],
                "sales": float(hourly_stats['sales']),
                "avg_order_value": float(hourly_stats['sales'] / hourly_stats['transactions']) if hourly_stats['transactions'] > 0 else 0
            }
        }), 201
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Inventory Module APIs
@app.route('/api/inventory/summary', methods=['GET'])
def get_inventory_summary():
    """Get inventory summary with low stock alerts"""
    conn = get_db_connection()
    
    # Total products
    total_products = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1').fetchone()
    
    # Low stock items
    low_stock = conn.execute('''
        SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC
    ''').fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute('''
        SELECT COUNT(*) as count FROM products 
        WHERE is_active = 1 AND stock = 0
    ''').fetchone()
    
    # Total inventory value
    inventory_value = conn.execute('''
        SELECT COALESCE(SUM(stock * cost), 0) as value FROM products WHERE is_active = 1
    ''').fetchone()
    
    conn.close()
    
    return jsonify({
        "total_products": total_products['count'],
        "low_stock_count": len(low_stock),
        "out_of_stock_count": out_of_stock['count'],
        "inventory_value": float(inventory_value['value']),
        "low_stock_items": [dict(row) for row in low_stock]
    })

@app.route('/api/inventory/summary', methods=['GET'])
def get_inventory_summary():
    """Get inventory summary including low stock alerts"""
    conn = get_db_connection()
    
    # Total products
    total_products = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_active = 1').fetchone()
    
    # Low stock items
    low_stock = conn.execute('''
        SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC
    ''').fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute('''
        SELECT * FROM products 
        WHERE is_active = 1 AND stock = 0
    ''').fetchall()
    
    # Total inventory value
    inventory_value = conn.execute('''
        SELECT SUM(stock * cost) as total_cost, SUM(stock * price) as total_value
        FROM products WHERE is_active = 1
    ''').fetchone()
    
    conn.close()
    
    return jsonify({
        "total_products": dict(total_products)["count"] if total_products else 0,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "low_stock_items": [dict(row) for row in low_stock],
        "out_of_stock_items": [dict(row) for row in out_of_stock],
        "inventory_value": dict(inventory_value) if inventory_value else {"total_cost": 0, "total_value": 0}
    })

# Dashboard Analytics API
@app.route('/api/analytics/sales')
@require_auth
def get_sales_analytics():
    business_type = request.args.get('type', 'retail')
    conn = get_db_connection()
    
    # Total sales
    total_sales = conn.execute('''
        SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills WHERE business_type = ?
    ''', (business_type,)).fetchone()
    
    # Daily sales for last 7 days
    daily_sales = conn.execute('''
        SELECT DATE(created_at) as date, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
        FROM bills 
        WHERE business_type = ? AND DATE(created_at) >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
    ''', (business_type,)).fetchall()
    
    # Top products
    top_products = conn.execute('''
        SELECT p.name, SUM(bi.quantity) as quantity, SUM(bi.total_price) as revenue
        FROM bill_items bi
        JOIN products p ON bi.product_id = p.id
        JOIN bills b ON bi.bill_id = b.id
        WHERE b.business_type = ?
        GROUP BY p.id, p.name
        ORDER BY revenue DESC
        LIMIT 5
    ''', (business_type,)).fetchall()
    
    conn.close()
    
    return jsonify({
        "total_sales": dict(total_sales) if total_sales else {"total": 0, "count": 0},
        "daily_sales": [dict(row) for row in daily_sales],
        "top_products": [dict(row) for row in top_products]
    })

if __name__ == '__main__':
    init_db()
    print("🚀 BizPulse ERP System Starting...")
    print("📊 Database initialized with sample data")
    print("🌐 Server running on http://localhost:5000")
    print("📱 Mobile PWA available at: http://localhost:5000/mobile")
    print("💡 For mobile access, use your computer's IP address")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)