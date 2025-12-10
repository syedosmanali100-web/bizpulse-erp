from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import hashlib
from functools import wraps

app = Flask(__name__)
# Enable CORS for all domains and methods (for mobile app)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
app.config['SECRET_KEY'] = 'cms-secret-key-change-in-production-2024'  # Change this in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session expires after 24 hours
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates for development

# --- Internationalization (i18n) support (minimal) ---
TRANSLATIONS = {}
def load_translations():
    base = os.path.join(os.path.dirname(__file__), 'translations')
    try:
        for fname in os.listdir(base):
            if fname.endswith('.json'):
                lang = fname.split('.')[0]
                with open(os.path.join(base, fname), 'r', encoding='utf-8') as f:
                    TRANSLATIONS[lang] = json.load(f)
    except Exception:
        # If translations folder missing or invalid, keep TRANSLATIONS empty
        pass

load_translations()

from flask import g, make_response

def get_translation(key, lang=None):
    lang = lang or getattr(g, 'lang', None) or request.cookies.get('app_lang') or 'en'
    data = TRANSLATIONS.get(lang, {})
    return data.get(key, key)

@app.context_processor
def inject_translator():
    # provide translator function `t(key)` and the full translations map for current lang as `I18N`
    def _t(k):
        return get_translation(k)
    cur_lang = getattr(g, 'lang', None) or request.cookies.get('app_lang') or 'en'
    return dict(t=_t, I18N=TRANSLATIONS.get(cur_lang, {}))

@app.before_request
def detect_language():
    # language preference comes from cookie `app_lang` (set by frontend)
    lang = request.cookies.get('app_lang')
    if not lang:
        # try Accept-Language header fallback (very small parsing)
        al = request.headers.get('Accept-Language', '')
        if al:
            lang = al.split(',')[0].split('-')[0]
    g.lang = lang or 'en'

@app.route('/api/set_language', methods=['POST'])
def api_set_language():
    try:
        data = request.get_json(force=True)
        lang = data.get('lang') if isinstance(data, dict) else None
        if not lang:
            return jsonify({'status':'error','message':'missing lang'}), 400
        resp = make_response(jsonify({'status':'ok'}))
        # set cookie for 1 year
        resp.set_cookie('app_lang', lang, max_age=60*60*24*365, httponly=False)
        return resp
    except Exception as e:
        return jsonify({'status':'error','message': str(e)}), 500

# --- end i18n support ---

