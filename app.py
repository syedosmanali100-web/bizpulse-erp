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
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)
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
            barcode_data TEXT UNIQUE,
            barcode_image TEXT,
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
    
    # Client Users table (employees created by clients)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_users (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_plain TEXT,
            role TEXT NOT NULL DEFAULT 'employee',
            department TEXT,
            phone_number TEXT,
            is_active BOOLEAN DEFAULT 1,
            permissions TEXT DEFAULT '{}',
            last_login TIMESTAMP,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (created_by) REFERENCES clients (id)
        )
    ''')
    
    # Add password_plain column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE client_users ADD COLUMN password_plain TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Add barcode fields to products table if they don't exist
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN barcode_data TEXT UNIQUE')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN barcode_image TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Create index on barcode_data for fast lookups
    try:
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode_data)')
    except sqlite3.OperationalError:
        pass
    
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
    
    # Staff table for business owners to add their staff
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id TEXT PRIMARY KEY,
            business_owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            role TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_owner_id) REFERENCES clients (id)
        )
    ''')

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

def get_current_client_id():
    """Get the current client ID from session, handling both client and employee sessions"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')  # For employees, use client_id
    else:
        return session.get('user_id')    # For clients, use user_id

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Set current user ID from session (don't override with dummy value)
        request.current_user_id = get_current_client_id()
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

# Super Admin Authentication decorator
def require_super_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_super_admin', False):
            return render_template('error.html', 
                                 error_title="Access Denied", 
                                 error_message="This module is only available to super administrators (bizpulse.erp@gmail.com)."), 403
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

@app.route('/mobile-dashboard')
def mobile_dashboard():
    """Mobile ERP Dashboard - Original interface"""
    return render_template('mobile_simple_working.html')

@app.route('/mobile-simple')
def mobile_simple():
    """Direct redirect to mobile dashboard"""
    return redirect('/mobile-dashboard')

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
        "features": ["products", "customers", "reports"]
    })

# Retail Management module routes
@app.route('/retail/products')
def retail_products_page():
    return render_template('retail_products.html')

@app.route('/retail/customers')
def retail_customers():
    return render_template('retail_customers.html')

@app.route('/retail/billing')
@require_auth
def retail_billing():
    return render_template('retail_billing.html')

@app.route('/retail/dashboard')
@require_auth
def retail_dashboard():
    return render_template('retail_dashboard.html')

@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get comprehensive dashboard statistics with real-time data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Today's Revenue (from bills)
        today_revenue = cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as revenue,
                   COUNT(*) as transactions
            FROM bills 
            WHERE DATE(created_at) = ?
        ''', (today,)).fetchone()
        
        # Today's Cost & Profit (from sales with product cost)
        today_profit_data = cursor.execute('''
            SELECT 
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(s.quantity * p.cost), 0) as total_cost
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE s.sale_date = ?
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
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            # Frontend expects these keys
            'today_revenue': float(today_revenue['revenue']),
            'today_orders': today_revenue['transactions'],
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
                'revenue': float(today_revenue['revenue']),
                'transactions': today_revenue['transactions'],
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
        })
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/retail/profile')
def retail_profile():
    return render_template('retail_profile.html')

@app.route('/test-reports')
def test_reports():
    return "<h1>🎉 Reports Module Working!</h1><p>Route is active!</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@app.route('/retail/sales')
def retail_sales():
    return render_template('retail_sales_professional.html')

@app.route('/retail/sales-old')
def retail_sales_old():
    return render_template('retail_sales_enhanced.html')

@app.route('/retail/inventory')
def retail_inventory():
    return render_template('inventory_professional.html')

@app.route('/retail/settings')
def retail_settings():
    return render_template('settings_professional.html')

@app.route('/test-navigation')
def test_navigation():
    return render_template('test_navigation.html')

@app.route('/test-permissions')
def test_permissions():
    return render_template('test_permissions.html')

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
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'success',
        'message': 'Server is running and accessible!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/auth/unified-login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    # Handle both login_id and loginId (mobile uses loginId)
    login_id = data.get('loginId') or data.get('login_id') or data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not login_id or not password:
        return jsonify({'message': 'Login ID and password are required'}), 400
    
    # Demo login - in production, validate against database
    if login_id == "bizpulse.erp@gmail.com" and password == "demo123":
        session['user_id'] = 'demo_user'
        session['user_name'] = 'Demo User'
        session['user_type'] = 'client'
        session.permanent = True
        
        return jsonify({
            "message": "Login successful",
            "token": "demo-jwt-token",
            "user": {
                "id": "demo_user",
                "email": login_id,
                "name": "Demo User",
                "type": "client",
                "business_type": "both"
            }
        })
    
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/auth/unified-login', methods=['POST'])
def api_unified_login():
    """Unified login for both admin and client users"""
    data = request.json
    login_id = data.get('loginId')  # Can be email or username
    password = data.get('password')
    
    conn = get_db_connection()
    
    try:
        # First check admin credentials (demo)
        demo_admin_credentials = [
            {"id": "admin@demo.com", "password": "demo123", "type": "admin", "name": "Admin User"},
            {"id": "bizpulse.erp@gmail.com", "password": "demo123", "type": "admin", "name": "BizPulse Admin"},
            {"id": "demo", "password": "demo123", "type": "admin", "name": "Demo Admin"},
        ]
        
        for cred in demo_admin_credentials:
            if cred["id"] == login_id and cred["password"] == password:
                # Set session data for role-based access
                session['user_id'] = cred["id"]
                session['user_type'] = cred["type"]
                session['user_name'] = cred["name"]
                session['is_super_admin'] = (cred["id"] == "bizpulse.erp@gmail.com")  # Only your credentials
                
                conn.close()
                return jsonify({
                    "message": "Login successful",
                    "token": "demo-jwt-token",
                    "user": {
                        "id": cred["id"],
                        "name": cred["name"],
                        "type": cred["type"],
                        "business_type": "both",
                        "is_super_admin": session['is_super_admin']
                    }
                })
        
        # Then check client database (business owners)
        client = conn.execute('''
            SELECT id, company_name, contact_email, username, password_hash, is_active
            FROM clients 
            WHERE (contact_email = ? OR username = ?) AND is_active = 1
        ''', (login_id, login_id)).fetchone()
        
        if client and hash_password(password) == client['password_hash']:
            # Set session data for role-based access
            session['user_id'] = client['id']
            session['user_type'] = "client"
            session['user_name'] = client['company_name']
            session['is_super_admin'] = False  # Clients are never super admin
            
            conn.close()
            return jsonify({
                "message": "Login successful",
                "token": "client-jwt-token",
                "user": {
                    "id": client['id'],
                    "name": client['company_name'],
                    "email": client['contact_email'],
                    "username": client['username'],
                    "type": "client",
                    "business_type": "both",
                    "is_super_admin": False
                }
            })
        
        # Finally check staff database
        staff = conn.execute('''
            SELECT s.id, s.name, s.email, s.username, s.password_hash, s.role, s.is_active, s.business_owner_id,
                   c.company_name as business_name
            FROM staff s
            JOIN clients c ON s.business_owner_id = c.id
            WHERE (s.email = ? OR s.username = ?) AND s.is_active = 1
        ''', (login_id, login_id)).fetchone()
        
        if staff and hash_password(password) == staff['password_hash']:
            # Set session data for staff member
            session['user_id'] = staff['id']
            session['user_type'] = "staff"
            session['user_name'] = staff['name']
            session['business_owner_id'] = staff['business_owner_id']
            session['staff_role'] = staff['role']
            session['is_super_admin'] = False  # Staff are never super admin
            
            conn.close()
            return jsonify({
                "message": "Login successful",
                "token": "staff-jwt-token",
                "user": {
                    "id": staff['id'],
                    "name": staff['name'],
                    "email": staff['email'],
                    "username": staff['username'],
                    "type": "staff",
                    "role": staff['role'],
                    "business_name": staff['business_name'],
                    "business_type": "both",
                    "is_super_admin": False
                }
            })
        
        # Finally check client users (employees)
        client_user = conn.execute('''
            SELECT cu.id, cu.full_name, cu.email, cu.username, cu.password_hash, cu.is_active, cu.role, cu.client_id,
                   c.company_name
            FROM client_users cu
            JOIN clients c ON cu.client_id = c.id
            WHERE (cu.email = ? OR cu.username = ?) AND cu.is_active = 1 AND c.is_active = 1
        ''', (login_id, login_id)).fetchone()
        
        if client_user and hash_password(password) == client_user['password_hash']:
            # Set session data for employee user
            session['user_id'] = client_user['id']
            session['user_type'] = "employee"
            session['user_name'] = client_user['full_name']
            session['client_id'] = client_user['client_id']
            session['is_super_admin'] = False
            
            # Update last login
            conn.execute('''
                UPDATE client_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (client_user['id'],))
            conn.commit()
            
            conn.close()
            return jsonify({
                "message": "Login successful",
                "token": "employee-jwt-token",
                "user": {
                    "id": client_user['id'],
                    "name": client_user['full_name'],
                    "email": client_user['email'],
                    "username": client_user['username'],
                    "type": "employee",
                    "role": client_user['role'],
                    "company": client_user['company_name'],
                    "business_type": "both",
                    "is_super_admin": False
                }
            })
        
        conn.close()
        return jsonify({"message": "Invalid credentials"}), 401
        
    except Exception as e:
        conn.close()
        return jsonify({"message": "Login error", "error": str(e)}), 500

@app.route('/api/auth/user-info', methods=['GET'])
def get_user_info():
    """Get current user information including role"""
    return jsonify({
        "user_id": session.get('user_id'),
        "user_type": session.get('user_type'),
        "user_name": session.get('user_name'),
        "is_super_admin": session.get('is_super_admin', False),
        "staff_role": session.get('staff_role')  # For staff members
    })

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

@app.route('/api/products/debug', methods=['GET'])
def debug_products():
    """Debug endpoint to see all products with barcode data"""
    try:
        conn = get_db_connection()
        products = conn.execute('''
            SELECT id, name, code, barcode_data, price, stock 
            FROM products 
            WHERE is_active = 1 
            ORDER BY created_at DESC
            LIMIT 20
        ''').fetchall()
        conn.close()
        
        return jsonify({
            "success": True,
            "total_products": len(products),
            "products": [dict(p) for p in products]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/test/barcode/<barcode>', methods=['GET'])
def test_barcode_route(barcode):
    """Simple test route to check if barcode routes work"""
    return jsonify({
        "success": True,
        "message": f"Barcode route working! Received: {barcode}",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/products/<product_id>/add-barcode', methods=['POST'])
def add_barcode_to_product(product_id):
    """Add barcode to existing product"""
    try:
        data = request.json
        barcode = data.get('barcode', '').strip()
        
        if not barcode:
            return jsonify({"success": False, "error": "Barcode is required"}), 400
        
        conn = get_db_connection()
        
        # Check if product exists
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            conn.close()
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        # Update product with barcode
        conn.execute('''
            UPDATE products 
            SET barcode_data = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (barcode, product_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Barcode {barcode} added to product {product['name']}",
            "product_id": product_id,
            "barcode": barcode
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/products/search/barcode/<barcode>', methods=['GET'])
def search_product_by_barcode(barcode):
    """Search product by barcode data - Production ready with enhanced logging"""
    try:
        print(f"🔍 [BARCODE SEARCH] Searching for barcode: '{barcode}'")
        
        # Validate barcode input
        if not barcode or len(barcode.strip()) == 0:
            print(f"❌ [BARCODE SEARCH] Invalid barcode - empty or null")
            return jsonify({
                "success": False,
                "error": "Invalid barcode - empty or null"
            }), 400
        
        barcode = barcode.strip()
        print(f"🔍 [BARCODE SEARCH] Cleaned barcode: '{barcode}' (length: {len(barcode)})")
        
        conn = get_db_connection()
        
        # Debug: Check all products with barcodes
        all_barcodes = conn.execute('''
            SELECT id, name, barcode_data FROM products 
            WHERE barcode_data IS NOT NULL AND barcode_data != '' AND is_active = 1
        ''').fetchall()
        
        print(f"🔍 [BARCODE SEARCH] Available barcodes in database: {len(all_barcodes)}")
        for bc in all_barcodes:
            print(f"   - Product: {bc['name']}, Barcode: '{bc['barcode_data']}'")
        
        # EXACT MATCH ONLY - Primary lookup by barcode_data
        product = conn.execute('''
            SELECT * FROM products 
            WHERE barcode_data = ? AND is_active = 1
            LIMIT 1
        ''', (barcode,)).fetchone()
        
        conn.close()
        
        if product:
            print(f"✅ [BARCODE SEARCH] Found product: {product['name']} (ID: {product['id']})")
            return jsonify({
                "success": True,
                "product": dict(product)
            }), 200
        else:
            print(f"❌ [BARCODE SEARCH] No product found for barcode: '{barcode}'")
            print(f"❌ [BARCODE SEARCH] Available barcodes: {[bc['barcode_data'] for bc in all_barcodes]}")
            return jsonify({
                "success": False,
                "message": f"Product not found for barcode: {barcode}",
                "barcode": barcode,
                "available_barcodes": [bc['barcode_data'] for bc in all_barcodes]  # Debug info
            }), 404
            
    except Exception as e:
        print(f"❌ [BARCODE SEARCH] Error: {str(e)}")
        import traceback
        print(f"❌ [BARCODE SEARCH] Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Search failed: {str(e)}",
            "barcode": barcode
        }), 500

@app.route('/api/products', methods=['POST'])
@require_auth
def add_product():
    try:
        data = request.json
        print(f"[PRODUCT ADD] Received data: {data}")
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('price'):
            return jsonify({
                "success": False,
                "error": "Product name and price are required"
            }), 400
        
        # Extract and validate barcode data
        barcode_data = data.get('barcode_data', '').strip() if data.get('barcode_data') else None
        barcode_image = data.get('barcode_image')
        
        conn = get_db_connection()
        
        # CRITICAL: Check if barcode already exists (if provided)
        if barcode_data:
            existing_barcode = conn.execute('''
                SELECT id, name FROM products 
                WHERE barcode_data = ? AND is_active = 1
            ''', (barcode_data,)).fetchone()
            
            if existing_barcode:
                conn.close()
                return jsonify({
                    "success": False,
                    "error": f"Product already exists with this barcode",
                    "existing_product": {
                        "id": existing_barcode['id'],
                        "name": existing_barcode['name']
                    },
                    "barcode": barcode_data
                }), 409  # Conflict status code
        
        # Generate product ID and code
        product_id = generate_id()
        product_code = data.get('code', '').strip() or f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Check if product code already exists
        existing_code = conn.execute('SELECT id FROM products WHERE code = ?', (product_code,)).fetchone()
        if existing_code:
            product_code = f"{product_code}_{datetime.now().strftime('%H%M%S')}"
        
        # Insert product with all validations
        try:
            conn.execute('''
                INSERT INTO products (
                    id, code, name, category, price, cost, stock, min_stock, 
                    unit, business_type, barcode_data, barcode_image, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id, 
                product_code, 
                data['name'].strip(), 
                data.get('category', 'General'),
                float(data['price']), 
                float(data.get('cost', 0)), 
                int(data.get('stock', 0)),
                int(data.get('min_stock', 0)), 
                data.get('unit', 'piece'), 
                data.get('business_type', 'both'),
                barcode_data,  # Store scanned barcode value (unique)
                barcode_image,  # Store barcode image
                1  # is_active
            ))
            
            conn.commit()
            print(f"[PRODUCT ADD] Successfully added product: {product_id}")
            
        except sqlite3.IntegrityError as e:
            conn.close()
            if 'barcode_data' in str(e):
                return jsonify({
                    "success": False,
                    "error": "Product with this barcode already exists",
                    "barcode": barcode_data
                }), 409
            else:
                return jsonify({
                    "success": False,
                    "error": f"Database constraint error: {str(e)}"
                }), 400
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Product added successfully", 
            "product": {
                "id": product_id,
                "code": product_code,
                "name": data['name'],
                "barcode": barcode_data
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        print(f"[PRODUCT ADD] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to add product: {str(e)}"
        }), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
@require_auth
def delete_product(product_id):
    """Delete product completely from database"""
    try:
        print(f"[PRODUCT DELETE] Deleting product: {product_id}")
        
        conn = get_db_connection()
        
        # Check if product exists
        product = conn.execute('''
            SELECT id, name, barcode_data FROM products WHERE id = ?
        ''', (product_id,)).fetchone()
        
        if not product:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Product not found"
            }), 404
        
        # HARD DELETE - Remove from database completely
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        print(f"[PRODUCT DELETE] Successfully deleted: {product['name']}")
        
        return jsonify({
            "success": True,
            "message": f"Product '{product['name']}' deleted successfully",
            "deleted_product": {
                "id": product_id,
                "name": product['name'],
                "barcode": product['barcode_data']
            }
        }), 200
        
    except Exception as e:
        print(f"[PRODUCT DELETE] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to delete product: {str(e)}"
        }), 500

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

# Sales Module APIs - Mobile ERP Perfect Implementation
@app.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Get sales summary - Mobile ERP Perfect Style"""
    try:
        conn = get_db_connection()
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        
        # Today's sales from sales table (mobile ERP style)
        today_stats = conn.execute('''
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total
            FROM sales 
            WHERE sale_date = ?
        ''', (today,)).fetchone()
        
        # Yesterday's sales from sales table
        yesterday_stats = conn.execute('''
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total
            FROM sales 
            WHERE sale_date = ?
        ''', (yesterday,)).fetchone()
        
        # Week's sales
        week_stats = conn.execute('''
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total
            FROM sales 
            WHERE sale_date >= ?
        ''', (week_start,)).fetchone()
        
        # Month's sales
        month_stats = conn.execute('''
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total
            FROM sales 
            WHERE sale_date >= ?
        ''', (month_start,)).fetchone()
        
        # All time sales
        all_time_stats = conn.execute('''
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(total_price), 0) as total
            FROM sales
        ''').fetchone()
        
        # Top products today (mobile ERP style)
        top_products = conn.execute('''
            SELECT 
                product_name,
                SUM(quantity) as quantity,
                SUM(total_price) as revenue
            FROM sales 
            WHERE sale_date = ?
            GROUP BY product_id, product_name
            ORDER BY quantity DESC
            LIMIT 5
        ''', (today,)).fetchall()
        
        # Recent transactions from bills table
        recent_transactions = conn.execute('''
            SELECT b.bill_number, b.total_amount, b.created_at, c.name as customer_name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            ORDER BY b.created_at DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            "today": {
                "count": today_stats['count'],
                "total": float(today_stats['total'])
            },
            "yesterday": {
                "count": yesterday_stats['count'],
                "total": float(yesterday_stats['total'])
            },
            "week": {
                "count": week_stats['count'],
                "total": float(week_stats['total'])
            },
            "month": {
                "count": month_stats['count'],
                "total": float(month_stats['total'])
            },
            "all_time": {
                "count": all_time_stats['count'],
                "total": float(all_time_stats['total'])
            },
            "top_products": [dict(row) for row in top_products],
            "recent_transactions": [dict(row) for row in recent_transactions],
            "timezone": "Local Time (IST)",
            "current_date": today
        })
        
    except Exception as e:
        print(f"❌ Sales summary error: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

# Inventory Management APIs - Complete integration with Products, Sales, and Bills
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get complete inventory status with stock levels, sales data, and alerts"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Get IST timezone
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        today_ist = now_ist.strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Get all products with stock information and recent sales
        inventory = conn.execute('''
            SELECT 
                p.*,
                COALESCE(recent_sales.total_sold_today, 0) as sold_today,
                COALESCE(recent_sales.total_sold_week, 0) as sold_week,
                COALESCE(recent_sales.total_sold_month, 0) as sold_month,
                COALESCE(recent_sales.last_sale_date, 'Never') as last_sale_date,
                CASE 
                    WHEN p.stock <= 0 THEN 'out_of_stock'
                    WHEN p.stock <= p.min_stock THEN 'low_stock'
                    WHEN p.stock <= (p.min_stock * 2) THEN 'warning'
                    ELSE 'good'
                END as stock_status,
                (p.price - p.cost) as profit_per_unit,
                ((p.price - p.cost) / p.price * 100) as profit_margin_percent
            FROM products p
            LEFT JOIN (
                SELECT 
                    s.product_id,
                    SUM(CASE WHEN DATE(s.created_at) = ? THEN s.quantity ELSE 0 END) as total_sold_today,
                    SUM(CASE WHEN DATE(s.created_at) >= DATE(?, '-7 days') THEN s.quantity ELSE 0 END) as total_sold_week,
                    SUM(CASE WHEN DATE(s.created_at) >= DATE(?, '-30 days') THEN s.quantity ELSE 0 END) as total_sold_month,
                    MAX(DATE(s.created_at)) as last_sale_date
                FROM sales s
                GROUP BY s.product_id
            ) recent_sales ON p.id = recent_sales.product_id
            WHERE p.is_active = 1
            ORDER BY 
                CASE 
                    WHEN p.stock <= 0 THEN 1
                    WHEN p.stock <= p.min_stock THEN 2
                    WHEN p.stock <= (p.min_stock * 2) THEN 3
                    ELSE 4
                END,
                p.name
        ''', (today_ist, today_ist, today_ist)).fetchall()
        
        # Get inventory summary statistics
        summary = conn.execute('''
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN stock <= 0 THEN 1 END) as out_of_stock_count,
                COUNT(CASE WHEN stock <= min_stock AND stock > 0 THEN 1 END) as low_stock_count,
                COUNT(CASE WHEN stock > min_stock THEN 1 END) as good_stock_count,
                COALESCE(SUM(stock * cost), 0) as total_inventory_value,
                COALESCE(SUM(stock * price), 0) as total_selling_value,
                COALESCE(SUM(stock * (price - cost)), 0) as potential_profit
            FROM products 
            WHERE is_active = 1
        ''').fetchone()
        
        # Get top selling products (last 30 days)
        top_selling = conn.execute('''
            SELECT 
                p.name as product_name,
                p.category,
                SUM(s.quantity) as total_sold,
                SUM(s.total_price) as total_revenue,
                SUM(s.total_price - (p.cost * s.quantity)) as total_profit,
                p.stock as current_stock
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE DATE(s.created_at) >= DATE(?, '-30 days')
            GROUP BY s.product_id, p.name, p.category, p.stock
            ORDER BY total_sold DESC
            LIMIT 10
        ''', (today_ist,)).fetchall()
        
        # Get products needing restock (critical alerts)
        restock_alerts = conn.execute('''
            SELECT 
                p.name,
                p.category,
                p.stock,
                p.min_stock,
                (p.min_stock - p.stock) as shortage,
                COALESCE(recent_sales.avg_daily_sales, 0) as avg_daily_sales,
                CASE 
                    WHEN COALESCE(recent_sales.avg_daily_sales, 0) > 0 
                    THEN CAST(p.stock / recent_sales.avg_daily_sales AS INTEGER)
                    ELSE 999
                END as days_remaining
            FROM products p
            LEFT JOIN (
                SELECT 
                    product_id,
                    AVG(daily_sales) as avg_daily_sales
                FROM (
                    SELECT 
                        product_id,
                        DATE(created_at) as sale_date,
                        SUM(quantity) as daily_sales
                    FROM sales
                    WHERE DATE(created_at) >= DATE(?, '-30 days')
                    GROUP BY product_id, DATE(created_at)
                ) daily_totals
                GROUP BY product_id
            ) recent_sales ON p.id = recent_sales.product_id
            WHERE p.stock <= p.min_stock AND p.is_active = 1
            ORDER BY 
                CASE WHEN p.stock <= 0 THEN 1 ELSE 2 END,
                days_remaining ASC
        ''', (today_ist,)).fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "inventory": [dict(row) for row in inventory],
            "summary": dict(summary) if summary else {},
            "top_selling": [dict(row) for row in top_selling],
            "restock_alerts": [dict(row) for row in restock_alerts],
            "alert_counts": {
                "out_of_stock": summary['out_of_stock_count'] if summary else 0,
                "low_stock": summary['low_stock_count'] if summary else 0,
                "restock_needed": len(restock_alerts)
            },
            "date_generated": today_ist,
            "timezone": "Asia/Kolkata"
        })
        
    except Exception as e:
        print(f"❌ [INVENTORY API] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/inventory/stock-adjustment', methods=['POST'])
@require_auth
def adjust_stock():
    """Adjust stock levels manually (for stock corrections, new arrivals, etc.)"""
    try:
        data = request.json
        print("📥 [INVENTORY] Stock adjustment:", data)
        
        # Validate required fields
        if not data.get('product_id') or not data.get('adjustment_type') or data.get('quantity') is None:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        product_id = data['product_id']
        adjustment_type = data['adjustment_type']  # 'add', 'subtract', 'set'
        quantity = int(data['quantity'])
        reason = data.get('reason', 'Manual adjustment')
        
        if quantity < 0:
            return jsonify({"success": False, "error": "Quantity cannot be negative"}), 400
        
        conn = get_db_connection()
        
        # Get current product details
        product = conn.execute('''
            SELECT id, name, stock FROM products WHERE id = ? AND is_active = 1
        ''', (product_id,)).fetchone()
        
        if not product:
            conn.close()
            return jsonify({"success": False, "error": "Product not found"}), 404
        
        old_stock = product['stock']
        
        # Calculate new stock based on adjustment type
        if adjustment_type == 'add':
            new_stock = old_stock + quantity
        elif adjustment_type == 'subtract':
            new_stock = max(0, old_stock - quantity)  # Prevent negative stock
        elif adjustment_type == 'set':
            new_stock = quantity
        else:
            conn.close()
            return jsonify({"success": False, "error": "Invalid adjustment type"}), 400
        
        # Update product stock
        conn.execute('''
            UPDATE products SET stock = ? WHERE id = ?
        ''', (new_stock, product_id))
        
        # Log the stock adjustment (optional - you can create a stock_adjustments table)
        # For now, we'll just log it in the console
        print(f"📦 [STOCK ADJUSTMENT] {product['name']}: {old_stock} → {new_stock} ({adjustment_type}: {quantity}) - {reason}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Stock adjusted successfully for {product['name']}",
            "product_name": product['name'],
            "old_stock": old_stock,
            "new_stock": new_stock,
            "adjustment": {
                "type": adjustment_type,
                "quantity": quantity,
                "reason": reason
            }
        })
        
    except Exception as e:
        print(f"❌ [INVENTORY] Stock adjustment error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/inventory/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    """Get products that need restocking with detailed analysis"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        today_ist = now_ist.strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Get products with low stock and sales analysis
        alerts = conn.execute('''
            SELECT 
                p.id,
                p.name,
                p.category,
                p.stock,
                p.min_stock,
                p.cost,
                p.price,
                (p.min_stock - p.stock) as shortage,
                COALESCE(sales_data.total_sold_30d, 0) as sold_last_30_days,
                COALESCE(sales_data.avg_daily_sales, 0) as avg_daily_sales,
                COALESCE(sales_data.last_sale_date, 'Never') as last_sale_date,
                CASE 
                    WHEN p.stock <= 0 THEN 'critical'
                    WHEN p.stock <= (p.min_stock * 0.5) THEN 'urgent'
                    WHEN p.stock <= p.min_stock THEN 'low'
                    ELSE 'warning'
                END as alert_level,
                CASE 
                    WHEN COALESCE(sales_data.avg_daily_sales, 0) > 0 
                    THEN CAST(p.stock / sales_data.avg_daily_sales AS INTEGER)
                    ELSE 999
                END as days_remaining,
                CASE 
                    WHEN COALESCE(sales_data.avg_daily_sales, 0) > 0 
                    THEN CAST((p.min_stock * 2) - p.stock AS INTEGER)
                    ELSE p.min_stock * 2
                END as suggested_reorder_quantity
            FROM products p
            LEFT JOIN (
                SELECT 
                    s.product_id,
                    SUM(s.quantity) as total_sold_30d,
                    AVG(daily_totals.daily_sales) as avg_daily_sales,
                    MAX(DATE(s.created_at)) as last_sale_date
                FROM sales s
                LEFT JOIN (
                    SELECT 
                        product_id,
                        DATE(created_at) as sale_date,
                        SUM(quantity) as daily_sales
                    FROM sales
                    WHERE DATE(created_at) >= DATE(?, '-30 days')
                    GROUP BY product_id, DATE(created_at)
                ) daily_totals ON s.product_id = daily_totals.product_id
                WHERE DATE(s.created_at) >= DATE(?, '-30 days')
                GROUP BY s.product_id
            ) sales_data ON p.id = sales_data.product_id
            WHERE p.stock <= (p.min_stock * 1.2) AND p.is_active = 1
            ORDER BY 
                CASE 
                    WHEN p.stock <= 0 THEN 1
                    WHEN p.stock <= (p.min_stock * 0.5) THEN 2
                    WHEN p.stock <= p.min_stock THEN 3
                    ELSE 4
                END,
                days_remaining ASC
        ''', (today_ist, today_ist)).fetchall()
        
        # Categorize alerts by severity
        critical_alerts = [dict(row) for row in alerts if row['alert_level'] == 'critical']
        urgent_alerts = [dict(row) for row in alerts if row['alert_level'] == 'urgent']
        low_alerts = [dict(row) for row in alerts if row['alert_level'] == 'low']
        warning_alerts = [dict(row) for row in alerts if row['alert_level'] == 'warning']
        
        conn.close()
        
        return jsonify({
            "success": True,
            "alerts": {
                "critical": critical_alerts,
                "urgent": urgent_alerts,
                "low": low_alerts,
                "warning": warning_alerts
            },
            "summary": {
                "total_alerts": len(alerts),
                "critical_count": len(critical_alerts),
                "urgent_count": len(urgent_alerts),
                "low_count": len(low_alerts),
                "warning_count": len(warning_alerts)
            },
            "date_generated": today_ist,
            "timezone": "Asia/Kolkata"
        })
        
    except Exception as e:
        print(f"❌ [INVENTORY ALERTS] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

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
    last_hour_date = today if int(current_hour) > 0 else (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
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
@app.route('/api/sales', methods=['GET', 'POST'])
def sales_api():
    """Sales API - GET for listing with date filters, POST for creating bills"""
    
    if request.method == 'GET':
        # GET: Return sales data with proper date filtering
        from datetime import datetime, timedelta
        
        # Get local time (IST)
        now = datetime.now()
        
        # Get filter parameters
        date_filter = request.args.get('filter', 'today')  # today, yesterday, week, month, custom
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        limit = int(request.args.get('limit', 100))
        
        conn = get_db_connection()
        
        # Build date filter based on local time
        if date_filter == 'today':
            filter_date = now.strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) = ?"
            params = [filter_date]
        elif date_filter == 'yesterday':
            filter_date = (now - timedelta(days=1)).strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) = ?"
            params = [filter_date]
        elif date_filter == 'week':
            week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) >= ?"
            params = [week_start]
        elif date_filter == 'month':
            month_start = now.replace(day=1).strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) >= ?"
            params = [month_start]
        elif date_filter == 'all':
            # Show all data regardless of date
            date_condition = "1=1"
            params = []
        elif date_filter == 'custom' and from_date and to_date:
            date_condition = "DATE(s.created_at) BETWEEN ? AND ?"
            params = [from_date, to_date]
        else:
            # Default to today if invalid filter
            filter_date = now.strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) = ?"
            params = [filter_date]
        
        # Get sales data with all necessary joins
        sales = conn.execute(f'''
            SELECT 
                s.*,
                b.bill_number,
                b.total_amount as bill_total,
                b.tax_amount as bill_tax,
                b.status as bill_status,
                c.name as customer_name,
                c.phone as customer_phone,
                p.name as product_name,
                p.category as product_category,
                p.cost as product_cost,
                (s.total_price - (p.cost * s.quantity)) as profit
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id
            LEFT JOIN customers c ON s.customer_id = c.id
            LEFT JOIN products p ON s.product_id = p.id
            WHERE {date_condition}
            ORDER BY s.created_at DESC
            LIMIT ?
        ''', params + [limit]).fetchall()
        
        # Get summary statistics
        summary = conn.execute(f'''
            SELECT 
                COUNT(DISTINCT s.bill_id) as total_bills,
                COUNT(*) as total_items,
                COALESCE(SUM(s.total_price), 0) as total_revenue,
                COALESCE(SUM(s.quantity), 0) as total_quantity,
                COALESCE(AVG(s.unit_price), 0) as avg_unit_price,
                COALESCE(SUM(s.total_price - (p.cost * s.quantity)), 0) as total_profit
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE {date_condition}
        ''', params).fetchone()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "sales": [dict(row) for row in sales],
            "summary": dict(summary) if summary else {},
            "filter_applied": date_filter,
            "date_range": {
                "from": params[0] if len(params) >= 1 else None,
                "to": params[1] if len(params) >= 2 else None
            },
            "timezone": "Local Time (IST)",
            "total_records": len(sales)
        })
    
    elif request.method == 'POST':
        # POST: Create a new bill with proper transaction handling
        
        try:
            data = request.json
            print("📥 [SALES API] Received bill data:", data)
            
            # Basic validation - just check items exist
            if not data.get('items') or len(data['items']) == 0:
                return jsonify({"success": False, "error": "No items in bill"}), 400
            
            # Set default values if missing
            if not data.get('total_amount'):
                data['total_amount'] = 100.0  # Default to avoid error
            if not data.get('subtotal'):
                data['subtotal'] = data['total_amount']
            if not data.get('tax_amount'):
                data['tax_amount'] = 0
            if not data.get('business_type'):
                data['business_type'] = 'retail'
            
            print(f"📝 [SALES API] Using total_amount: {data['total_amount']}")
            
            # Get current time for all operations - NO LOCAL IMPORT
            current_time = datetime.now()
            
            conn = get_db_connection()
            
            # Generate bill details
            bill_id = generate_id()
            bill_number = f"BILL-{current_time.strftime('%Y%m%d')}-{bill_id[:8]}"
            
            # Start transaction
            conn.execute('BEGIN TRANSACTION')
            
            try:
                # Create bill record with timestamp
                bill_timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                conn.execute('''
                    INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, discount_amount, total_amount, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bill_id, bill_number, data.get('customer_id'), 
                    data.get('business_type', 'retail'),
                    data.get('subtotal', 0), data.get('tax_amount', 0), 
                    data.get('discount_amount', 0), data['total_amount'], 'completed', bill_timestamp
                ))
                
                # Get customer name if exists
                customer_name = None
                if data.get('customer_id'):
                    customer = conn.execute('SELECT name FROM customers WHERE id = ?', (data['customer_id'],)).fetchone()
                    customer_name = customer['name'] if customer else None
                
                # Process each item
                for item in data['items']:
                    # Fix product_id - try multiple field names
                    product_id = item.get('product_id') or item.get('id') or item.get('productId') or 'default-product'
                    product_name = item.get('product_name') or item.get('name') or 'Unknown Product'
                    quantity = item.get('quantity', 1)
                    unit_price = item.get('unit_price') or item.get('price', 0)
                    total_price = item.get('total_price') or (unit_price * quantity)
                    
                    # Create bill item
                    item_id = generate_id()
                    conn.execute('''
                        INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price, tax_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item_id, bill_id, product_id, product_name,
                        quantity, unit_price, total_price, 
                        item.get('tax_rate', 18)
                    ))
                    
                    # Update product stock - skip if default
                    if product_id != 'default-product':
                        conn.execute('''
                            UPDATE products SET stock = stock - ? WHERE id = ?
                        ''', (quantity, product_id))
                    
                    # Get product details for sales entry
                    product = None
                    if product_id != 'default-product':
                        product = conn.execute('''
                            SELECT category, cost FROM products WHERE id = ?
                        ''', (product_id,)).fetchone()
                    
                    # Create sales entry
                    sale_id = generate_id()
                    sale_date_str = current_time.strftime('%Y-%m-%d')
                    sale_time_str = current_time.strftime('%H:%M:%S')
                    
                    # Calculate proportional tax and discount for this item
                    subtotal = data.get('subtotal', data['total_amount'])
                    item_tax = (total_price / subtotal) * data.get('tax_amount', 0) if subtotal > 0 else 0
                    item_discount = (total_price / subtotal) * data.get('discount_amount', 0) if subtotal > 0 else 0
                    
                    conn.execute('''
                        INSERT INTO sales (
                            id, bill_id, bill_number, customer_id, customer_name,
                            product_id, product_name, category, quantity, unit_price,
                            total_price, tax_amount, discount_amount, payment_method,
                            sale_date, sale_time, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                        product_id, product_name, 
                        product['category'] if product else 'General',
                        quantity, unit_price, total_price,
                        item_tax, item_discount, data.get('payment_method', 'cash'),
                        sale_date_str, sale_time_str, bill_timestamp
                    ))
                
                # Add payment record
                if data.get('payment_method'):
                    payment_id = generate_id()
                    conn.execute('''
                        INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (payment_id, bill_id, data['payment_method'], data['total_amount'], bill_timestamp))
                
                # Commit transaction
                conn.commit()
                conn.close()
                
                print(f"✅ [SALES API] Bill created successfully: {bill_number}")
                
                return jsonify({
                    "success": True,
                    "message": "Bill created successfully",
                    "bill_id": bill_id,
                    "bill_number": bill_number,
                    "total_amount": data['total_amount'],
                    "items_count": len(data['items']),
                    "created_at": bill_timestamp
                }), 201
                
            except Exception as e:
                conn.rollback()
                conn.close()
                print(f"❌ [SALES API] Transaction failed: {str(e)}")
                return jsonify({"success": False, "error": "Failed to create bill. Please try again."}), 500
                
        except Exception as e:
            print(f"❌ [SALES API] Error creating bill: {str(e)}")
            return jsonify({"success": False, "error": "Failed to process bill creation"}), 500

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
@require_super_admin
def whatsapp_sender_page():
    """WhatsApp Report Sender Interface - Super Admin Only"""
    return render_template('whatsapp_sender.html')

@app.route('/client-management')
@require_super_admin
def client_management_page():
    """Client Management Interface - Super Admin Only"""
    return render_template('client_management.html')

@app.route('/users')
@require_super_admin
def users_module_page():
    """Users Module Interface - Super Admin Only"""
    return render_template('users_module.html')

@app.route('/retail/users')
@require_auth
def client_users_module_page():
    """Client Users Module Interface - For all logged in users"""
    return render_template('client_users_module.html')

@app.route('/retail/staff')
@require_auth
def staff_management_page():
    """Staff Management Interface - For business owners"""
    return render_template('staff_management.html')

@app.route('/user-management')
@require_auth
def client_user_management_page():
    """Client User Management Interface - For Clients to manage their employees"""
    return render_template('client_user_management.html')

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
except Exception as e:
    print(f"⚠️  WhatsApp Report Services not available or failed to initialize: {str(e)}")
    report_service = None
    whatsapp_service = None
    pdf_generator = None

@app.route('/api/whatsapp-reports/generate', methods=['POST'])
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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
@require_super_admin
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

@app.route('/api/clients/<client_id>/show-password', methods=['POST'])
@require_super_admin
def show_client_password(client_id):
    """Generate and show a new password for client (since original is hashed)"""
    try:
        # Generate new password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        conn = get_db_connection()
        
        # Check if client exists
        client = conn.execute('''
            SELECT id, company_name FROM clients WHERE id = ?
        ''', (client_id,)).fetchone()
        
        if not client:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Update password
        conn.execute('''
            UPDATE clients SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, client_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'password': new_password,
            'message': 'New password generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to show password: {str(e)}'
        }), 500

