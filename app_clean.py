from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import uuid
import hashlib
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection
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
            business_type TEXT DEFAULT 'kirana',
            gst_number TEXT,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

# Kirana module routes
@app.route('/kirana/products')
def kirana_products_page():
    return render_template('kirana_products.html')

@app.route('/kirana/customers')
def kirana_customers():
    return render_template('kirana_customers.html')

@app.route('/kirana/dashboard')
def kirana_dashboard():
    return render_template('kirana_dashboard.html')

# Hotel module routes
@app.route('/hotel/dashboard')
def hotel_dashboard():
    return render_template('hotel_dashboard.html')

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
            data.get('business_name', ''), data.get('business_type', 'kirana')
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

# Bills API
@app.route('/api/bills', methods=['POST'])
@require_auth
def create_bill():
    data = request.json
    bill_id = generate_id()
    bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
    
    conn = get_db_connection()
    
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
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "Bill created successfully",
        "bill_id": bill_id,
        "bill_number": bill_number
    }), 201

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

# Dashboard Analytics API
@app.route('/api/analytics/sales')
@require_auth
def get_sales_analytics():
    business_type = request.args.get('type', 'kirana')
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
    print("🚀 Starting Billing Software API...")
    print("📊 Database initialized with sample data")
    print("🌐 Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)