# File Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    
    # Sales table - for tracking all sales transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            bill_id TEXT,
            bill_number TEXT,
            customer_id TEXT,
            customer_name TEXT,
            product_id TEXT,
            product_name TEXT,
            category TEXT,
            quantity INTEGER,
            unit_price REAL,
            total_price REAL,
            tax_amount REAL,
            discount_amount REAL DEFAULT 0,
            payment_method TEXT,
            sale_date DATE,
            sale_time TIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id) REFERENCES bills (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
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
    
    # Clients table - for client management system
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            contact_email TEXT UNIQUE NOT NULL,
            contact_name TEXT,
            phone_number TEXT,
            whatsapp_number TEXT,
            business_address TEXT,
            business_type TEXT DEFAULT 'retail',
            gst_number TEXT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # CMS Tables for Content Management
    
    # Site Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT DEFAULT 'BizPulse ERP',
            logo_url TEXT,
            favicon_url TEXT,
            primary_color TEXT DEFAULT '#732C3F',
            secondary_color TEXT DEFAULT '#F7E8EC',
            contact_email TEXT,
            contact_phone TEXT,
            address TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Hero Section table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_hero_section (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT 'Welcome to BizPulse',
            subtitle TEXT DEFAULT 'Complete Business Management Solution',
            button_text TEXT DEFAULT 'Get Started',
            button_link TEXT DEFAULT '/register',
            background_image_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Features table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_features (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            icon_image_url TEXT,
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pricing Plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_pricing_plans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            price_per_month REAL NOT NULL,
            description TEXT,
            features TEXT,
            is_popular BOOLEAN DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Testimonials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_testimonials (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT,
            company TEXT,
            message TEXT NOT NULL,
            avatar_image_url TEXT,
            rating INTEGER DEFAULT 5,
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # FAQs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_faqs (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Gallery Images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_gallery (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            image_url TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # CMS Admin Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_admin_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Website Content table - stores edited website HTML
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cms_website_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_name TEXT DEFAULT 'index',
            content_html TEXT NOT NULL,
            edited_by TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Companies table - for multi-tenant support and WhatsApp reports
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            phone_number TEXT,
            whatsapp_number TEXT,
            email TEXT,
            address TEXT,
            send_daily_report BOOLEAN DEFAULT 1,
            report_time TIME DEFAULT '23:55:00',
            timezone TEXT DEFAULT 'Asia/Kolkata',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Update invoices table to include company_id and cost tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            company_id TEXT DEFAULT 'default_company',
            invoice_number TEXT UNIQUE,
            customer_id TEXT,
            invoice_date DATE DEFAULT CURRENT_DATE,
            due_date DATE,
            subtotal REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            total_cost REAL DEFAULT 0,
            profit_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # WhatsApp Reports Log table - track sent reports
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whatsapp_reports_log (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            report_date DATE NOT NULL,
            report_type TEXT DEFAULT 'daily_sales',
            whatsapp_number TEXT,
            pdf_filename TEXT,
            media_id TEXT,
            message_id TEXT,
            status TEXT DEFAULT 'pending',
            total_sales REAL DEFAULT 0,
            total_profit REAL DEFAULT 0,
            total_invoices INTEGER DEFAULT 0,
            error_message TEXT,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    

    
    # Initialize default CMS data
    cursor.execute('SELECT COUNT(*) FROM cms_site_settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO cms_site_settings (site_name, primary_color, secondary_color)
            VALUES ('BizPulse ERP', '#732C3F', '#F7E8EC')
        ''')
    
    cursor.execute('SELECT COUNT(*) FROM cms_hero_section')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO cms_hero_section (title, subtitle, button_text, button_link)
            VALUES ('Welcome to BizPulse', 'Complete Business Management Solution', 'Get Started', '/register')
        ''')
    
    # Initialize default CMS admin user
    cursor.execute('SELECT COUNT(*) FROM cms_admin_users')
    if cursor.fetchone()[0] == 0:
        # Default credentials: username=admin, password=admin123
        default_password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO cms_admin_users (id, username, password_hash, email, full_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (generate_id(), 'admin', default_password_hash, 'admin@bizpulse.com', 'CMS Administrator'))
    
    # Initialize default company
    cursor.execute('SELECT COUNT(*) FROM companies')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO companies (id, business_name, phone_number, whatsapp_number, email, address, send_daily_report, report_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('default_company', 'BizPulse Demo Store', '7093635305', '7093635305', 'bizpulse.erp@gmail.com', 'Hyderabad, Telangana, India', 1, '23:55:00'))
    
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

# CMS Authentication decorator
def require_cms_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cms_admin_id' not in session:
            return redirect(url_for('cms_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Main website - loads saved content if available, or returns default template"""
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

@app.route('/gallery')
def gallery_page():
    """Public Gallery Page"""
    return render_template('gallery.html')

@app.route('/website-builder')
@require_cms_auth
def website_builder():
    """Professional Website Builder - Photoshop/Canva Style"""
    return render_template('website_builder_pro.html')

@app.route('/mobile-login-test')
def mobile_login_test():
    return render_template('mobile_login_test.html')

@app.route('/mobile-simple-old')
def mobile_simple_old():
    return render_template('mobile_simple_test.html')

@app.route('/mobile-instant')
def mobile_instant():
    return render_template('mobile_instant.html')

@app.route('/mobile-debug')
def mobile_debug():
    return render_template('mobile_debug.html')

@app.route('/test-hamburger')
def test_hamburger():
    return render_template('test_hamburger.html')

@app.route('/diagnostic-full')
def diagnostic_full():
    return render_template('mobile_diagnostic_full.html')

@app.route('/mobile-simple')
def mobile_simple_new():
    return render_template('mobile_simple_working.html')

@app.route('/mobile-diagnostic')
def mobile_diagnostic():
    return render_template('mobile_diagnostic_simple.html')

@app.route('/mobile-test')
def mobile_test_connection():
    return render_template('mobile_test_connection.html')

@app.route('/mobile-fresh')
def mobile_fresh_version():
    return render_template('mobile_fresh.html')

@app.route('/mobile-test-page')
def mobile_test_page():
    return render_template('mobile_test_simple.html')

@app.route('/camera-test')
def camera_test():
    return render_template('camera_test.html')

# PWA Support Routes
@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

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
        <h1>BizPulse</h1>
        <h2>You're offline</h2>
        <p>Please check your internet connection and try again.</p>
        <button class="btn" onclick="window.location.reload()">Try Again</button>
    </div>
</body>
</html>'''

@app.route('/mobile')
def mobile_app():
    return render_template('mobile_simple_working.html')

@app.route('/mobile-v1')
def mobile_app_v1():
    return render_template('mobile_erp_working.html')

@app.route('/mobile-old')
def mobile_app_old():
    return render_template('mobile_erp_working.html')

@app.route('/mobile-working')
def mobile_working():
    return render_template('mobile_erp_working.html')

@app.route('/mobile-fixed')
def mobile_app_fixed():
    return render_template('mobile_erp_working.html')

@app.route('/mobile-pwa')
def mobile_pwa():
    from flask import make_response
    response = make_response(render_template('mobile_erp_working.html'))
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
    return render_template('retail_sales_professional.html')

@app.route('/retail/sales-old')
def retail_sales_old():
    return render_template('retail_sales_enhanced.html')

@app.route('/retail/invoices')
def retail_invoices():
    return render_template('invoices_professional.html')

@app.route('/retail/invoice/<invoice_id>')
def retail_invoice_detail(invoice_id):
    return render_template('retail_invoice_detail.html', invoice_id=invoice_id)

@app.route('/retail/inventory')
def retail_inventory():
    return render_template('inventory_professional.html')

@app.route('/retail/settings')
def retail_settings():
    return render_template('settings_professional.html')

@app.route('/invoice-demo')
def invoice_demo():
    return render_template('invoice_demo.html')

@app.route('/test-navigation')
def test_navigation():
    return render_template('test_navigation.html')

@app.route('/sales-management')
def sales_management():
    return render_template('sales_management_wine.html')

@app.route('/sales-management-old')
def sales_management_old():
    return render_template('sales_management_new.html')

@app.route('/inventory/low-stock')
def low_stock_management():
    return render_template('low_stock_management.html')

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
    if email == "bizpulse.erp@gmail.com" and password == "demo123":
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

@app.route('/api/sales/refresh', methods=['POST'])
def refresh_sales_data():
    """Refresh sales data based on date range"""
    data = request.json
    range_type = data.get('range', 'today')
    from_date = data.get('from_date')
    to_date = data.get('to_date')
    
    conn = get_db_connection()
    
    try:
        # Build query based on range type
        if range_type == 'today':
            date_filter = "DATE(created_at) = DATE('now')"
            params = []
        elif range_type == 'week':
            date_filter = "DATE(created_at) >= DATE('now', 'weekday 0', '-6 days')"
            params = []
        elif range_type == 'month':
            date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
            params = []
        elif range_type == 'custom' and from_date and to_date:
            date_filter = "DATE(created_at) BETWEEN ? AND ?"
            params = [from_date, to_date]
        else:
            date_filter = "DATE(created_at) = DATE('now')"
            params = []
        
        # Get sales summary
        sales_query = f'''
            SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM bills WHERE {date_filter}
        '''
        sales_data = conn.execute(sales_query, params).fetchone()
        
        # Get top products for the period
        products_query = f'''
            SELECT bi.product_name, SUM(bi.quantity) as quantity, 
                   SUM(bi.total_price) as sales, COUNT(DISTINCT b.id) as orders
            FROM bill_items bi
            JOIN bills b ON bi.bill_id = b.id
            WHERE {date_filter}
            GROUP BY bi.product_name
            ORDER BY sales DESC
            LIMIT 5
        '''
        top_products = conn.execute(products_query, params).fetchall()
        
        # Get recent transactions for the period
        transactions_query = f'''
            SELECT b.bill_number, b.total_amount, b.created_at, 
                   c.name as customer_name, b.status
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE {date_filter}
            ORDER BY b.created_at DESC
            LIMIT 10
        '''
        recent_transactions = conn.execute(transactions_query, params).fetchall()
        
        # Get payment methods breakdown
        payments_query = f'''
            SELECT p.method, COUNT(*) as count, SUM(p.amount) as total
            FROM payments p
            JOIN bills b ON p.bill_id = b.id
            WHERE {date_filter}
            GROUP BY p.method
            ORDER BY total DESC
        '''
        payment_methods = conn.execute(payments_query, params).fetchall()
        
        # Get hourly sales data for charts (if today or specific date)
        if range_type == 'today' or (range_type == 'custom' and from_date == to_date):
            chart_date = from_date if range_type == 'custom' else datetime.now().strftime('%Y-%m-%d')
            hourly_query = '''
                SELECT strftime('%H', created_at) as hour,
                       COUNT(*) as transactions,
                       COALESCE(SUM(total_amount), 0) as sales
                FROM bills 
                WHERE DATE(created_at) = ?
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
            '''
            hourly_data = conn.execute(hourly_query, [chart_date]).fetchall()
        else:
            hourly_data = []
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Sales data refreshed successfully",
            "data": {
                "summary": dict(sales_data) if sales_data else {"total": 0, "count": 0, "avg_order_value": 0},
                "top_products": [dict(row) for row in top_products],
                "recent_transactions": [dict(row) for row in recent_transactions],
                "payment_methods": [dict(row) for row in payment_methods],
                "hourly_data": [dict(row) for row in hourly_data],
                "range": range_type,
                "from_date": from_date,
                "to_date": to_date,
                "refreshed_at": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"Error refreshing sales data: {str(e)}"
        }), 500

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
    """Get hourly sales data for today's sales chart with category breakdown"""
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
    
    # Get category-wise sales for the date
    category_sales = conn.execute('''
        SELECT 
            p.category,
            COUNT(DISTINCT b.id) as transactions,
            COALESCE(SUM(bi.total_price), 0) as sales,
            COALESCE(SUM(bi.quantity), 0) as quantity_sold
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE DATE(b.created_at) = ?
        GROUP BY p.category
        ORDER BY sales DESC
    ''', (date,)).fetchall()
    
    # Get hourly category breakdown
    hourly_category_sales = conn.execute('''
        SELECT 
            strftime('%H', b.created_at) as hour,
            p.category,
            COALESCE(SUM(bi.total_price), 0) as sales,
            COALESCE(SUM(bi.quantity), 0) as quantity
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE DATE(b.created_at) = ?
        GROUP BY strftime('%H', b.created_at), p.category
        ORDER BY hour, sales DESC
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
    
    # Process hourly category data
    hourly_categories = {}
    for row in hourly_category_sales:
        hour = int(row['hour'])
        if hour not in hourly_categories:
            hourly_categories[hour] = {}
        hourly_categories[hour][row['category']] = {
            'sales': float(row['sales']),
            'quantity': int(row['quantity'])
        }
    
    return jsonify({
        'date': date,
        'hourly_data': complete_data,
        'category_sales': [dict(row) for row in category_sales],
        'hourly_categories': hourly_categories,
        'total_sales': sum(item['sales'] for item in complete_data),
        'total_transactions': sum(item['transactions'] for item in complete_data),
        'peak_hour': max(complete_data, key=lambda x: x['sales'])['hour'] if any(item['sales'] > 0 for item in complete_data) else '00:00',
        'top_category': category_sales[0]['category'] if category_sales else 'No sales'
    })

@app.route('/api/sales/categories', methods=['GET'])
def get_category_sales():
    """Get category-wise sales breakdown for the sales module"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    period = request.args.get('period', 'today')  # today, week, month
    
    conn = get_db_connection()
    
    # Determine date range based on period
    if period == 'week':
        date_condition = "DATE(b.created_at) >= DATE('now', 'weekday 0', '-6 days')"
    elif period == 'month':
        date_condition = "strftime('%Y-%m', b.created_at) = strftime('%Y-%m', 'now')"
    else:  # today
        date_condition = f"DATE(b.created_at) = '{date}'"
    
    # Get category sales with detailed breakdown
    category_details = conn.execute(f'''
        SELECT 
            p.category,
            COUNT(DISTINCT b.id) as transactions,
            COALESCE(SUM(bi.total_price), 0) as total_sales,
            COALESCE(SUM(bi.quantity), 0) as total_quantity,
            COALESCE(AVG(bi.total_price), 0) as avg_sale_value,
            COUNT(DISTINCT bi.product_id) as unique_products,
            MAX(bi.total_price) as highest_sale,
            MIN(bi.total_price) as lowest_sale
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE {date_condition}
        GROUP BY p.category
        ORDER BY total_sales DESC
    ''').fetchall()
    
    # Get top selling products per category
    top_products_per_category = conn.execute(f'''
        SELECT 
            p.category,
            bi.product_name,
            COALESCE(SUM(bi.quantity), 0) as quantity_sold,
            COALESCE(SUM(bi.total_price), 0) as sales,
            ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY SUM(bi.total_price) DESC) as rank
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE {date_condition}
        GROUP BY p.category, bi.product_name
        HAVING rank <= 3
        ORDER BY p.category, sales DESC
    ''').fetchall()
    
    # Calculate total sales for percentage calculation
    total_sales = sum(float(row['total_sales']) for row in category_details)
    
    # Process category data with percentages
    categories_with_percentage = []
    for row in category_details:
        category_data = dict(row)
        category_data['percentage'] = round((float(row['total_sales']) / total_sales * 100), 2) if total_sales > 0 else 0
        category_data['total_sales'] = float(row['total_sales'])
        category_data['avg_sale_value'] = float(row['avg_sale_value'])
        category_data['highest_sale'] = float(row['highest_sale'])
        category_data['lowest_sale'] = float(row['lowest_sale'])
        categories_with_percentage.append(category_data)
    
    # Group top products by category
    top_products_grouped = {}
    for row in top_products_per_category:
        category = row['category']
        if category not in top_products_grouped:
            top_products_grouped[category] = []
        top_products_grouped[category].append({
            'product_name': row['product_name'],
            'quantity_sold': row['quantity_sold'],
            'sales': float(row['sales'])
        })
    
    conn.close()
    
    return jsonify({
        'period': period,
        'date': date,
        'categories': categories_with_percentage,
        'top_products_per_category': top_products_grouped,
        'total_sales': total_sales,
        'total_categories': len(category_details),
        'summary': {
            'best_performing_category': categories_with_percentage[0]['category'] if categories_with_percentage else 'No sales',
            'total_transactions': sum(row['transactions'] for row in categories_with_percentage),
            'avg_category_sales': round(total_sales / len(categories_with_percentage), 2) if categories_with_percentage else 0
        }
    })

@app.route('/api/inventory/low-stock', methods=['GET'])
def get_low_stock_items():
    """Get detailed low stock items with management options"""
    conn = get_db_connection()
    
    # Get low stock items with detailed information
    low_stock_items = conn.execute('''
        SELECT 
            p.*,
            (p.min_stock - p.stock) as shortage_quantity,
            (p.min_stock - p.stock) * p.cost as reorder_cost,
            CASE 
                WHEN p.stock = 0 THEN 'out_of_stock'
                WHEN p.stock <= p.min_stock * 0.5 THEN 'critical'
                WHEN p.stock <= p.min_stock THEN 'low'
                ELSE 'normal'
            END as urgency_level
        FROM products p
        WHERE p.is_active = 1 AND p.stock <= p.min_stock
        ORDER BY 
            CASE 
                WHEN p.stock = 0 THEN 1
                WHEN p.stock <= p.min_stock * 0.5 THEN 2
                ELSE 3
            END,
            p.stock ASC
    ''').fetchall()
    
    # Get category-wise low stock summary
    category_summary = conn.execute('''
        SELECT 
            p.category,
            COUNT(*) as low_stock_count,
            SUM(p.min_stock - p.stock) as total_shortage,
            SUM((p.min_stock - p.stock) * p.cost) as total_reorder_cost,
            AVG(p.stock * 100.0 / p.min_stock) as avg_stock_percentage
        FROM products p
        WHERE p.is_active = 1 AND p.stock <= p.min_stock
        GROUP BY p.category
        ORDER BY low_stock_count DESC
    ''').fetchall()
    
    # Get recent stock movements (if you have a stock_movements table)
    # For now, we'll simulate this with recent bill items
    recent_movements = conn.execute('''
        SELECT 
            bi.product_name,
            bi.quantity,
            b.created_at,
            'sale' as movement_type
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE p.stock <= p.min_stock
        ORDER BY b.created_at DESC
        LIMIT 20
    ''').fetchall()
    
    conn.close()
    
    # Calculate summary statistics
    total_low_stock = len(low_stock_items)
    critical_items = len([item for item in low_stock_items if item['urgency_level'] == 'critical'])
    out_of_stock = len([item for item in low_stock_items if item['urgency_level'] == 'out_of_stock'])
    total_reorder_cost = sum(float(item['reorder_cost']) for item in low_stock_items)
    
    return jsonify({
        'low_stock_items': [dict(row) for row in low_stock_items],
        'category_summary': [dict(row) for row in category_summary],
        'recent_movements': [dict(row) for row in recent_movements],
        'summary': {
            'total_low_stock': total_low_stock,
            'critical_items': critical_items,
            'out_of_stock': out_of_stock,
            'total_reorder_cost': round(total_reorder_cost, 2),
            'categories_affected': len(category_summary)
        }
    })

@app.route('/api/inventory/restock', methods=['POST'])
@require_auth
def restock_product():
    """Restock a product - update stock quantity"""
    data = request.json
    product_id = data.get('product_id')
    quantity_to_add = data.get('quantity', 0)
    cost_per_unit = data.get('cost_per_unit')
    notes = data.get('notes', '')
    
    conn = get_db_connection()
    
    try:
        # Get current product info
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Update stock
        new_stock = product['stock'] + quantity_to_add
        
        # Update cost if provided
        if cost_per_unit:
            conn.execute('''
                UPDATE products 
                SET stock = ?, cost = ?
                WHERE id = ?
            ''', (new_stock, cost_per_unit, product_id))
        else:
            conn.execute('''
                UPDATE products 
                SET stock = ?
                WHERE id = ?
            ''', (new_stock, product_id))
        
        conn.commit()
        
        return jsonify({
            'message': 'Product restocked successfully',
            'product_id': product_id,
            'old_stock': product['stock'],
            'new_stock': new_stock,
            'quantity_added': quantity_to_add
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/inventory/update-min-stock', methods=['POST'])
@require_auth
def update_min_stock():
    """Update minimum stock level for a product"""
    data = request.json
    product_id = data.get('product_id')
    new_min_stock = data.get('min_stock')
    
    conn = get_db_connection()
    
    try:
        conn.execute('''
            UPDATE products 
            SET min_stock = ?
            WHERE id = ?
        ''', (new_min_stock, product_id))
        
        conn.commit()
        
        return jsonify({
            'message': 'Minimum stock level updated successfully',
            'product_id': product_id,
            'new_min_stock': new_min_stock
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

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
    try:
        data = request.json
        print("📥 Received bill data:", data)
        
        bill_id = generate_id()
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"📝 Generated bill: {bill_number}")
        
        conn = get_db_connection()
    except Exception as e:
        print(f"❌ Error in bill creation setup: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    try:
        # Create bill
        conn.execute('''
            INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bill_id, bill_number, data.get('customer_id'), data['business_type'],
            data['subtotal'], data['tax_amount'], data['total_amount']
        ))
        
        # Get customer name if customer_id exists
        customer_name = None
        if data.get('customer_id'):
            customer = conn.execute('''
                SELECT name FROM customers WHERE id = ?
            ''', (data.get('customer_id'),)).fetchone()
            customer_name = customer['name'] if customer else None
        
        # Add bill items and create sales entries
        for item in data['items']:
            item_id = generate_id()
            conn.execute('''
                INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, bill_id, item['product_id'], item['product_name'],
                item['quantity'], item['unit_price'], item['total_price']
            ))
            
            # Update product stock (AUTOMATIC STOCK REDUCTION)
            conn.execute('''
                UPDATE products SET stock = stock - ? WHERE id = ?
            ''', (item['quantity'], item['product_id']))
            
            # Get product details for sales entry
            product = conn.execute('''
                SELECT category FROM products WHERE id = ?
            ''', (item['product_id'],)).fetchone()
            
            # Create sales entry for each item (AUTOMATIC SALES ENTRY)
            sale_id = generate_id()
            sale_date = datetime.now().strftime('%Y-%m-%d')
            sale_time = datetime.now().strftime('%H:%M:%S')
            
            # Calculate item tax amount (proportional to item total)
            item_tax = (item['total_price'] / data['subtotal']) * data['tax_amount'] if data['subtotal'] > 0 else 0
            item_discount = (item['total_price'] / data['subtotal']) * data.get('discount_amount', 0) if data['subtotal'] > 0 else 0
            
            conn.execute('''
                INSERT INTO sales (
                    id, bill_id, bill_number, customer_id, customer_name,
                    product_id, product_name, category, quantity, unit_price,
                    total_price, tax_amount, discount_amount, payment_method,
                    sale_date, sale_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                item['product_id'], item['product_name'], product['category'] if product else 'General',
                item['quantity'], item['unit_price'], item['total_price'],
                item_tax, item_discount, data.get('payment_method', 'cash'),
                sale_date, sale_time
            ))
        
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
        
        print(f">> Bill created successfully: {bill_number}")
        print(f">> Sales entries created: {len(data['items'])}")
        
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
        print(f">> Error creating bill: {str(e)}")
        import traceback
        print(f">> Traceback: {traceback.format_exc()}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500

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

# Hourly Sales Tracking APIs - DUPLICATE REMOVED
# @app.route('/api/sales/hourly', methods=['GET'])
def get_hourly_sales_duplicate():
    """DUPLICATE FUNCTION - DISABLED"""
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

# @app.route('/api/sales/live-stats', methods=['GET'])  # DUPLICATE REMOVED
def get_live_sales_stats_duplicate():
    """DUPLICATE FUNCTION - DISABLED"""
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

# Enhanced Bills API with hourly tracking - DUPLICATE REMOVED
# @app.route('/api/bills', methods=['POST'])
# @require_auth
def create_bill_duplicate():
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
# @app.route('/api/inventory/summary', methods=['GET'])
# def get_inventory_summary():
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

# @app.route('/api/inventory/summary', methods=['GET'])
# def get_inventory_summary():
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

# Sales Module - Detailed Sales Data APIs
@app.route('/api/sales', methods=['GET'])
def get_sales():
    """Get all sales entries - simple endpoint for sales management page"""
    conn = get_db_connection()
    
    sales = conn.execute('''
        SELECT 
            s.*,
            COALESCE(s.total_price, s.unit_price * s.quantity) as total_amount
        FROM sales s
        ORDER BY s.created_at DESC
        LIMIT 500
    ''').fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in sales])

@app.route('/api/sales/all', methods=['GET'])
def get_all_sales():
    """Get all sales entries with filtering options"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    category = request.args.get('category', 'all')
    limit = int(request.args.get('limit', 100))
    
    conn = get_db_connection()
    
    query = '''
        SELECT 
            s.*,
            p.stock as current_stock,
            p.min_stock,
            p.cost as purchase_price,
            p.price as selling_price
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        WHERE s.sale_date BETWEEN ? AND ?
    '''
    params = [date_from, date_to]
    
    if category != 'all':
        query += ' AND s.category = ?'
        params.append(category)
    
    query += ' ORDER BY s.created_at DESC LIMIT ?'
    params.append(limit)
    
    sales = conn.execute(query, params).fetchall()
    
    # Get summary statistics
    summary_query = '''
        SELECT 
            COUNT(DISTINCT bill_id) as total_bills,
            COUNT(*) as total_items,
            SUM(quantity) as total_quantity,
            SUM(total_price) as total_sales,
            SUM(tax_amount) as total_tax,
            SUM(discount_amount) as total_discount,
            AVG(total_price) as avg_sale_value
        FROM sales
        WHERE sale_date BETWEEN ? AND ?
    '''
    summary_params = [date_from, date_to]
    
    if category != 'all':
        summary_query += ' AND category = ?'
        summary_params.append(category)
    
    summary = conn.execute(summary_query, summary_params).fetchone()
    
    conn.close()
    
    return jsonify({
        'sales': [dict(row) for row in sales],
        'summary': dict(summary) if summary else {},
        'filters': {
            'from': date_from,
            'to': date_to,
            'category': category,
            'limit': limit
        }
    })

@app.route('/api/sales/by-product', methods=['GET'])
def get_sales_by_product():
    """Get sales grouped by product"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    product_sales = conn.execute('''
        SELECT 
            s.product_id,
            s.product_name,
            s.category,
            COUNT(DISTINCT s.bill_id) as transactions,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_sales,
            AVG(s.unit_price) as avg_price,
            p.stock as current_stock,
            p.min_stock
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.product_id, s.product_name, s.category
        ORDER BY total_sales DESC
    ''', (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'product_sales': [dict(row) for row in product_sales],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

@app.route('/api/sales/by-category', methods=['GET'])
def get_sales_by_category():
    """Get sales grouped by category"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    category_sales = conn.execute('''
        SELECT 
            s.category,
            COUNT(DISTINCT s.bill_id) as transactions,
            COUNT(DISTINCT s.product_id) as unique_products,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_sales,
            AVG(s.total_price) as avg_sale_value
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.category
        ORDER BY total_sales DESC
    ''', (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'category_sales': [dict(row) for row in category_sales],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

@app.route('/api/sales/by-customer', methods=['GET'])
def get_sales_by_customer():
    """Get sales grouped by customer"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    customer_sales = conn.execute('''
        SELECT 
            s.customer_id,
            s.customer_name,
            COUNT(DISTINCT s.bill_id) as total_bills,
            COUNT(*) as total_items,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_sales,
            AVG(s.total_price) as avg_purchase_value,
            MAX(s.created_at) as last_purchase_date
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.customer_id, s.customer_name
        ORDER BY total_sales DESC
    ''', (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'customer_sales': [dict(row) for row in customer_sales],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

@app.route('/api/sales/daily-summary', methods=['GET'])
def get_daily_sales_summary():
    """Get daily sales summary for a date range"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    daily_summary = conn.execute('''
        SELECT 
            s.sale_date,
            COUNT(DISTINCT s.bill_id) as total_bills,
            COUNT(*) as total_items,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_sales,
            SUM(s.tax_amount) as total_tax,
            AVG(s.total_price) as avg_item_value
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.sale_date
        ORDER BY s.sale_date DESC
    ''', (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'daily_summary': [dict(row) for row in daily_summary],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

@app.route('/api/sales/export', methods=['GET'])
def export_sales():
    """Export sales data in multiple formats"""
    try:
        from flask import make_response
        import csv
        from io import StringIO, BytesIO
        import json
        
        # Get filters
        date_range = request.args.get('date_range', 'all')
        payment_method = request.args.get('payment_method', 'all')
        export_format = request.args.get('format', 'csv')
        
        conn = get_db_connection()
        
        # First check what columns exist in sales table
        cursor = conn.execute("PRAGMA table_info(sales)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Build query with only existing columns
        select_cols = []
        if 'id' in columns:
            select_cols.append('id')
        if 'date' in columns or 'created_at' in columns:
            select_cols.append('date' if 'date' in columns else 'created_at as date')
        if 'customer_name' in columns:
            select_cols.append('customer_name')
        if 'total_amount' in columns or 'amount' in columns:
            select_cols.append('total_amount' if 'total_amount' in columns else 'amount as total_amount')
        if 'payment_method' in columns:
            select_cols.append('payment_method')
        
        # If no columns found, use simple query
        if not select_cols:
            select_cols = ['*']
        
        query = f"SELECT {', '.join(select_cols)} FROM sales WHERE 1=1"
        params = []
        
        # Date filter
        date_col = 'date' if 'date' in columns else 'created_at'
        if date_range == 'today':
            query += f" AND DATE({date_col}) = DATE('now')"
        elif date_range == 'yesterday':
            query += f" AND DATE({date_col}) = DATE('now', '-1 day')"
        elif date_range == 'week':
            query += f" AND DATE({date_col}) >= DATE('now', '-7 days')"
        elif date_range == 'month':
            query += f" AND DATE({date_col}) >= DATE('now', '-30 days')"
        
        # Payment method filter
        if payment_method != 'all' and 'payment_method' in columns:
            query += " AND LOWER(payment_method) = ?"
            params.append(payment_method.lower())
        
        query += f" ORDER BY {date_col} DESC LIMIT 1000"
        
        sales = conn.execute(query, params).fetchall()
        conn.close()
        
        # Create CSV with proper formatting
        output = StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow(['Invoice Number', 'Date', 'Customer Name', 'Amount (INR)', 'Payment Method', 'Status'])
        
        # Write data
        for sale in sales:
            sale_dict = dict(sale)
            invoice_num = sale_dict.get('id', 'N/A')
            date_val = sale_dict.get('date', sale_dict.get('created_at', 'N/A'))
            customer = sale_dict.get('customer_name', 'Walk-in Customer')
            amount = sale_dict.get('total_amount', sale_dict.get('amount', 0))
            payment = sale_dict.get('payment_method', 'Cash')
            
            writer.writerow([
                invoice_num,
                date_val,
                customer,
                f"{amount:.2f}",
                payment,
                'Completed'
            ])
        
        # Create response with proper headers
        output.seek(0)
        csv_data = output.getvalue()
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="sales_export_{date_range}.csv"'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response
        
    except Exception as e:
        print(f"Export error: {str(e)}")  # Log error
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales/payment-methods', methods=['GET'])
def get_sales_by_payment_method():
    """Get sales breakdown by payment method"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    payment_breakdown = conn.execute('''
        SELECT 
            s.payment_method,
            COUNT(DISTINCT s.bill_id) as transactions,
            SUM(s.total_price) as total_amount,
            AVG(s.total_price) as avg_transaction_value
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.payment_method
        ORDER BY total_amount DESC
    ''', (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'payment_breakdown': [dict(row) for row in payment_breakdown],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

# ============================================================================
# CMS (Content Management System) APIs
# ============================================================================

# File Upload API
@app.route('/api/cms/upload', methods=['POST'])
@require_auth
def upload_file():
    """Upload image file for CMS"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Return public URL
        file_url = f"/static/uploads/{filename}"
        return jsonify({
            "message": "File uploaded successfully",
            "url": file_url,
            "filename": filename
        }), 200
    
    return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, svg, webp"}), 400

# Admin CMS APIs (Auth required)

@app.route('/api/cms/admin/settings', methods=['GET', 'PUT'])
@require_auth
def manage_site_settings():
    """Get or update site settings (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        settings = conn.execute('SELECT * FROM cms_site_settings ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        return jsonify(dict(settings) if settings else {})
    
    # PUT - Update settings
    data = request.json
    
    # Check if settings exist
    existing = conn.execute('SELECT id FROM cms_site_settings LIMIT 1').fetchone()
    
    if existing:
        conn.execute('''
            UPDATE cms_site_settings SET
                site_name = ?,
                logo_url = ?,
                favicon_url = ?,
                primary_color = ?,
                secondary_color = ?,
                contact_email = ?,
                contact_phone = ?,
                address = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('site_name'),
            data.get('logo_url'),
            data.get('favicon_url'),
            data.get('primary_color'),
            data.get('secondary_color'),
            data.get('contact_email'),
            data.get('contact_phone'),
            data.get('address'),
            existing['id']
        ))
    else:
        conn.execute('''
            INSERT INTO cms_site_settings (
                site_name, logo_url, favicon_url, primary_color, secondary_color,
                contact_email, contact_phone, address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('site_name'),
            data.get('logo_url'),
            data.get('favicon_url'),
            data.get('primary_color'),
            data.get('secondary_color'),
            data.get('contact_email'),
            data.get('contact_phone'),
            data.get('address')
        ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Settings updated successfully"})

@app.route('/api/cms/admin/hero', methods=['GET', 'PUT'])
@require_auth
def manage_hero_section():
    """Get or update hero section (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        hero = conn.execute('SELECT * FROM cms_hero_section ORDER BY id DESC LIMIT 1').fetchone()
        conn.close()
        return jsonify(dict(hero) if hero else {})
    
    # PUT - Update hero
    data = request.json
    
    existing = conn.execute('SELECT id FROM cms_hero_section LIMIT 1').fetchone()
    
    if existing:
        conn.execute('''
            UPDATE cms_hero_section SET
                title = ?,
                subtitle = ?,
                button_text = ?,
                button_link = ?,
                background_image_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('subtitle'),
            data.get('button_text'),
            data.get('button_link'),
            data.get('background_image_url'),
            existing['id']
        ))
    else:
        conn.execute('''
            INSERT INTO cms_hero_section (title, subtitle, button_text, button_link, background_image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('subtitle'),
            data.get('button_text'),
            data.get('button_link'),
            data.get('background_image_url')
        ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Hero section updated successfully"})

# CRUD for Features
@app.route('/api/cms/admin/features', methods=['GET', 'POST'])
@require_auth
def manage_features():
    """Get all or create feature (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        features = conn.execute('SELECT * FROM cms_features ORDER BY display_order, created_at').fetchall()
        conn.close()
        return jsonify([dict(row) for row in features])
    
    # POST - Create feature
    data = request.json
    feature_id = generate_id()
    
    conn.execute('''
        INSERT INTO cms_features (id, title, description, icon_image_url, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        feature_id,
        data.get('title'),
        data.get('description'),
        data.get('icon_image_url'),
        data.get('display_order', 0),
        data.get('is_active', 1)
    ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Feature created successfully", "id": feature_id}), 201

@app.route('/api/cms/admin/features/<feature_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_feature(feature_id):
    """Get, update or delete a feature (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        feature = conn.execute('SELECT * FROM cms_features WHERE id = ?', (feature_id,)).fetchone()
        conn.close()
        if feature:
            return jsonify(dict(feature))
        return jsonify({"error": "Feature not found"}), 404
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('''
            UPDATE cms_features SET
                title = ?,
                description = ?,
                icon_image_url = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('description'),
            data.get('icon_image_url'),
            data.get('display_order', 0),
            data.get('is_active', 1),
            feature_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Feature updated successfully"})
    
    # DELETE
    conn.execute('DELETE FROM cms_features WHERE id = ?', (feature_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Feature deleted successfully"})

# CRUD for Pricing Plans
@app.route('/api/cms/admin/pricing', methods=['GET', 'POST'])
@require_auth
def manage_pricing_plans():
    """Get all or create pricing plan (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        plans = conn.execute('SELECT * FROM cms_pricing_plans ORDER BY display_order, price_per_month').fetchall()
        conn.close()
        
        result = []
        for plan in plans:
            plan_dict = dict(plan)
            if plan_dict.get('features'):
                try:
                    plan_dict['features'] = json.loads(plan_dict['features'])
                except:
                    plan_dict['features'] = []
            result.append(plan_dict)
        
        return jsonify(result)
    
    # POST - Create plan
    data = request.json
    plan_id = generate_id()
    
    # Convert features array to JSON string
    features_json = json.dumps(data.get('features', []))
    
    conn.execute('''
        INSERT INTO cms_pricing_plans (id, name, price_per_month, description, features, is_popular, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        plan_id,
        data.get('name'),
        data.get('price_per_month'),
        data.get('description'),
        features_json,
        data.get('is_popular', 0),
        data.get('display_order', 0),
        data.get('is_active', 1)
    ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Pricing plan created successfully", "id": plan_id}), 201

@app.route('/api/cms/admin/pricing/<plan_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_pricing_plan(plan_id):
    """Get, update or delete a pricing plan (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        plan = conn.execute('SELECT * FROM cms_pricing_plans WHERE id = ?', (plan_id,)).fetchone()
        conn.close()
        if plan:
            plan_dict = dict(plan)
            if plan_dict.get('features'):
                try:
                    plan_dict['features'] = json.loads(plan_dict['features'])
                except:
                    plan_dict['features'] = []
            return jsonify(plan_dict)
        return jsonify({"error": "Plan not found"}), 404
    
    if request.method == 'PUT':
        data = request.json
        features_json = json.dumps(data.get('features', []))
        
        conn.execute('''
            UPDATE cms_pricing_plans SET
                name = ?,
                price_per_month = ?,
                description = ?,
                features = ?,
                is_popular = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('price_per_month'),
            data.get('description'),
            features_json,
            data.get('is_popular', 0),
            data.get('display_order', 0),
            data.get('is_active', 1),
            plan_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Pricing plan updated successfully"})
    
    # DELETE
    conn.execute('DELETE FROM cms_pricing_plans WHERE id = ?', (plan_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Pricing plan deleted successfully"})

# CRUD for Testimonials
@app.route('/api/cms/admin/testimonials', methods=['GET', 'POST'])
@require_auth
def manage_testimonials():
    """Get all or create testimonial (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        testimonials = conn.execute('SELECT * FROM cms_testimonials ORDER BY display_order, created_at').fetchall()
        conn.close()
        return jsonify([dict(row) for row in testimonials])
    
    # POST - Create testimonial
    data = request.json
    testimonial_id = generate_id()
    
    conn.execute('''
        INSERT INTO cms_testimonials (id, name, role, company, message, avatar_image_url, rating, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        testimonial_id,
        data.get('name'),
        data.get('role'),
        data.get('company'),
        data.get('message'),
        data.get('avatar_image_url'),
        data.get('rating', 5),
        data.get('display_order', 0),
        data.get('is_active', 1)
    ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Testimonial created successfully", "id": testimonial_id}), 201

@app.route('/api/cms/admin/testimonials/<testimonial_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_testimonial(testimonial_id):
    """Get, update or delete a testimonial (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        testimonial = conn.execute('SELECT * FROM cms_testimonials WHERE id = ?', (testimonial_id,)).fetchone()
        conn.close()
        if testimonial:
            return jsonify(dict(testimonial))
        return jsonify({"error": "Testimonial not found"}), 404
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('''
            UPDATE cms_testimonials SET
                name = ?,
                role = ?,
                company = ?,
                message = ?,
                avatar_image_url = ?,
                rating = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?
        ''', (
            data.get('name'),
            data.get('role'),
            data.get('company'),
            data.get('message'),
            data.get('avatar_image_url'),
            data.get('rating', 5),
            data.get('display_order', 0),
            data.get('is_active', 1),
            testimonial_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Testimonial updated successfully"})
    
    # DELETE
    conn.execute('DELETE FROM cms_testimonials WHERE id = ?', (testimonial_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Testimonial deleted successfully"})

# CRUD for FAQs
@app.route('/api/cms/admin/faqs', methods=['GET', 'POST'])
@require_auth
def manage_faqs():
    """Get all or create FAQ (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        faqs = conn.execute('SELECT * FROM cms_faqs ORDER BY display_order, created_at').fetchall()
        conn.close()
        return jsonify([dict(row) for row in faqs])
    
    # POST - Create FAQ
    data = request.json
    faq_id = generate_id()
    
    conn.execute('''
        INSERT INTO cms_faqs (id, question, answer, category, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        faq_id,
        data.get('question'),
        data.get('answer'),
        data.get('category', 'General'),
        data.get('display_order', 0),
        data.get('is_active', 1)
    ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "FAQ created successfully", "id": faq_id}), 201

@app.route('/api/cms/admin/faqs/<faq_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_faq(faq_id):
    """Get, update or delete a FAQ (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        faq = conn.execute('SELECT * FROM cms_faqs WHERE id = ?', (faq_id,)).fetchone()
        conn.close()
        if faq:
            return jsonify(dict(faq))
        return jsonify({"error": "FAQ not found"}), 404
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('''
            UPDATE cms_faqs SET
                question = ?,
                answer = ?,
                category = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?
        ''', (
            data.get('question'),
            data.get('answer'),
            data.get('category', 'General'),
            data.get('display_order', 0),
            data.get('is_active', 1),
            faq_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "FAQ updated successfully"})
    
    # DELETE
    conn.execute('DELETE FROM cms_faqs WHERE id = ?', (faq_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "FAQ deleted successfully"})

# CRUD for Gallery
@app.route('/api/cms/admin/gallery', methods=['GET', 'POST'])
@require_auth
def manage_gallery():
    """Get all or create gallery image (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        category = request.args.get('category')
        if category:
            gallery = conn.execute('SELECT * FROM cms_gallery WHERE category = ? ORDER BY display_order, created_at', (category,)).fetchall()
        else:
            gallery = conn.execute('SELECT * FROM cms_gallery ORDER BY display_order, created_at').fetchall()
        conn.close()
        return jsonify([dict(row) for row in gallery])
    
    # POST - Create gallery image
    data = request.json
    gallery_id = generate_id()
    
    conn.execute('''
        INSERT INTO cms_gallery (id, title, description, image_url, category, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        gallery_id,
        data.get('title'),
        data.get('description'),
        data.get('image_url'),
        data.get('category', 'General'),
        data.get('display_order', 0),
        data.get('is_active', 1)
    ))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Gallery image created successfully", "id": gallery_id}), 201

@app.route('/api/cms/admin/gallery/<gallery_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_gallery_image(gallery_id):
    """Get, update or delete a gallery image (admin only)"""
    conn = get_db_connection()
    
    if request.method == 'GET':
        image = conn.execute('SELECT * FROM cms_gallery WHERE id = ?', (gallery_id,)).fetchone()
        conn.close()
        if image:
            return jsonify(dict(image))
        return jsonify({"error": "Gallery image not found"}), 404
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('''
            UPDATE cms_gallery SET
                title = ?,
                description = ?,
                image_url = ?,
                category = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?
        ''', (
            data.get('title'),
            data.get('description'),
            data.get('image_url'),
            data.get('category', 'General'),
            data.get('display_order', 0),
            data.get('is_active', 1),
            gallery_id
        ))
        conn.commit()
        conn.close()
        return jsonify({"message": "Gallery image updated successfully"})
    
    # DELETE
    conn.execute('DELETE FROM cms_gallery WHERE id = ?', (gallery_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Gallery image deleted successfully"})

# Public CMS APIs (No auth required - for frontend)

@app.route('/api/cms/settings', methods=['GET'])
def get_site_settings():
    """Get site settings (public)"""
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM cms_site_settings ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    if settings:
        return jsonify(dict(settings))
    return jsonify({
        "site_name": "BizPulse ERP",
        "primary_color": "#732C3F",
        "secondary_color": "#F7E8EC"
    })

@app.route('/api/cms/hero', methods=['GET'])
def get_hero_section():
    """Get hero section (public)"""
    conn = get_db_connection()
    hero = conn.execute('SELECT * FROM cms_hero_section ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    if hero:
        return jsonify(dict(hero))
    return jsonify({
        "title": "Welcome to BizPulse",
        "subtitle": "Complete Business Management Solution",
        "button_text": "Get Started",
        "button_link": "/register"
    })

@app.route('/api/cms/features', methods=['GET'])
def get_features():
    """Get all features (public)"""
    conn = get_db_connection()
    features = conn.execute('''
        SELECT * FROM cms_features 
        WHERE is_active = 1 
        ORDER BY display_order, created_at
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in features])

@app.route('/api/cms/pricing', methods=['GET'])
def get_pricing_plans():
    """Get all pricing plans (public)"""
    conn = get_db_connection()
    plans = conn.execute('''
        SELECT * FROM cms_pricing_plans 
        WHERE is_active = 1 
        ORDER BY display_order, price_per_month
    ''').fetchall()
    conn.close()
    
    # Parse features JSON string to array
    result = []
    for plan in plans:
        plan_dict = dict(plan)
        if plan_dict.get('features'):
            try:
                plan_dict['features'] = json.loads(plan_dict['features'])
            except:
                plan_dict['features'] = []
        result.append(plan_dict)
    
    return jsonify(result)

@app.route('/api/cms/testimonials', methods=['GET'])
def get_testimonials():
    """Get all testimonials (public)"""
    conn = get_db_connection()
    testimonials = conn.execute('''
        SELECT * FROM cms_testimonials 
        WHERE is_active = 1 
        ORDER BY display_order, created_at DESC
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in testimonials])

@app.route('/api/cms/faqs', methods=['GET'])
def get_faqs():
    """Get all FAQs (public)"""
    conn = get_db_connection()
    faqs = conn.execute('''
        SELECT * FROM cms_faqs 
        WHERE is_active = 1 
        ORDER BY display_order, created_at
    ''').fetchall()
    conn.close()
    return jsonify([dict(row) for row in faqs])

@app.route('/api/cms/gallery', methods=['GET'])
def get_gallery():
    """Get all gallery images (public)"""
    category = request.args.get('category', 'all')
    
    conn = get_db_connection()
    
    if category == 'all':
        images = conn.execute('''
            SELECT * FROM cms_gallery 
            WHERE is_active = 1 
            ORDER BY display_order, created_at DESC
        ''').fetchall()
    else:
        images = conn.execute('''
            SELECT * FROM cms_gallery 
            WHERE is_active = 1 AND category = ?
            ORDER BY display_order, created_at DESC
        ''', (category,)).fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in images])

# Website Content Save/Load APIs
@app.route('/api/cms/website-content/save', methods=['POST'])
@require_cms_auth
def save_website_content():
    """Save edited website content"""
    data = request.json
    content_html = data.get('content_html')
    page_name = data.get('page_name', 'index')
    
    if not content_html:
        return jsonify({"error": "Content HTML is required"}), 400
    
    conn = get_db_connection()
    
    # Get admin username
    admin_id = session.get('cms_admin_id')
    admin = conn.execute('SELECT username FROM cms_admin_users WHERE id = ?', (admin_id,)).fetchone()
    edited_by = admin['username'] if admin else 'unknown'
    
    # Deactivate previous versions
    conn.execute('''
        UPDATE cms_website_content 
        SET is_active = 0 
        WHERE page_name = ?
    ''', (page_name,))
    
    # Insert new version
    conn.execute('''
        INSERT INTO cms_website_content (page_name, content_html, edited_by, is_active)
        VALUES (?, ?, ?, 1)
    ''', (page_name, content_html, edited_by))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "Website content saved successfully",
        "page_name": page_name,
        "edited_by": edited_by,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/cms/website-content/load', methods=['GET'])
def load_website_content():
    """Load saved website content"""
    page_name = request.args.get('page_name', 'index')
    
    conn = get_db_connection()
    content = conn.execute('''
        SELECT content_html, edited_by, updated_at 
        FROM cms_website_content 
        WHERE page_name = ? AND is_active = 1
        ORDER BY updated_at DESC
        LIMIT 1
    ''', (page_name,)).fetchone()
    conn.close()
    
    if content:
        return jsonify({
            "found": True,
            "content_html": content['content_html'],
            "edited_by": content['edited_by'],
            "updated_at": content['updated_at']
        })
    else:
        return jsonify({
            "found": False,
            "message": "No saved content found"
        })

# CMS Access Page (redirects to login)
@app.route('/cms-access')
def cms_access_page():
    """CMS Access Information Page - Redirects to login"""
    return redirect(url_for('cms_login'))

# CMS Login Page
@app.route('/cms/login', methods=['GET', 'POST'])
def cms_login():
    """CMS Login Page"""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if 'cms_admin_id' in session:
            return redirect(url_for('cms_dashboard'))
        return render_template('cms_login.html')
    
    # POST - Handle login
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    
    conn = get_db_connection()
    
    # Hash the password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Check credentials
    admin = conn.execute('''
        SELECT * FROM cms_admin_users 
        WHERE username = ? AND password_hash = ? AND is_active = 1
    ''', (username, password_hash)).fetchone()
    
    if admin:
        # Update last login
        conn.execute('''
            UPDATE cms_admin_users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (admin['id'],))
        conn.commit()
        
        # Set session
        session['cms_admin_id'] = admin['id']
        session['cms_admin_username'] = admin['username']
        session['cms_admin_name'] = admin['full_name']
        session.permanent = True
        
        conn.close()
        return jsonify({
            "success": True, 
            "message": "Login successful",
            "redirect": url_for('cms_dashboard')
        })
    
    conn.close()
    return jsonify({"success": False, "message": "Invalid username or password"}), 401

# CMS Logout
@app.route('/cms/logout')
def cms_logout():
    """CMS Logout"""
    session.pop('cms_admin_id', None)
    session.pop('cms_admin_username', None)
    session.pop('cms_admin_name', None)
    return redirect(url_for('cms_login'))

# CMS Dashboard Routes
@app.route('/cms')
@require_cms_auth
def cms_dashboard():
    """CMS Dashboard - Overview of all content"""
    return render_template('cms_dashboard.html')

@app.route('/cms/settings')
@require_cms_auth
def cms_settings():
    """CMS Settings Page - Site configuration"""
    return render_template('cms_settings.html')

@app.route('/cms/hero')
@require_cms_auth
def cms_hero():
    """CMS Hero Section Editor"""
    return render_template('cms_hero.html')

@app.route('/cms/features')
@require_cms_auth
def cms_features():
    """CMS Features Manager"""
    return render_template('cms_features.html')

@app.route('/cms/pricing')
@require_cms_auth
def cms_pricing():
    """CMS Pricing Plans Manager"""
    return render_template('cms_pricing.html')

@app.route('/cms/testimonials')
@require_cms_auth
def cms_testimonials():
    """CMS Testimonials Manager"""
    return render_template('cms_testimonials.html')

@app.route('/cms/faqs')
@require_cms_auth
def cms_faqs():
    """CMS FAQs Manager"""
    return render_template('cms_faqs.html')

@app.route('/cms/gallery')
@require_cms_auth
def cms_gallery():
    """CMS Gallery Manager"""
    return render_template('cms_gallery.html')

# CMS Profile & Password Change
@app.route('/cms/profile')
@require_cms_auth
def cms_profile():
    """CMS Admin Profile & Password Change"""
    return render_template('cms_profile.html')

@app.route('/whatsapp-sender')
def whatsapp_sender_page():
    """WhatsApp Report Sender Interface"""
    return render_template('whatsapp_sender.html')

@app.route('/client-management')
def client_management_page():
    """Client Management Interface"""
    return render_template('client_management.html')

@app.route('/cms/change-password', methods=['POST'])
@require_cms_auth
def cms_change_password():
    """Change CMS Admin Password"""
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({"success": False, "message": "Current and new password required"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters"}), 400
    
    conn = get_db_connection()
    
    # Verify current password
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    admin = conn.execute('''
        SELECT * FROM cms_admin_users 
        WHERE id = ? AND password_hash = ?
    ''', (session['cms_admin_id'], current_hash)).fetchone()
    
    if not admin:
        conn.close()
        return jsonify({"success": False, "message": "Current password is incorrect"}), 401
    
    # Update password
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn.execute('''
        UPDATE cms_admin_users 
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_hash, session['cms_admin_id']))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Password changed successfully"})

# ============================================================================
# WhatsApp Daily Reports System
# ============================================================================

# Import report services
try:
    from services.report_service import ReportService
    from services.whatsapp_service import WhatsAppService
    from services.pdf_generator import PDFGenerator
    
    # Initialize services
    report_service = ReportService()
    whatsapp_service = WhatsAppService()
    pdf_generator = PDFGenerator()
    
    print("✅ WhatsApp Report Services loaded successfully")
except ImportError as e:
    print(f"⚠️  WhatsApp Report Services not available: {str(e)}")
    report_service = None
    whatsapp_service = None
    pdf_generator = None

@app.route('/api/whatsapp-reports/generate', methods=['POST'])
@require_auth
def generate_whatsapp_report():
    """
    Generate and send daily report via WhatsApp (Manual trigger)
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        data = request.json or {}
        company_id = data.get('company_id', 'default_company')
        report_date = data.get('report_date')
        
        # Parse report date
        if report_date:
            from datetime import datetime
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            from datetime import date
            report_date = date.today()
        
        # Generate and send report
        result = report_service.send_daily_report_whatsapp(company_id, report_date)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Daily report sent successfully via WhatsApp',
                'company_name': result['company_data']['business_name'],
                'whatsapp_number': result['whatsapp_result']['whatsapp_number'],
                'report_data': result['report_data'],
                'report_date': report_date.strftime('%Y-%m-%d')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred'),
                'company_name': result.get('company_data', {}).get('business_name', 'Unknown')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in generate_whatsapp_report: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Report generation failed: {str(e)}'
        }), 500

@app.route('/api/whatsapp-reports/send-all', methods=['POST'])
@require_auth
def send_all_whatsapp_reports():
    """
    Send daily reports to all companies (Manual trigger for all)
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        data = request.json or {}
        report_date = data.get('report_date')
        
        # Parse report date
        if report_date:
            from datetime import datetime
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            from datetime import date
            report_date = date.today()
        
        # Send reports to all companies
        result = report_service.send_reports_to_all_companies(report_date)
        
        return jsonify({
            'success': True,
            'message': f'Daily reports processed for {result["total_companies"]} companies',
            'summary': {
                'total_companies': result['total_companies'],
                'successful_reports': result['successful_reports'],
                'failed_reports': result['failed_reports'],
                'report_date': result['report_date']
            },
            'results': result['results']
        })
        
    except Exception as e:
        logger.error(f"Error in send_all_whatsapp_reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Bulk report sending failed: {str(e)}'
        }), 500

@app.route('/api/whatsapp-reports/logs', methods=['GET'])
@require_auth
def get_whatsapp_report_logs():
    """
    Get WhatsApp report logs with filtering
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        company_id = request.args.get('company_id')
        days = int(request.args.get('days', 7))
        
        logs = report_service.get_report_logs(company_id, days)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'filters': {
                'company_id': company_id,
                'days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_whatsapp_report_logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get report logs: {str(e)}'
        }), 500

@app.route('/api/whatsapp-reports/companies', methods=['GET'])
@require_auth
def get_companies_for_reports():
    """
    Get all companies configured for WhatsApp reports
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        companies = report_service.get_companies_for_reports()
        
        return jsonify({
            'success': True,
            'companies': companies,
            'total': len(companies)
        })
        
    except Exception as e:
        logger.error(f"Error in get_companies_for_reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get companies: {str(e)}'
        }), 500

@app.route('/api/whatsapp-reports/config/validate', methods=['GET'])
@require_auth
def validate_whatsapp_config():
    """
    Validate WhatsApp API configuration
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        validation_result = report_service.validate_whatsapp_config()
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Error in validate_whatsapp_config: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Configuration validation failed: {str(e)}'
        }), 500

@app.route('/api/whatsapp-reports/test', methods=['POST'])
@require_auth
def test_whatsapp_report():
    """
    Test WhatsApp report generation (PDF only, no sending)
    """
    if not report_service:
        return jsonify({
            'success': False,
            'error': 'WhatsApp report service not available'
        }), 500
    
    try:
        data = request.json or {}
        company_id = data.get('company_id', 'default_company')
        report_date = data.get('report_date')
        
        # Parse report date
        if report_date:
            from datetime import datetime
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            from datetime import date
            report_date = date.today()
        
        # Generate report (PDF only)
        result = report_service.generate_daily_report(company_id, report_date)
        
        if result['success']:
            # Clean up the PDF file after generation
            try:
                pdf_generator.cleanup_temp_files(result['pdf_path'])
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': 'Test report generated successfully',
                'company_name': result['company_data']['business_name'],
                'report_data': result['report_data'],
                'report_date': report_date.strftime('%Y-%m-%d')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in test_whatsapp_report: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Test report generation failed: {str(e)}'
        }), 500

# Company Management APIs for WhatsApp Reports
@app.route('/api/companies', methods=['GET'])
@require_auth
def get_companies():
    """Get all companies"""
    conn = get_db_connection()
    companies = conn.execute('SELECT * FROM companies ORDER BY business_name').fetchall()
    conn.close()
    return jsonify([dict(row) for row in companies])

@app.route('/api/companies', methods=['POST'])
@require_auth
def create_company():
    """Create new company"""
    data = request.json
    company_id = generate_id()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO companies (
            id, business_name, phone_number, whatsapp_number, email, address,
            send_daily_report, report_time, timezone, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        company_id,
        data.get('business_name'),
        data.get('phone_number'),
        data.get('whatsapp_number'),
        data.get('email'),
        data.get('address'),
        data.get('send_daily_report', 1),
        data.get('report_time', '23:55:00'),
        data.get('timezone', 'Asia/Kolkata'),
        data.get('is_active', 1)
    ))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Company created successfully',
        'company_id': company_id
    }), 201

@app.route('/api/companies/<company_id>', methods=['PUT'])
@require_auth
def update_company(company_id):
    """Update company details"""
    data = request.json
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE companies SET
            business_name = ?,
            phone_number = ?,
            whatsapp_number = ?,
            email = ?,
            address = ?,
            send_daily_report = ?,
            report_time = ?,
            timezone = ?,
            is_active = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('business_name'),
        data.get('phone_number'),
        data.get('whatsapp_number'),
        data.get('email'),
        data.get('address'),
        data.get('send_daily_report', 1),
        data.get('report_time', '23:55:00'),
        data.get('timezone', 'Asia/Kolkata'),
        data.get('is_active', 1),
        company_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Company updated successfully'
    })

# ============================================================================
# Scheduled Job System (Background Tasks)
# ============================================================================

def run_daily_reports_job():
    """
    Background job to send daily reports at scheduled time
    This should be called by a scheduler (cron job or task scheduler)
    """
    if not report_service:
        print("❌ WhatsApp report service not available")
        return
    
    try:
        from datetime import date
        today = date.today()
        
        print(f"🕐 Starting scheduled daily reports job - {today}")
        
        # Send reports to all companies
        result = report_service.send_reports_to_all_companies(today)
        
        print(f"✅ Daily reports job completed:")
        print(f"   - Total companies: {result['total_companies']}")
        print(f"   - Successful: {result['successful_reports']}")
        print(f"   - Failed: {result['failed_reports']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Daily reports job failed: {str(e)}")
        return {'success': False, 'error': str(e)}

# Manual trigger endpoint for scheduled job (for testing)
@app.route('/api/whatsapp-reports/run-scheduled-job', methods=['POST'])
@require_auth
def run_scheduled_job():
    """
    Manually trigger the scheduled daily reports job (for testing)
    """
    try:
        result = run_daily_reports_job()
        
        if result and result.get('success', True):
            return jsonify({
                'success': True,
                'message': 'Scheduled job executed successfully',
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Job execution failed')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Job execution failed: {str(e)}'
        }), 500

# ============================================================================
# Client Management System APIs
# ============================================================================

@app.route('/api/clients', methods=['GET'])
@require_auth
def get_clients():
    """Get all clients"""
    try:
        conn = get_db_connection()
        clients = conn.execute('''
            SELECT id, company_name, contact_email, contact_name, phone_number, 
                   whatsapp_number, business_address, business_type, gst_number,
                   username, is_active, last_login, created_at, updated_at
            FROM clients 
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'clients': [dict(row) for row in clients],
            'total': len(clients)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get clients: {str(e)}'
        }), 500

@app.route('/api/clients', methods=['POST'])
@require_auth
def create_client():
    """Create new client with auto-generated credentials"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('company_name') or not data.get('contact_email'):
            return jsonify({
                'success': False,
                'error': 'Company name and contact email are required'
            }), 400
        
        # Generate client ID
        client_id = generate_id()
        
        # Hash the password
        password_hash = hash_password(data['password'])
        
        conn = get_db_connection()
        
        # Check if email or username already exists
        existing = conn.execute('''
            SELECT id FROM clients 
            WHERE contact_email = ? OR username = ?
        ''', (data['contact_email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new client
        conn.execute('''
            INSERT INTO clients (
                id, company_name, contact_email, contact_name, phone_number,
                whatsapp_number, business_address, business_type, gst_number,
                username, password_hash, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id,
            data['company_name'],
            data['contact_email'],
            data.get('contact_name'),
            data.get('phone_number'),
            data.get('whatsapp_number'),
            data.get('business_address'),
            data.get('business_type', 'retail'),
            data.get('gst_number'),
            data['username'],
            password_hash,
            1
        ))
        
        # Also create a company record for WhatsApp reports
        company_id = f"client_{client_id}"
        conn.execute('''
            INSERT INTO companies (
                id, business_name, phone_number, whatsapp_number, email, address,
                send_daily_report, report_time, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_id,
            data['company_name'],
            data.get('phone_number'),
            data.get('whatsapp_number'),
            data['contact_email'],
            data.get('business_address'),
            1,  # Enable daily reports by default
            '23:55:00',
            1
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Client created successfully',
            'client_id': client_id,
            'username': data['username'],
            'password': data['password']  # Return plain password for display
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create client: {str(e)}'
        }), 500

@app.route('/api/clients/<client_id>', methods=['GET'])
@require_auth
def get_client(client_id):
    """Get specific client details"""
    try:
        conn = get_db_connection()
        client = conn.execute('''
            SELECT * FROM clients WHERE id = ?
        ''', (client_id,)).fetchone()
        conn.close()
        
        if client:
            return jsonify({
                'success': True,
                'client': dict(client)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get client: {str(e)}'
        }), 500

@app.route('/api/clients/<client_id>', methods=['PUT'])
@require_auth
def update_client(client_id):
    """Update client details"""
    try:
        data = request.json
        
        conn = get_db_connection()
        
        # Check if client exists
        client = conn.execute('SELECT id FROM clients WHERE id = ?', (client_id,)).fetchone()
        if not client:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Update client
        conn.execute('''
            UPDATE clients SET
                company_name = ?,
                contact_email = ?,
                contact_name = ?,
                phone_number = ?,
                whatsapp_number = ?,
                business_address = ?,
                business_type = ?,
                gst_number = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('company_name'),
            data.get('contact_email'),
            data.get('contact_name'),
            data.get('phone_number'),
            data.get('whatsapp_number'),
            data.get('business_address'),
            data.get('business_type'),
            data.get('gst_number'),
            client_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Client updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update client: {str(e)}'
        }), 500

@app.route('/api/clients/<client_id>/reset-password', methods=['POST'])
@require_auth
def reset_client_password(client_id):
    """Reset client password"""
    try:
        # Generate new password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        conn = get_db_connection()
        
        # Update password
        result = conn.execute('''
            UPDATE clients SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, client_id))
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully',
            'new_password': new_password
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to reset password: {str(e)}'
        }), 500

@app.route('/api/clients/<client_id>/toggle-status', methods=['POST'])
@require_auth
def toggle_client_status(client_id):
    """Toggle client active/inactive status"""
    try:
        data = request.json
        is_active = data.get('is_active', True)
        
        conn = get_db_connection()
        
        # Update status
        result = conn.execute('''
            UPDATE clients SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (is_active, client_id))
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Client {"activated" if is_active else "deactivated"} successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update status: {str(e)}'
        }), 500

@app.route('/api/clients/export', methods=['GET'])
@require_auth
def export_clients():
    """Export clients to CSV"""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        conn = get_db_connection()
        clients = conn.execute('''
            SELECT company_name, contact_email, contact_name, phone_number,
                   whatsapp_number, business_type, username, 
                   CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
                   created_at
            FROM clients 
            ORDER BY created_at DESC
        ''').fetchall()
        conn.close()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Company Name', 'Contact Email', 'Contact Person', 'Phone Number',
            'WhatsApp Number', 'Business Type', 'Username', 'Status', 'Created Date'
        ])
        
        # Write data
        for client in clients:
            writer.writerow([
                client['company_name'],
                client['contact_email'],
                client['contact_name'] or 'N/A',
                client['phone_number'] or 'N/A',
                client['whatsapp_number'] or 'N/A',
                client['business_type'],
                client['username'],
                client['status'],
                client['created_at']
            ])
        
        # Create response
        output.seek(0)
        csv_data = output.getvalue()
        
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="clients_export_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to export clients: {str(e)}'
        }), 500