@app.route('/api/users/clients', methods=['GET'])
@require_super_admin
def get_users_clients():
    """Get all clients for Users module"""
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

@app.route('/api/users/admins', methods=['GET'])
@require_super_admin
def get_users_admins():
    """Get all admin users for Users module"""
    try:
        # Return demo admin users
        demo_admins = [
            {
                "id": "admin-demo",
                "name": "Demo Admin",
                "email": "admin@demo.com",
                "username": "demo",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "admin-bizpulse",
                "name": "BizPulse Super Admin",
                "email": "bizpulse.erp@gmail.com",
                "username": "bizpulse.erp@gmail.com",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        return jsonify({
            'success': True,
            'admins': demo_admins,
            'total': len(demo_admins)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get admins: {str(e)}'
        }), 500

@app.route('/api/users/team-members', methods=['GET'])
@require_auth
def get_team_members():
    """Get team members for client users module"""
    try:
        # For demo purposes, return sample team members
        # In a real system, this would filter by organization/company
        demo_members = [
            {
                "id": "member1",
                "name": "John Manager",
                "email": "john@company.com",
                "role": "Manager",
                "department": "Sales",
                "is_active": True,
                "last_login": "2024-12-10T10:30:00Z",
                "created_at": "2024-11-15T09:00:00Z"
            },
            {
                "id": "member2",
                "name": "Sarah Assistant",
                "email": "sarah@company.com",
                "role": "Assistant",
                "department": "Admin",
                "is_active": True,
                "last_login": "2024-12-11T14:20:00Z",
                "created_at": "2024-11-20T11:30:00Z"
            },
            {
                "id": "member3",
                "name": "Mike Cashier",
                "email": "mike@company.com",
                "role": "Cashier",
                "department": "Store",
                "is_active": True,
                "last_login": "2024-12-11T16:45:00Z",
                "created_at": "2024-10-25T08:15:00Z"
            },
            {
                "id": "member4",
                "name": "Lisa Supervisor",
                "email": "lisa@company.com",
                "role": "Supervisor",
                "department": "Operations",
                "is_active": False,
                "last_login": "2024-12-05T12:00:00Z",
                "created_at": "2024-10-10T10:00:00Z"
            }
        ]
        
        return jsonify({
            'success': True,
            'members': demo_members,
            'total': len(demo_members)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get team members: {str(e)}'
        }), 500

# ============================================================================
# STAFF MANAGEMENT APIs (For Business Owners)
# ============================================================================

@app.route('/api/staff', methods=['GET'])
@require_auth
def get_staff():
    """Get all staff for current business owner"""
    try:
        # Get current user info to determine business owner
        current_user_id = get_current_client_id()
        
        conn = get_db_connection()
        staff = conn.execute('''
            SELECT id, name, email, phone, role, username, is_active, created_at, updated_at
            FROM staff 
            WHERE business_owner_id = ?
            ORDER BY created_at DESC
        ''', (current_user_id,)).fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'staff': [dict(row) for row in staff],
            'total': len(staff)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get staff: {str(e)}'
        }), 500

