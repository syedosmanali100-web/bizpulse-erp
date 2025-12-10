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
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
app.config['SECRET_KEY'] = 'your-secret-key-here'

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
    
    # Add sample data if empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('prod-1', 'P001', 'Rice (1kg)', 'Groceries', 80.0, 70.0, 100, 10, 'kg', 'retail'),
            ('prod-2', 'P002', 'Wheat Flour (1kg)', 'Groceries', 45.0, 40.0, 50, 5, 'kg', 'retail'),
            ('prod-3', 'P003', 'Sugar (1kg)', 'Groceries', 55.0, 50.0, 30, 5, 'kg', 'retail'),
            ('prod-4', 'P004', 'Tea Powder (250g)', 'Beverages', 120.0, 100.0, 25, 3, 'packet', 'retail'),
            ('prod-5', 'P005', 'Cooking Oil (1L)', 'Groceries', 150.0, 140.0, 20, 2, 'liter', 'retail')
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
            ('cust-3', 'Amit Singh', '+91 9876543212', 'amit@email.com', '789 Garden Road, City', 2000.0)
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

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.current_user_id = "demo-user-id"
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile-pwa')
def mobile_pwa():
    response = send_from_directory('.', 'mobile_web_app.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db_connection()
    customers = conn.execute('SELECT * FROM customers WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in customers])

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
    
    conn.close()
    
    return jsonify({
        "today": dict(today_sales) if today_sales else {"total": 0, "count": 0},
        "week": dict(week_sales) if week_sales else {"total": 0, "count": 0},
        "month": dict(month_sales) if month_sales else {"total": 0, "count": 0}
    })

if __name__ == '__main__':
    init_db()
    print("🚀 BizPulse ERP System Starting...")
    print("📊 Database initialized with sample data")
    print("🌐 Server running on http://localhost:5000")
    print("📱 Mobile PWA available at: http://localhost:5000/mobile-pwa")
    print("💡 For mobile access, use your computer's IP address")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)