# Enhanced login API to support client login
@app.route('/api/auth/client-login', methods=['POST'])
def client_login():
    """Client login with username/password"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        conn = get_db_connection()
        
        # Check client credentials
        client = conn.execute('''
            SELECT id, company_name, contact_email, username, password_hash, is_active
            FROM clients 
            WHERE username = ? AND is_active = 1
        ''', (username,)).fetchone()
        
        if client and hash_password(password) == client['password_hash']:
            # Update last login
            conn.execute('''
                UPDATE clients SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (client['id'],))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': f"client_token_{client['id']}",
                'user': {
                    'id': client['id'],
                    'username': client['username'],
                    'company_name': client['company_name'],
                    'email': client['contact_email'],
                    'user_type': 'client'
                }
            })
        else:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500



if __name__ == '__main__':
    init_db()
    
    # Get local IP address
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "localhost"
    
    print("=" * 70)
    print("🚀 BizPulse ERP System Starting...")
    print("=" * 70)
    print(f"✅ Database initialized with sample data")
    print(f"✅ Server running on all interfaces (0.0.0.0:5000)")
    print(f"✅ FREE WhatsApp Reports System Ready!")
    print()
    print("📱 [MOBILE ACCESS]:")
    print(f"   Mobile App: http://{local_ip}:5000/mobile-simple")
    print(f"   Login: bizpulse.erp@gmail.com / demo123")
    print()
    print("🖥️  [DESKTOP ACCESS]:")
    print(f"   Main Site: http://localhost:5000")
    print(f"   Network: http://{local_ip}:5000")
    print()
    print("📊 [WHATSAPP REPORTS - NEW!]:")
    print(f"   WhatsApp Sender: http://localhost:5000/whatsapp-sender")
    print(f"   🎉 FREE Service - No API keys required!")
    print(f"   📱 Send daily reports via WhatsApp instantly")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Mobile and laptop must be on SAME WiFi")
    print("   - Allow Python through Windows Firewall")
    print("   - For WhatsApp reports: Open /whatsapp-sender")
    print("=" * 70)
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)