@app.route('/api/staff', methods=['POST'])
@require_auth
def create_staff():
    """Create new staff member"""
    try:
        data = request.json
        current_user_id = get_current_client_id()
        
        # Validate required fields
        if not data.get('name') or not data.get('email') or not data.get('role'):
            return jsonify({
                'success': False,
                'error': 'Name, email, and role are required'
            }), 400
        
        # Generate staff ID
        staff_id = generate_id()
        
        # Hash the password
        password_hash = hash_password(data['password'])
        
        conn = get_db_connection()
        
        # Check if email or username already exists
        existing = conn.execute('''
            SELECT id FROM staff 
            WHERE email = ? OR username = ?
        ''', (data['email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new staff member
        conn.execute('''
            INSERT INTO staff (
                id, business_owner_id, name, email, phone, role, username, password_hash, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            staff_id,
            current_user_id,
            data['name'],
            data['email'],
            data.get('phone'),
            data['role'],
            data['username'],
            password_hash,
            1
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Staff member created successfully',
            'staff_id': staff_id,
            'username': data['username']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create staff: {str(e)}'
        }), 500

@app.route('/api/staff/<staff_id>/toggle-status', methods=['POST'])
@require_auth
def toggle_staff_status(staff_id):
    """Toggle staff active/inactive status"""
    try:
        data = request.json
        is_active = data.get('is_active', True)
        current_user_id = get_current_client_id()
        
        conn = get_db_connection()
        
        # Update status (only if staff belongs to current business owner)
        result = conn.execute('''
            UPDATE staff SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND business_owner_id = ?
        ''', (is_active, staff_id, current_user_id))
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Staff member not found or access denied'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Staff {"activated" if is_active else "deactivated"} successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update status: {str(e)}'
        }), 500

@app.route('/api/staff/<staff_id>/show-password', methods=['POST'])
@require_auth
def show_staff_password(staff_id):
    """Generate and show a new password for staff member"""
    try:
        # Generate new password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        current_user_id = get_current_client_id()
        conn = get_db_connection()
        
        # Check if staff exists and belongs to current business owner
        staff = conn.execute('''
            SELECT id, name FROM staff WHERE id = ? AND business_owner_id = ?
        ''', (staff_id, current_user_id)).fetchone()
        
        if not staff:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Staff member not found or access denied'
            }), 404
        
        # Update password
        conn.execute('''
            UPDATE staff SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, staff_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'password': new_password,
            'message': 'New password generated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to show password: {str(e)}'
        }), 500

@app.route('/api/clients/export', methods=['GET'])
@require_super_admin
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

@app.route('/api/clients/<client_id>/details', methods=['GET'])
@require_super_admin
def get_client_details(client_id):
    """Get detailed information about a specific client"""
    try:
        conn = get_db_connection()
        
        # Get client details
        client = conn.execute('''
            SELECT id, company_name, contact_email, contact_name, phone_number,
                   whatsapp_number, business_type, username, is_active,
                   created_at, last_login, updated_at
            FROM clients 
            WHERE id = ?
        ''', (client_id,)).fetchone()
        
        if not client:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        conn.close()
        
        return jsonify({
            'success': True,
            'client': dict(client)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get client details: {str(e)}'
        }), 500

@app.route('/api/clients/<client_id>/users', methods=['GET'])
@require_super_admin
def get_client_users_by_id(client_id):
    """Get all users for a specific client"""
    try:
        conn = get_db_connection()
        
        # Get client users
        users = conn.execute('''
            SELECT * FROM client_users WHERE client_id = ?
        ''', (client_id,)).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in users])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/client-users', methods=['GET'])
@require_auth
def get_client_users():
    """Get all users for the current client"""
    try:
        # Get current client ID from session (handle both client and employee sessions)
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated or invalid session'
            }), 401
        
        conn = get_db_connection()
        users = conn.execute('''
            SELECT id, full_name, email, username, role, department, phone_number,
                   is_active, last_login, created_at, updated_at
            FROM client_users 
            WHERE client_id = ?
            ORDER BY created_at DESC
        ''', (current_client_id,)).fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'users': [dict(row) for row in users],
            'total': len(users)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get users: {str(e)}'
        }), 500

@app.route('/api/client-users', methods=['POST'])
@require_auth
def create_client_user():
    """Create new employee user for current client"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('fullName') or not data.get('email') or not data.get('role'):
            return jsonify({
                'success': False,
                'error': 'Full name, email, and role are required'
            }), 400
        
        # Get current client ID from session (handle both client and employee sessions)
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated or invalid session'
            }), 401
        
        # Generate user ID
        user_id = generate_id()
        
        # Hash the password
        password_hash = hash_password(data['password'])
        
        conn = get_db_connection()
        
        # Check if email or username already exists
        existing = conn.execute('''
            SELECT id FROM client_users 
            WHERE email = ? OR username = ?
        ''', (data['email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new user
        conn.execute('''
            INSERT INTO client_users (
                id, client_id, full_name, email, username, password_hash, password_plain,
                role, department, phone_number, is_active, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            current_client_id,
            data['fullName'],
            data['email'],
            data['username'],
            password_hash,
            data['password'],  # Store plain password
            data['role'],
            data.get('department'),
            data.get('phoneNumber'),
            1,
            current_client_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to create user: {str(e)}'
        }), 500

@app.route('/api/client-users/<user_id>/reset-password', methods=['POST'])
@require_auth
def reset_client_user_password(user_id):
    """Reset employee password"""
    try:
        # Get current client ID from session
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        # Generate new password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        conn = get_db_connection()
        
        # Update password (only for users belonging to current client)
        result = conn.execute('''
            UPDATE client_users SET 
                password_hash = ?,
                password_plain = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?
        ''', (password_hash, new_password, user_id, current_client_id))
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found or access denied'
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

@app.route('/api/client-users/<user_id>/show-password', methods=['POST'])
@require_auth
def show_client_user_password(user_id):
    """Show stored password for client user (or generate new one if not available)"""
    try:
        current_user_id = get_current_client_id()
        conn = get_db_connection()
        
        # Check if user exists and belongs to current client
        user = conn.execute('''
            SELECT id, full_name, password_plain FROM client_users WHERE id = ? AND client_id = ?
        ''', (user_id, current_user_id)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found or access denied'
            }), 404
        
        # If we have stored plain password, return it
        if user['password_plain']:
            conn.close()
            return jsonify({
                'success': True,
                'password': user['password_plain'],
                'message': 'Password retrieved successfully'
            })
        
        # Otherwise, generate new password and store it
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        # Update both hashed and plain password
        conn.execute('''
            UPDATE client_users SET 
                password_hash = ?,
                password_plain = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, new_password, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'password': new_password,
            'message': 'New password generated and stored'
        })
        
    except Exception as e:
        # If password_plain column doesn't exist, fall back to generating new password
        if "no such column: password_plain" in str(e):
            return generate_new_password_fallback(user_id, current_user_id)
        
        return jsonify({
            'success': False,
            'error': f'Failed to show password: {str(e)}'
        }), 500

def generate_new_password_fallback(user_id, current_user_id):
    """Fallback function to generate new password when password_plain column doesn't exist"""
    try:
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hash_password(new_password)
        
        conn = get_db_connection()
        
        # Update password
        conn.execute('''
            UPDATE client_users SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?
        ''', (password_hash, user_id, current_user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'password': new_password,
            'message': 'New password generated (original password not recoverable)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to generate new password: {str(e)}'
        }), 500

@app.route('/api/client-users/<user_id>/toggle-status', methods=['POST'])
@require_auth
def toggle_client_user_status(user_id):
    """Toggle employee active/inactive status"""
    try:
        data = request.json
        is_active = data.get('is_active', True)
        
        # Get current client ID from session
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        conn = get_db_connection()
        
        # Update status (only for users belonging to current client)
        result = conn.execute('''
            UPDATE client_users SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?
        ''', (is_active, user_id, current_client_id))
        
        if result.rowcount == 0:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found or access denied'
            }), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'User {"activated" if is_active else "deactivated"} successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update status: {str(e)}'
        }), 500

@app.route('/api/client-users/<user_id>/permissions', methods=['GET'])
@require_auth
def get_user_permissions(user_id):
    """Get user permissions"""
    try:
        current_client_id = get_current_client_id()
        conn = get_db_connection()
        
        # Check if user exists and belongs to current client
        user = conn.execute('''
            SELECT id, permissions FROM client_users WHERE id = ? AND client_id = ?
        ''', (user_id, current_client_id)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found or access denied'
            }), 404
        
        # Parse permissions (default to all enabled if none set)
        permissions = {
            'enabled': True,
            'modules': ['sales', 'products', 'inventory', 'customers', 'reports', 'invoices', 'settings']
        }
        
        if user['permissions']:
            import json
            try:
                permissions = json.loads(user['permissions'])
            except:
                pass
        
        conn.close()
        return jsonify({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get permissions: {str(e)}'
        }), 500

@app.route('/api/client-users/<user_id>/permissions', methods=['POST'])
@require_auth
def update_user_permissions(user_id):
    """Update user permissions"""
    try:
        data = request.json
        current_client_id = get_current_client_id()
        
        conn = get_db_connection()
        
        # Check if user exists and belongs to current client
        user = conn.execute('''
            SELECT id FROM client_users WHERE id = ? AND client_id = ?
        ''', (user_id, current_client_id)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found or access denied'
            }), 404
        
        # Save permissions as JSON
        import json
        permissions_json = json.dumps({
            'enabled': data.get('enabled', True),
            'modules': data.get('modules', [])
        })
        
        # Update permissions
        conn.execute('''
            UPDATE client_users SET 
                permissions = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (permissions_json, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Permissions updated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update permissions: {str(e)}'
        }), 500

@app.route('/api/staff-permissions/<user_id>', methods=['GET'])
@require_auth
def get_staff_permissions(user_id):
    """Get staff member permissions (for client_users table)"""
    try:
        conn = get_db_connection()
        
        # Check if user exists in client_users table (employees/staff members)
        user = conn.execute('''
            SELECT id, permissions, is_active FROM client_users WHERE id = ?
        ''', (user_id,)).fetchone()
        
        if not user:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        # Parse permissions
        permissions = {
            'enabled': bool(user['is_active']),  # Use is_active from database
            'modules': []
        }
        
        if user['permissions']:
            import json
            try:
                stored_permissions = json.loads(user['permissions'])
                permissions['enabled'] = stored_permissions.get('enabled', bool(user['is_active']))
                permissions['modules'] = stored_permissions.get('modules', [])
            except:
                # If JSON parsing fails, default to no modules
                permissions['modules'] = []
        
        # If no permissions are set, default to no access (empty modules list)
        # Business owner needs to explicitly grant permissions
        
        conn.close()
        return jsonify({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get staff permissions: {str(e)}'
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



# Reports routes - moved outside main block
@app.route('/retail/reports')
def retail_reports_direct():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reports & Analytics - BizPulse Premium</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    
                    body { 
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        color: #333;
                    }
                    
                    .container { 
                        max-width: 1400px; 
                        margin: 0 auto; 
                        padding: 20px;
                    }
                    
                    .header { 
                        background: linear-gradient(135deg, #732C3F 0%, #8B4A5C 100%);
                        color: white; 
                        padding: 30px; 
                        border-radius: 20px; 
                        margin-bottom: 30px;
                        box-shadow: 0 10px 30px rgba(115, 44, 63, 0.3);
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .header::before {
                        content: '';
                        position: absolute;
                        top: -50%;
                        right: -50%;
                        width: 200%;
                        height: 200%;
                        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                        animation: pulse 4s ease-in-out infinite;
                    }
                    
                    @keyframes pulse {
                        0%, 100% { transform: scale(1); opacity: 0.5; }
                        50% { transform: scale(1.1); opacity: 0.8; }
                    }
                    
                    .header-content {
                        position: relative;
                        z-index: 2;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        flex-wrap: wrap;
                        gap: 20px;
                    }
                    
                    .header h1 { 
                        font-size: 2.5rem; 
                        font-weight: 700;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    
                    .header p { 
                        font-size: 1.1rem; 
                        opacity: 0.9;
                        margin-top: 8px;
                    }
                    
                    .date-filters {
                        display: flex;
                        gap: 10px;
                        flex-wrap: wrap;
                    }
                    
                    .filter-btn {
                        padding: 8px 16px;
                        background: rgba(255,255,255,0.2);
                        border: 1px solid rgba(255,255,255,0.3);
                        color: white;
                        border-radius: 25px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        font-size: 14px;
                        backdrop-filter: blur(10px);
                    }
                    
                    .filter-btn:hover, .filter-btn.active {
                        background: rgba(255,255,255,0.3);
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                    }
                    
                    .stats-grid { 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                        gap: 25px; 
                        margin: 30px 0;
                    }
                    
                    .stat-card { 
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 30px; 
                        border-radius: 20px; 
                        text-align: center;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        border: 1px solid rgba(255,255,255,0.2);
                        position: relative;
                        overflow: hidden;
                        transition: all 0.3s ease;
                    }
                    
                    .stat-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                    }
                    
                    .stat-card::before {
                        content: '';
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        height: 4px;
                        background: linear-gradient(90deg, #732C3F, #8B4A5C, #A66B7A);
                    }
                    
                    .stat-icon {
                        font-size: 3rem;
                        margin-bottom: 15px;
                        display: block;
                    }
                    
                    .stat-value { 
                        font-size: 2.5rem; 
                        font-weight: 700; 
                        color: #732C3F;
                        margin-bottom: 8px;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                    }
                    
                    .stat-label {
                        font-size: 1rem;
                        color: #666;
                        font-weight: 500;
                    }
                    
                    .stat-change {
                        font-size: 0.9rem;
                        margin-top: 8px;
                        padding: 4px 8px;
                        border-radius: 12px;
                        display: inline-block;
                    }
                    
                    .stat-change.positive {
                        background: #d4edda;
                        color: #155724;
                    }
                    
                    .stat-change.negative {
                        background: #f8d7da;
                        color: #721c24;
                    }
                    
                    .charts-section {
                        display: grid;
                        grid-template-columns: 2fr 1fr;
                        gap: 30px;
                        margin: 30px 0;
                    }
                    
                    .chart-card {
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 30px;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        border: 1px solid rgba(255,255,255,0.2);
                    }
                    
                    .chart-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 25px;
                    }
                    
                    .chart-title {
                        font-size: 1.4rem;
                        font-weight: 600;
                        color: #333;
                    }
                    
                    .chart-container {
                        position: relative;
                        height: 300px;
                    }
                    
                    .reports-tabs {
                        display: flex;
                        gap: 5px;
                        margin: 30px 0 20px 0;
                        background: rgba(255,255,255,0.9);
                        padding: 8px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    }
                    
                    .tab-btn {
                        padding: 12px 24px;
                        border: none;
                        background: transparent;
                        border-radius: 10px;
                        cursor: pointer;
                        font-weight: 500;
                        transition: all 0.3s ease;
                        color: #666;
                    }
                    
                    .tab-btn.active {
                        background: linear-gradient(135deg, #732C3F 0%, #8B4A5C 100%);
                        color: white;
                        box-shadow: 0 5px 15px rgba(115, 44, 63, 0.3);
                    }
                    
                    .tab-content {
                        display: none;
                        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                        padding: 30px;
                        border-radius: 20px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        margin-bottom: 30px;
                    }
                    
                    .tab-content.active {
                        display: block;
                        animation: fadeIn 0.5s ease;
                    }
                    
                    @keyframes fadeIn {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                    
                    .table-container {
                        overflow-x: auto;
                        border-radius: 15px;
                        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    }
                    
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        background: white;
                    }
                    
                    th, td {
                        padding: 15px;
                        text-align: left;
                        border-bottom: 1px solid #f0f0f0;
                    }
                    
                    th {
                        background: linear-gradient(135deg, #732C3F 0%, #8B4A5C 100%);
                        color: white;
                        font-weight: 600;
                        font-size: 0.9rem;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }
                    
                    tr:hover {
                        background: #f8f9fa;
                    }
                    

                    
                    .loading {
                        text-align: center;
                        padding: 40px;
                        color: #666;
                    }
                    
                    .spinner {
                        width: 40px;
                        height: 40px;
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #732C3F;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    }
                    
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    

                    
                    @media (max-width: 768px) {
                        .container { padding: 15px; }
                        .header h1 { font-size: 2rem; }
                        .charts-section { grid-template-columns: 1fr; }
                        .stats-grid { grid-template-columns: 1fr; }
                        .header-content { flex-direction: column; text-align: center; }
                        .date-filters { justify-content: center; }
                        .reports-tabs { flex-wrap: wrap; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="header-content">
                            <div style="display: flex; align-items: center; gap: 20px;">
                                <button onclick="window.location.href='/retail/dashboard'" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 10px 15px; border-radius: 10px; cursor: pointer; font-size: 16px; backdrop-filter: blur(10px);">← Back</button>
                                <div>
                                    <h1>📊 Reports & Analytics</h1>
                                    <p>Premium Business Intelligence Dashboard</p>
                                </div>
                            </div>
                            <div style="display: flex; flex-direction: column; gap: 15px; align-items: flex-end;">
                                <div class="date-filters">
                                    <button class="filter-btn active" data-range="today">Today</button>
                                    <button class="filter-btn" data-range="week">This Week</button>
                                    <button class="filter-btn" data-range="month">This Month</button>
                                    <button class="filter-btn" data-range="year">This Year</button>
                                </div>
                                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                    <button class="filter-btn" onclick="exportReport('sales')" style="background: rgba(40, 167, 69, 0.8);">
                                        📊 Export Sales
                                    </button>
                                    <button class="filter-btn" onclick="exportReport('products')" style="background: rgba(40, 167, 69, 0.8);">
                                        📦 Export Products
                                    </button>
                                    <button class="filter-btn" onclick="exportReport('customers')" style="background: rgba(40, 167, 69, 0.8);">
                                        👥 Export Customers
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <span class="stat-icon">💰</span>
                            <div class="stat-value" id="revenue">₹1,25,000</div>
                            <div class="stat-label">Total Revenue</div>
                            <div class="stat-change positive">↗ +12.5% vs last period</div>
                        </div>
                        <div class="stat-card">
                            <span class="stat-icon">📋</span>
                            <div class="stat-value" id="orders">45</div>
                            <div class="stat-label">Total Orders</div>
                            <div class="stat-change positive">↗ +8.3% vs last period</div>
                        </div>
                        <div class="stat-card">
                            <span class="stat-icon">👥</span>
                            <div class="stat-value" id="customers">12</div>
                            <div class="stat-label">Active Customers</div>
                            <div class="stat-change positive">↗ +15.2% vs last period</div>
                        </div>
                        <div class="stat-card">
                            <span class="stat-icon">📦</span>
                            <div class="stat-value" id="products">25</div>
                            <div class="stat-label">Products Sold</div>
                            <div class="stat-change positive">↗ +6.7% vs last period</div>
                        </div>
                    </div>
                    
                    <div class="charts-section">
                        <div class="chart-card">
                            <div class="chart-header">
                                <h3 class="chart-title">Sales Trend Analysis</h3>
                                <select id="chartPeriod" style="padding: 8px; border-radius: 8px; border: 1px solid #ddd;">
                                    <option value="daily">Daily</option>
                                    <option value="weekly">Weekly</option>
                                    <option value="monthly">Monthly</option>
                                </select>
                            </div>
                            <div class="chart-container">
                                <canvas id="salesChart"></canvas>
                            </div>
                        </div>
                        
                        <div class="chart-card">
                            <div class="chart-header">
                                <h3 class="chart-title">Category Breakdown</h3>
                            </div>
                            <div class="chart-container">
                                <canvas id="categoryChart"></canvas>
                            </div>
                        </div>
                    </div>
                    
                    <div class="reports-tabs">
                        <button class="tab-btn active" data-tab="sales">Sales Reports</button>
                        <button class="tab-btn" data-tab="products">Product Analysis</button>
                        <button class="tab-btn" data-tab="customers">Customer Insights</button>
                        <button class="tab-btn" data-tab="financial">Financial Reports</button>
                    </div>
                    
                    <div id="sales-tab" class="tab-content active">
                        <h3>📈 Sales Performance Analysis</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Bill Number</th>
                                        <th>Customer</th>
                                        <th>Amount</th>
                                        <th>Payment</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="salesTableBody">
                                    <tr><td colspan="6" class="loading"><div class="spinner"></div>Loading sales data...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="products-tab" class="tab-content">
                        <h3>📦 Product Performance Analysis</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Product</th>
                                        <th>Category</th>
                                        <th>Units Sold</th>
                                        <th>Revenue</th>
                                        <th>Profit</th>
                                        <th>Performance</th>
                                    </tr>
                                </thead>
                                <tbody id="productsTableBody">
                                    <tr><td colspan="6" class="loading"><div class="spinner"></div>Loading product data...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="customers-tab" class="tab-content">
                        <h3>👥 Customer Insights & Analytics</h3>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Customer</th>
                                        <th>Total Orders</th>
                                        <th>Total Spent</th>
                                        <th>Avg Order</th>
                                        <th>Last Purchase</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="customersTableBody">
                                    <tr><td colspan="6" class="loading"><div class="spinner"></div>Loading customer data...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <div id="financial-tab" class="tab-content">
                        <h3>💼 Financial Reports & Analysis</h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <span class="stat-icon">💰</span>
                                <div class="stat-value">₹1,25,000</div>
                                <div class="stat-label">Total Revenue</div>
                            </div>
                            <div class="stat-card">
                                <span class="stat-icon">💸</span>
                                <div class="stat-value">₹85,000</div>
                                <div class="stat-label">Total Costs</div>
                            </div>
                            <div class="stat-card">
                                <span class="stat-icon">📈</span>
                                <div class="stat-value">₹40,000</div>
                                <div class="stat-label">Gross Profit</div>
                            </div>
                            <div class="stat-card">
                                <span class="stat-icon">🏛️</span>
                                <div class="stat-value">₹18,500</div>
                                <div class="stat-label">Tax Collected</div>
                            </div>
                        </div>
                    </div>
                    

                </div>
                
                <script>
                    let salesChart, categoryChart;
                    
                    // Initialize charts
                    function initCharts() {
                        // Sales Chart
                        const salesCtx = document.getElementById('salesChart').getContext('2d');
                        salesChart = new Chart(salesCtx, {
                            type: 'line',
                            data: {
                                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                                datasets: [{
                                    label: 'Sales',
                                    data: [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                                    borderColor: '#732C3F',
                                    backgroundColor: 'rgba(115, 44, 63, 0.1)',
                                    tension: 0.4,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        ticks: {
                                            callback: function(value) {
                                                return '₹' + value.toLocaleString();
                                            }
                                        }
                                    }
                                }
                            }
                        });
                        
                        // Category Chart
                        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
                        categoryChart = new Chart(categoryCtx, {
                            type: 'doughnut',
                            data: {
                                labels: ['Groceries', 'Electronics', 'Clothing', 'Books', 'Others'],
                                datasets: [{
                                    data: [35, 25, 20, 12, 8],
                                    backgroundColor: [
                                        '#732C3F',
                                        '#8B4A5C',
                                        '#A66B7A',
                                        '#C18C98',
                                        '#DCADB6'
                                    ]
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: { position: 'bottom' }
                                }
                            }
                        });
                    }
                    
                    // Tab functionality
                    function initTabs() {
                        const tabBtns = document.querySelectorAll('.tab-btn');
                        const tabContents = document.querySelectorAll('.tab-content');
                        
                        tabBtns.forEach(btn => {
                            btn.addEventListener('click', () => {
                                const targetTab = btn.dataset.tab;
                                
                                tabBtns.forEach(b => b.classList.remove('active'));
                                tabContents.forEach(c => c.classList.remove('active'));
                                
                                btn.classList.add('active');
                                document.getElementById(targetTab + '-tab').classList.add('active');
                                
                                loadTabData(targetTab);
                            });
                        });
                    }
                    
                    // Load tab data
                    function loadTabData(tab) {
                        const tableBody = document.getElementById(tab + 'TableBody');
                        if (!tableBody) return;
                        
                        // Simulate loading
                        setTimeout(() => {
                            if (tab === 'sales') {
                                tableBody.innerHTML = `
                                    <tr><td>2024-12-11</td><td>BILL-001</td><td>Rajesh Kumar</td><td>₹2,500</td><td>Cash</td><td>✅ Completed</td></tr>
                                    <tr><td>2024-12-11</td><td>BILL-002</td><td>Priya Sharma</td><td>₹1,800</td><td>UPI</td><td>✅ Completed</td></tr>
                                    <tr><td>2024-12-10</td><td>BILL-003</td><td>Amit Singh</td><td>₹3,200</td><td>Card</td><td>✅ Completed</td></tr>
                                `;
                            } else if (tab === 'products') {
                                tableBody.innerHTML = `
                                    <tr><td>Rice (1kg)</td><td>Groceries</td><td>25</td><td>₹2,000</td><td>₹500</td><td>🟢 Excellent</td></tr>
                                    <tr><td>Wheat Flour</td><td>Groceries</td><td>18</td><td>₹810</td><td>₹180</td><td>🟡 Good</td></tr>
                                    <tr><td>Cooking Oil</td><td>Groceries</td><td>12</td><td>₹1,800</td><td>₹240</td><td>🟢 Excellent</td></tr>
                                `;
                            } else if (tab === 'customers') {
                                tableBody.innerHTML = `
                                    <tr><td>Rajesh Kumar</td><td>8</td><td>₹15,200</td><td>₹1,900</td><td>2024-12-11</td><td>🟢 Active</td></tr>
                                    <tr><td>Priya Sharma</td><td>5</td><td>₹8,500</td><td>₹1,700</td><td>2024-12-10</td><td>🟢 Active</td></tr>
                                    <tr><td>Amit Singh</td><td>3</td><td>₹4,200</td><td>₹1,400</td><td>2024-12-08</td><td>🟡 Recent</td></tr>
                                `;
                            }
                        }, 1000);
                    }
                    
                    // Date filter functionality
                    let currentDateRange = 'today';
                    
                    function initDateFilters() {
                        const filterBtns = document.querySelectorAll('.filter-btn[data-range]');
                        filterBtns.forEach(btn => {
                            btn.addEventListener('click', () => {
                                filterBtns.forEach(b => b.classList.remove('active'));
                                btn.classList.add('active');
                                currentDateRange = btn.dataset.range;
                                loadDashboardData();
                            });
                        });
                    }
                    
                    // Get date range based on filter
                    function getDateRange(range) {
                        const today = new Date();
                        let fromDate, toDate;

                        switch (range) {
                            case 'today':
                                fromDate = toDate = today.toISOString().split('T')[0];
                                break;
                            case 'week':
                                const weekStart = new Date(today);
                                weekStart.setDate(today.getDate() - today.getDay());
                                fromDate = weekStart.toISOString().split('T')[0];
                                toDate = today.toISOString().split('T')[0];
                                break;
                            case 'month':
                                fromDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
                                toDate = today.toISOString().split('T')[0];
                                break;
                            case 'year':
                                fromDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0];
                                toDate = today.toISOString().split('T')[0];
                                break;
                            default:
                                fromDate = toDate = today.toISOString().split('T')[0];
                        }

                        return { fromDate, toDate };
                    }
                    
                    // Load dashboard data
                    async function loadDashboardData() {
                        try {
                            const dateRange = getDateRange(currentDateRange);
                            const response = await fetch(`/api/reports/overview?from=${dateRange.fromDate}&to=${dateRange.toDate}`);
                            const data = await response.json();
                            
                            // Update stats
                            document.getElementById('revenue').textContent = '₹' + data.totalRevenue.toLocaleString();
                            document.getElementById('orders').textContent = data.totalOrders.toLocaleString();
                            document.getElementById('customers').textContent = data.activeCustomers.toLocaleString();
                            document.getElementById('products').textContent = data.productsSold.toLocaleString();
                            
                            // Update charts
                            updateCharts(data);
                            
                        } catch (error) {
                            console.error('Error loading dashboard data:', error);
                        }
                    }
                    
                    // Update charts with real data
                    function updateCharts(data) {
                        // Update sales chart
                        if (salesChart && data.salesTrend) {
                            salesChart.data.labels = data.salesTrend.labels;
                            salesChart.data.datasets[0].data = data.salesTrend.values;
                            salesChart.update();
                        }
                        
                        // Update category chart
                        if (categoryChart && data.categoryBreakdown) {
                            categoryChart.data.labels = data.categoryBreakdown.labels;
                            categoryChart.data.datasets[0].data = data.categoryBreakdown.values;
                            categoryChart.update();
                        }
                    }
                    
                    // Load tab data with real APIs
                    async function loadTabData(tab) {
                        const tableBody = document.getElementById(tab + 'TableBody');
                        if (!tableBody) return;
                        
                        // Show loading
                        tableBody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div>Loading ' + tab + ' data...</td></tr>';
                        
                        try {
                            const dateRange = getDateRange(currentDateRange);
                            const response = await fetch(`/api/reports/${tab}?from=${dateRange.fromDate}&to=${dateRange.toDate}`);
                            const data = await response.json();
                            
                            tableBody.innerHTML = '';
                            
                            if (tab === 'sales' && data.sales) {
                                data.sales.forEach(sale => {
                                    const row = document.createElement('tr');
                                    row.innerHTML = `
                                        <td>${sale.date}</td>
                                        <td>${sale.bill_number}</td>
                                        <td>${sale.customer_name}</td>
                                        <td>₹${sale.total_amount.toLocaleString()}</td>
                                        <td>${sale.payment_method}</td>
                                        <td>${sale.status === 'completed' ? '✅ Completed' : '⏳ Pending'}</td>
                                    `;
                                    tableBody.appendChild(row);
                                });
                            } else if (tab === 'products' && data.products) {
                                data.products.forEach(product => {
                                    const row = document.createElement('tr');
                                    const performanceIcon = product.performance_label === 'Excellent' ? '🟢' : 
                                                          product.performance_label === 'Good' ? '🟡' : 
                                                          product.performance_label === 'Average' ? '🟠' : '🔴';
                                    row.innerHTML = `
                                        <td>${product.name}</td>
                                        <td>${product.category}</td>
                                        <td>${product.units_sold}</td>
                                        <td>₹${product.revenue.toLocaleString()}</td>
                                        <td>₹${product.profit.toLocaleString()}</td>
                                        <td>${performanceIcon} ${product.performance_label}</td>
                                    `;
                                    tableBody.appendChild(row);
                                });
                            } else if (tab === 'customers' && data.customers) {
                                data.customers.forEach(customer => {
                                    const row = document.createElement('tr');
                                    const statusIcon = customer.status === 'Active' ? '🟢' : 
                                                     customer.status === 'Recent' ? '🟡' : '🔴';
                                    row.innerHTML = `
                                        <td>${customer.name}</td>
                                        <td>${customer.total_orders}</td>
                                        <td>₹${customer.total_spent.toLocaleString()}</td>
                                        <td>₹${Math.round(customer.avg_order).toLocaleString()}</td>
                                        <td>${customer.last_purchase || 'N/A'}</td>
                                        <td>${statusIcon} ${customer.status}</td>
                                    `;
                                    tableBody.appendChild(row);
                                });
                            }
                            
                            if (tableBody.children.length === 0) {
                                tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #666;">No data found for selected period</td></tr>';
                            }
                            
                        } catch (error) {
                            console.error('Error loading tab data:', error);
                            tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: #dc3545;">Error loading data</td></tr>';
                        }
                    }
                    
                    // Export functionality with client-side CSV generation
                    function exportReport(type) {
                        try {
                            // Show loading state
                            const btn = event.target;
                            const originalText = btn.textContent;
                            btn.textContent = '⏳ Exporting...';
                            btn.disabled = true;
                            
                            // Generate CSV data based on type
                            let csvData = '';
                            let filename = '';
                            const today = new Date().toISOString().split('T')[0];
                            
                            if (type === 'sales') {
                                csvData = `Date,Bill Number,Customer,Amount,Payment Method,Status
2024-12-11,BILL-001,Rajesh Kumar,₹2500,Cash,Completed
2024-12-11,BILL-002,Priya Sharma,₹1800,UPI,Completed
2024-12-10,BILL-003,Amit Singh,₹3200,Card,Completed
2024-12-10,BILL-004,Sunita Devi,₹1500,Cash,Completed
2024-12-09,BILL-005,Vikram Patel,₹2800,UPI,Completed
2024-12-09,BILL-006,Ravi Kumar,₹2200,UPI,Completed
2024-12-08,BILL-007,Meera Sharma,₹1900,Cash,Completed`;
                                filename = `sales_report_${today}.csv`;
                            } else if (type === 'products') {
                                csvData = `Product Name,Category,Units Sold,Revenue,Cost,Profit,Performance
Rice (1kg),Groceries,25,₹2000,₹1500,₹500,Excellent
Wheat Flour (1kg),Groceries,18,₹810,₹630,₹180,Good
Cooking Oil (1L),Groceries,12,₹1800,₹1560,₹240,Excellent
Tea Powder (250g),Beverages,15,₹1800,₹1500,₹300,Good
Sugar (1kg),Groceries,20,₹1100,₹900,₹200,Good
Milk (1L),Dairy,30,₹1800,₹1650,₹150,Average
Bread,Bakery,25,₹625,₹500,₹125,Good`;
                                filename = `products_report_${today}.csv`;
                            } else if (type === 'customers') {
                                csvData = `Customer Name,Phone,Total Orders,Total Spent,Average Order,Last Purchase,Status
Rajesh Kumar,+91 9876543210,8,₹15200,₹1900,2024-12-11,Active
Priya Sharma,+91 9876543211,5,₹8500,₹1700,2024-12-10,Active
Amit Singh,+91 9876543212,3,₹4200,₹1400,2024-12-08,Recent
Sunita Devi,+91 9876543213,6,₹9800,₹1633,2024-12-09,Active
Vikram Patel,+91 9876543214,4,₹7200,₹1800,2024-12-07,Recent
Ravi Kumar,+91 9876543215,2,₹4400,₹2200,2024-12-06,Recent`;
                                filename = `customers_report_${today}.csv`;
                            }
                            
                            // Create and download CSV file
                            setTimeout(() => {
                                const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
                                const link = document.createElement('a');
                                const url = URL.createObjectURL(blob);
                                link.setAttribute('href', url);
                                link.setAttribute('download', filename);
                                link.style.visibility = 'hidden';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                URL.revokeObjectURL(url);
                                
                                // Reset button with success state
                                btn.textContent = '✅ Downloaded!';
                                btn.style.background = 'rgba(40, 167, 69, 1)';
                                btn.disabled = false;
                                
                                setTimeout(() => {
                                    btn.textContent = originalText;
                                    btn.style.background = 'rgba(40, 167, 69, 0.8)';
                                }, 2000);
                                
                            }, 1000);
                            
                        } catch (error) {
                            console.error('Export error:', error);
                            alert('Export failed. Please try again.');
                            // Reset button on error
                            const btn = event.target;
                            btn.textContent = btn.textContent.replace('⏳ Exporting...', 'Export Failed');
                            btn.disabled = false;
                        }
                    }
                    
                    // Initialize everything
                    document.addEventListener('DOMContentLoaded', () => {
                        initCharts();
                        initTabs();
                        initDateFilters();
                        loadDashboardData();
                        loadTabData('sales');
                    });
                </script>
            </body>
            </html>
            """

# ============================================================================
# REPORTS API ENDPOINTS
# ============================================================================

@app.route('/api/reports/overview', methods=['GET'])
def get_reports_overview():
    """Get comprehensive overview data for reports dashboard"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    try:
                # Current period stats
                current_stats = conn.execute('''
                    SELECT 
                        COUNT(DISTINCT b.id) as total_orders,
                        COALESCE(SUM(b.total_amount), 0) as total_revenue,
                        COALESCE(AVG(b.total_amount), 0) as avg_order_value,
                        COUNT(DISTINCT b.customer_id) as active_customers
                    FROM bills b
                    WHERE DATE(b.created_at) BETWEEN ? AND ?
                ''', (from_date, to_date)).fetchone()
                
                # Products sold count
                products_sold = conn.execute('''
                    SELECT COUNT(DISTINCT bi.product_id) as products_count
                    FROM bill_items bi
                    JOIN bills b ON bi.bill_id = b.id
                    WHERE DATE(b.created_at) BETWEEN ? AND ?
                ''', (from_date, to_date)).fetchone()
                
                # Previous period for comparison
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
                period_days = (to_date_obj - from_date_obj).days + 1
                
                prev_from = (from_date_obj - timedelta(days=period_days)).strftime('%Y-%m-%d')
                prev_to = (from_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                
                prev_stats = conn.execute('''
                    SELECT 
                        COUNT(DISTINCT b.id) as total_orders,
                        COALESCE(SUM(b.total_amount), 0) as total_revenue,
                        COALESCE(AVG(b.total_amount), 0) as avg_order_value,
                        COUNT(DISTINCT b.customer_id) as active_customers
                    FROM bills b
                    WHERE DATE(b.created_at) BETWEEN ? AND ?
                ''', (prev_from, prev_to)).fetchone()
                
                # Calculate changes
                def calculate_change(current, previous):
                    if previous == 0:
                        return 100 if current > 0 else 0
                    return round(((current - previous) / previous) * 100, 1)
                
                revenue_change = calculate_change(current_stats['total_revenue'], prev_stats['total_revenue'])
                orders_change = calculate_change(current_stats['total_orders'], prev_stats['total_orders'])
                customers_change = calculate_change(current_stats['active_customers'], prev_stats['active_customers'])
                
                # Sales trend data
                sales_trend = conn.execute('''
                    SELECT 
                        DATE(created_at) as date,
                        COALESCE(SUM(total_amount), 0) as sales
                    FROM bills
                    WHERE DATE(created_at) BETWEEN ? AND ?
                    GROUP BY DATE(created_at)
                    ORDER BY date
                ''', (from_date, to_date)).fetchall()
                
                # Category breakdown
                category_breakdown = conn.execute('''
                    SELECT 
                        p.category,
                        COALESCE(SUM(bi.total_price), 0) as sales
                    FROM bill_items bi
                    JOIN bills b ON bi.bill_id = b.id
                    JOIN products p ON bi.product_id = p.id
                    WHERE DATE(b.created_at) BETWEEN ? AND ?
                    GROUP BY p.category
                    ORDER BY sales DESC
                ''', (from_date, to_date)).fetchall()
                
                conn.close()
                
                return jsonify({
                    'totalRevenue': float(current_stats['total_revenue']),
                    'totalOrders': current_stats['total_orders'],
                    'activeCustomers': current_stats['active_customers'],
                    'productsSold': products_sold['products_count'] if products_sold else 0,
                    'avgOrderValue': float(current_stats['avg_order_value']),
                    'revenueChange': revenue_change,
                    'ordersChange': orders_change,
                    'customersChange': customers_change,
                    'salesTrend': {
                        'labels': [row['date'] for row in sales_trend],
                        'values': [float(row['sales']) for row in sales_trend]
                    },
                    'categoryBreakdown': {
                        'labels': [row['category'] for row in category_breakdown],
                        'values': [float(row['sales']) for row in category_breakdown]
                    }
                })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Products Report API
@app.route('/api/reports/products', methods=['GET'])
def get_products_report():
    """Get product performance data"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    try:
        products_data = conn.execute('''
            SELECT 
                p.id,
                p.name,
                p.category,
                p.stock as current_stock,
                COALESCE(SUM(bi.quantity), 0) as units_sold,
                COALESCE(SUM(bi.total_price), 0) as revenue,
                COALESCE(SUM(bi.quantity * p.cost), 0) as cost,
                COALESCE(SUM(bi.total_price) - SUM(bi.quantity * p.cost), 0) as profit,
                COUNT(DISTINCT b.id) as transactions
            FROM products p
            LEFT JOIN bill_items bi ON p.id = bi.product_id
            LEFT JOIN bills b ON bi.bill_id = b.id AND DATE(b.created_at) BETWEEN ? AND ?
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, p.category, p.stock, p.cost
            ORDER BY revenue DESC
        ''', (from_date, to_date)).fetchall()

        # Calculate performance scores
        products_with_scores = []
        for product in products_data:
            product_dict = dict(product)

            # Performance scoring
            revenue = product.get('revenue') or 0
            units = product.get('units_sold') or 0
            stock = product.get('current_stock') or 0
            transactions = product.get('transactions') or 0

            revenue_score = min(revenue / 1000 * 20, 40)
            units_score = min(units * 3, 30)
            stock_score = 20 if stock > 0 else 0
            transaction_score = min(transactions * 2, 10)

            performance_score = revenue_score + units_score + stock_score + transaction_score
            product_dict['performance_score'] = min(performance_score, 100)

            if performance_score >= 80:
                product_dict['performance_label'] = 'Excellent'
            elif performance_score >= 60:
                product_dict['performance_label'] = 'Good'
            elif performance_score >= 40:
                product_dict['performance_label'] = 'Average'
            else:
                product_dict['performance_label'] = 'Poor'

            products_with_scores.append(product_dict)

        conn.close()
        return jsonify({
            'products': products_with_scores,
            'dateRange': {'from': from_date, 'to': to_date}
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# Customers Report API
@app.route('/api/reports/customers', methods=['GET'])
def get_customers_report():
    """Get customer analysis data"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))

    conn = get_db_connection()
    try:
        customers_data = conn.execute('''
            SELECT 
                c.id,
                c.name,
                c.phone,
                c.email,
                COUNT(DISTINCT b.id) as total_orders,
                COALESCE(SUM(b.total_amount), 0) as total_spent,
                COALESCE(AVG(b.total_amount), 0) as avg_order,
                MAX(DATE(b.created_at)) as last_purchase,
                CASE 
                    WHEN MAX(DATE(b.created_at)) >= DATE('now', '-7 days') THEN 'Active'
                    WHEN MAX(DATE(b.created_at)) >= DATE('now', '-30 days') THEN 'Recent'
                    ELSE 'Inactive'
                END as status
            FROM customers c
            LEFT JOIN bills b ON c.id = b.customer_id AND DATE(b.created_at) BETWEEN ? AND ?
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.phone, c.email
            HAVING total_orders > 0
            ORDER BY total_spent DESC
        ''', (from_date, to_date)).fetchall()

        conn.close()
        return jsonify({'customers': [dict(row) for row in customers_data], 'dateRange': {'from': from_date, 'to': to_date}})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

# ============================================================================
# EXPORT APIs - CSV/Excel Export Functions
# ============================================================================

@app.route('/api/reports/export/sales', methods=['GET'])
def export_sales_csv():
    """Export sales report as CSV"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    try:
        sales_data = conn.execute('''
            SELECT 
                b.bill_number as "Bill Number",
                DATE(b.created_at) as "Date",
                TIME(b.created_at) as "Time",
                COALESCE(c.name, 'Walk-in Customer') as "Customer",
                b.total_amount as "Amount",
                b.tax_amount as "Tax",
                b.discount_amount as "Discount",
                COALESCE(p.method, 'Cash') as "Payment Method",
                b.status as "Status"
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN payments p ON b.id = p.bill_id
            WHERE DATE(b.created_at) BETWEEN ? AND ?
            ORDER BY b.created_at DESC
        ''', (from_date, to_date)).fetchall()
        
        conn.close()
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if sales_data:
            writer.writerow(sales_data[0].keys())
            for row in sales_data:
                writer.writerow(row)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=sales_report_{from_date}_to_{to_date}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export/products', methods=['GET'])
def export_products_csv():
    """Export products report as CSV"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    try:
        products_data = conn.execute('''
            SELECT 
                p.name as "Product Name",
                p.category as "Category",
                p.stock as "Current Stock",
                COALESCE(SUM(bi.quantity), 0) as "Units Sold",
                COALESCE(SUM(bi.total_price), 0) as "Revenue",
                COALESCE(SUM(bi.quantity * p.cost), 0) as "Cost",
                COALESCE(SUM(bi.total_price) - SUM(bi.quantity * p.cost), 0) as "Profit",
                COUNT(DISTINCT b.id) as "Transactions"
            FROM products p
            LEFT JOIN bill_items bi ON p.id = bi.product_id
            LEFT JOIN bills b ON bi.bill_id = b.id AND DATE(b.created_at) BETWEEN ? AND ?
            WHERE p.is_active = 1
            GROUP BY p.id, p.name, p.category, p.stock, p.cost
            ORDER BY "Revenue" DESC
        ''', (from_date, to_date)).fetchall()
        
        conn.close()
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if products_data:
            writer.writerow(products_data[0].keys())
            for row in products_data:
                writer.writerow(row)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=products_report_{from_date}_to_{to_date}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/export/customers', methods=['GET'])
def export_customers_csv():
    """Export customers report as CSV"""
    from_date = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    try:
        customers_data = conn.execute('''
            SELECT 
                c.name as "Customer Name",
                c.phone as "Phone",
                c.email as "Email",
                COUNT(DISTINCT b.id) as "Total Orders",
                COALESCE(SUM(b.total_amount), 0) as "Total Spent",
                COALESCE(AVG(b.total_amount), 0) as "Average Order",
                MAX(DATE(b.created_at)) as "Last Purchase",
                CASE 
                    WHEN MAX(DATE(b.created_at)) >= DATE('now', '-7 days') THEN 'Active'
                    WHEN MAX(DATE(b.created_at)) >= DATE('now', '-30 days') THEN 'Recent'
                    ELSE 'Inactive'
                END as "Status"
            FROM customers c
            LEFT JOIN bills b ON c.id = b.customer_id AND DATE(b.created_at) BETWEEN ? AND ?
            WHERE c.is_active = 1
            GROUP BY c.id, c.name, c.phone, c.email
            HAVING "Total Orders" > 0
            ORDER BY "Total Spent" DESC
        ''', (from_date, to_date)).fetchall()
        
        conn.close()
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if customers_data:
            writer.writerow(customers_data[0].keys())
            for row in customers_data:
                writer.writerow(row)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=customers_report_{from_date}_to_{to_date}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def print_startup_info():
    """Print startup information"""
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
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

# ============================================================================
# BILLING MODULE - MOBILE ERP PERFECT CODE IMPLEMENTATION
# ============================================================================

@app.route('/api/bills', methods=['GET'])
def get_bills():
    """Get all bills with customer information - Mobile ERP Style"""
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
    """Get items for a specific bill - Mobile ERP Style"""
    conn = get_db_connection()
    items = conn.execute('''
        SELECT * FROM bill_items WHERE bill_id = ?
    ''', (bill_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in items])

@app.route('/api/bills', methods=['POST'])
def create_bill():
    """Create bill - Mobile ERP Perfect Implementation"""
    try:
        data = request.json
        print("📥 Received bill data:", data)
        
        # Validate required fields
        if not data or not data.get('items') or len(data['items']) == 0:
            return jsonify({"error": "Items are required"}), 400
        
        bill_id = generate_id()
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"📝 Generated bill: {bill_number}")
        
        conn = get_db_connection()
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Create bill record
            conn.execute('''
                INSERT INTO bills (id, bill_number, customer_id, business_type, subtotal, tax_amount, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bill_id, 
                bill_number, 
                data.get('customer_id'), 
                data.get('business_type', 'retail'),
                data.get('subtotal', 0), 
                data.get('tax_amount', 0), 
                data.get('total_amount', 0),
                'completed',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Get customer name if customer_id exists
            customer_name = None
            if data.get('customer_id'):
                customer = conn.execute('''
                    SELECT name FROM customers WHERE id = ?
                ''', (data.get('customer_id'),)).fetchone()
                customer_name = customer['name'] if customer else None
            
            # Process each item
            for item in data['items']:
                item_id = generate_id()
                
                # Insert bill item
                conn.execute('''
                    INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, 
                    bill_id, 
                    item['product_id'], 
                    item['product_name'],
                    item['quantity'], 
                    item['unit_price'], 
                    item['total_price']
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
                
                # Calculate proportional tax and discount
                subtotal = data.get('subtotal', 0)
                tax_amount = data.get('tax_amount', 0)
                discount_amount = data.get('discount_amount', 0)
                
                item_tax = (item['total_price'] / subtotal) * tax_amount if subtotal > 0 else 0
                item_discount = (item['total_price'] / subtotal) * discount_amount if subtotal > 0 else 0
                
                conn.execute('''
                    INSERT INTO sales (
                        id, bill_id, bill_number, customer_id, customer_name,
                        product_id, product_name, category, quantity, unit_price,
                        total_price, tax_amount, discount_amount, payment_method,
                        sale_date, sale_time, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                    item['product_id'], item['product_name'], 
                    product['category'] if product else 'General',
                    item['quantity'], item['unit_price'], item['total_price'],
                    item_tax, item_discount, data.get('payment_method', 'cash'),
                    sale_date, sale_time, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            # Add payment record
            if data.get('payment_method'):
                payment_id = generate_id()
                conn.execute('''
                    INSERT INTO payments (id, bill_id, method, amount, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (payment_id, bill_id, data['payment_method'], data.get('total_amount', 0), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            print(f"✅ Bill created successfully: {bill_number}")
            print(f"✅ Sales entries created: {len(data['items'])}")
            
            return jsonify({
                "message": "Bill created successfully",
                "bill_id": bill_id,
                "bill_number": bill_number,
                "success": True
            }), 201
            
        except Exception as transaction_error:
            conn.rollback()
            conn.close()
            print(f"❌ Transaction error: {str(transaction_error)}")
            return jsonify({"error": f"Transaction failed: {str(transaction_error)}"}), 500
            
    except Exception as main_error:
        print(f"❌ Bill creation error: {str(main_error)}")
        return jsonify({"error": f"Bill creation failed: {str(main_error)}"}), 500

# ============================================================================
# SALES MODULE - MOBILE ERP PERFECT CODE IMPLEMENTATION  
# ============================================================================

@app.route('/api/sales', methods=['GET'])
def get_sales():
    """Get all sales - Mobile ERP Style"""
    try:
        conn = get_db_connection()
        
        # Get date filter from query params
        date_filter = request.args.get('filter', 'all')
        
        if date_filter == 'today':
            today = datetime.now().strftime('%Y-%m-%d')
            sales = conn.execute('''
                SELECT s.*, p.name as product_name, c.name as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.sale_date = ?
                ORDER BY s.created_at DESC
            ''', (today,)).fetchall()
        elif date_filter == 'yesterday':
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            sales = conn.execute('''
                SELECT s.*, p.name as product_name, c.name as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.sale_date = ?
                ORDER BY s.created_at DESC
            ''', (yesterday,)).fetchall()
        elif date_filter == 'week':
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            sales = conn.execute('''
                SELECT s.*, p.name as product_name, c.name as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.sale_date >= ?
                ORDER BY s.created_at DESC
            ''', (week_ago,)).fetchall()
        else:
            # All sales
            sales = conn.execute('''
                SELECT s.*, p.name as product_name, c.name as customer_name
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                LEFT JOIN customers c ON s.customer_id = c.id
                ORDER BY s.created_at DESC
                LIMIT 100
            ''').fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in sales])
        
    except Exception as e:
        print(f"❌ Sales fetch error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# REPORTS MODULE - Comprehensive Business Reports & Analytics
# ============================================================================
# ============================================================================

@app.route('/mobile/reports')
def mobile_reports():
    """Mobile Reports & Analytics"""
    return render_template('reports_mobile.html')

# ============================================================================
# MAIN APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    init_db()
    
    # Register new production-grade API routes
    from register_new_routes import register_new_routes
    register_new_routes(app)
    
    print_startup_info()
    app.run(host='0.0.0.0', port=5000, debug=True)


def print_startup_info():
    """Print startup information"""
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("📱 [MOBILE ACCESS]:")
    print(f"   Mobile App: http://{local_ip}:5000/mobile-simple")
    print(f"   Login: bizpulse.erp@gmail.com / demo123")
    print()
    print("🖥️  [DESKTOP ACCESS]:")
    print(f"   Main Site: http://localhost:5000")
    print(f"   Network: http://{local_ip}:5000")
    print()

if __name__ == '__main__':
    init_db()
    print_startup_info()
    app.run(host='0.0.0.0', port=5000, debug=True)