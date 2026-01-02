from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for, send_file
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

app = Flask(__name__, template_folder='frontend/screens/templates', static_folder='frontend/assets/static')
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
UPLOAD_FOLDER = 'frontend/assets/static/uploads'
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
            payment_status TEXT DEFAULT 'paid',
            payment_method TEXT DEFAULT 'cash',
            is_credit BOOLEAN DEFAULT 0,
            credit_due_date DATE,
            credit_amount REAL DEFAULT 0,
            credit_paid_amount REAL DEFAULT 0,
            credit_balance REAL DEFAULT 0,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # Credit Transactions table - for tracking credit payments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id TEXT PRIMARY KEY,
            bill_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL, -- 'payment', 'adjustment', 'interest'
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            reference_number TEXT,
            notes TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id) REFERENCES bills (id),
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
    
    # Add profile_picture column to clients table if it doesn't exist
    try:
        cursor.execute('ALTER TABLE clients ADD COLUMN profile_picture TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Add additional profile columns to clients table if they don't exist
    additional_client_columns = [
        ('city', 'TEXT'),
        ('state', 'TEXT'),
        ('pincode', 'TEXT'),
        ('country', 'TEXT DEFAULT "India"'),
        ('pan_number', 'TEXT'),
        ('website', 'TEXT'),
        ('date_of_birth', 'TEXT'),
        ('language', 'TEXT DEFAULT "en"'),
        ('timezone', 'TEXT DEFAULT "Asia/Kolkata"'),
        ('currency', 'TEXT DEFAULT "INR"'),
        ('date_format', 'TEXT DEFAULT "DD/MM/YYYY"'),
        ('last_login', 'TIMESTAMP'),
        ('login_count', 'INTEGER DEFAULT 0')
    ]
    
    for column_name, column_type in additional_client_columns:
        try:
            cursor.execute(f'ALTER TABLE clients ADD COLUMN {column_name} {column_type}')
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
    
    # Add BizPulse admin user if not exists
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('bizpulse.erp@gmail.com',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (id, first_name, last_name, email, business_name, business_type, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin-bizpulse', 'BizPulse', 'Admin', 'bizpulse.erp@gmail.com', 'BizPulse ERP', 'software', hash_password('demo123'), 1, datetime.now().isoformat()))
    
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

# BizPulse User Authentication decorator (for Client Management)
def require_bizpulse_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if user is BizPulse official user
        user_email = session.get('email', '').lower()
        user_username = session.get('username', '').lower()
        
        bizpulse_users = [
            'bizpulse.erp@gmail.com',
            'admin@bizpulse.com',
            'support@bizpulse.com',
            'developer@bizpulse.com',
            'osman@bizpulse.com'
        ]
        
        is_bizpulse_user = (
            user_email in bizpulse_users or 
            user_username in bizpulse_users or 
            '@bizpulse.com' in user_email
        )
        
        if not is_bizpulse_user:
            return render_template('error.html', 
                                 error_title="Access Denied", 
                                 error_message="Client Management is only available to BizPulse official users. Please contact support@bizpulse.com for access."), 403
        
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
def retail_billing():
    return render_template('retail_billing.html')

@app.route('/retail/billing-test')
def retail_billing_test():
    return "<h1>✅ Billing Route Working!</h1><p>This is a test route to verify billing is accessible.</p>"

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
        
        # Today's Revenue (from bills - EXCLUDING credit bills)
        today_revenue = cursor.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as revenue,
                   COUNT(*) as transactions
            FROM bills 
            WHERE DATE(created_at) = ?
            AND NOT EXISTS (
                SELECT 1 FROM sales s 
                WHERE s.bill_id = bills.id 
                AND s.payment_method = 'credit'
            )
        ''', (today,)).fetchone()
        
        # Today's Sales (INCLUDING credit bills for sales count)
        today_sales = cursor.execute('''
            SELECT COALESCE(SUM(s.total_price), 0) as sales,
                   COUNT(DISTINCT s.bill_id) as bills
            FROM sales s
            WHERE s.sale_date = ?
        ''', (today,)).fetchone()
        
        # Today's Cost & Profit (from sales with product cost - EXCLUDING credit bills from profit)
        today_profit_data = cursor.execute('''
            SELECT 
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(s.quantity * p.cost), 0) as total_cost
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE s.sale_date = ?
            AND s.payment_method != 'credit'
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
            'today_sales': float(today_sales['sales']),  # NEW: Total sales including credit
            'today_orders': today_sales['bills'],  # Use total bills count including credit
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
                'revenue': float(today_revenue['revenue']),  # Excludes credit
                'sales': float(today_sales['sales']),        # Includes credit
                'transactions': today_sales['bills'],        # Total bills including credit
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
    return render_template('retail_profile_professional.html')

@app.route('/test-reports')
def test_reports():
    return "<h1>🎉 Reports Module Working!</h1><p>Route is active!</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@app.route('/retail/sales')
def retail_sales():
    return render_template('retail_sales_professional.html')

@app.route('/retail/credit')
def retail_credit():
    return render_template('retail_credit_professional.html')

@app.route('/retail/sales-old')
def retail_sales_old():
    return render_template('retail_sales_enhanced.html')

@app.route('/retail/inventory')
def retail_inventory():
    return render_template('inventory_professional.html')

@app.route('/retail/settings')
def retail_settings():
    return render_template('settings_professional.html')

@app.route('/retail/invoices')
def retail_invoices():
    try:
        return render_template('invoices_professional.html')
    except Exception as e:
        return f"<h1>❌ Invoice Template Error</h1><p>Error: {str(e)}</p><p>Template: invoices_professional.html</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@app.route('/retail/invoices-test')
def retail_invoices_test():
    return "<h1>✅ Invoice Route Working!</h1><p>This is a test route to verify invoices are accessible.</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@app.route('/retail/invoice/<invoice_id>')
def retail_invoice_detail(invoice_id):
    try:
        return render_template('retail_invoice_detail.html', invoice_id=invoice_id)
    except Exception as e:
        return f"<h1>❌ Invoice Detail Template Error</h1><p>Error: {str(e)}</p><p>Template: retail_invoice_detail.html</p><p>Invoice ID: {invoice_id}</p><a href='/retail/invoices'>Back to Invoices</a>"

@app.route('/invoice-demo')
def invoice_demo():
    return render_template('invoice_demo.html')

@app.route('/invoice-test')
def invoice_test():
    """Invoice System Test Page"""
    return render_template('invoice_test_page.html')

# ============================================================================
# DESKTOP APP DOWNLOAD ROUTES - BizPulse Desktop ERP
# ============================================================================

@app.route('/desktop')
def desktop_download_page():
    """Desktop App Download Page"""
    return render_template('desktop_download.html')

@app.route('/download/desktop')
def download_desktop_app():
    """Download BizPulse Desktop ERP (Portable ZIP)"""
    try:
        zip_file = "BizPulse-Desktop/BizPulse-Desktop-Portable-20251223.zip"
        
        if os.path.exists(zip_file):
            return send_file(
                zip_file,
                as_attachment=True,
                download_name="BizPulse-Desktop-ERP.zip",
                mimetype='application/zip'
            )
        else:
            return jsonify({
                'error': 'Desktop app not found',
                'message': 'Please build the desktop app first',
                'build_command': 'cd BizPulse-Desktop && npm run pack'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/desktop/exe')
def download_desktop_exe():
    """Download BizPulse Desktop ERP (Direct EXE)"""
    try:
        exe_file = "BizPulse-Desktop/dist/win-unpacked/BizPulse ERP.exe"
        
        if os.path.exists(exe_file):
            return send_file(
                exe_file,
                as_attachment=True,
                download_name="BizPulse-ERP.exe",
                mimetype='application/octet-stream'
            )
        else:
            return jsonify({
                'error': 'Desktop executable not found',
                'message': 'Please build the desktop app first'
            }), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/desktop/info')
def desktop_app_info():
    """Get desktop app information and download status"""
    try:
        zip_file = "BizPulse-Desktop/BizPulse-Desktop-Portable-20251223.zip"
        exe_file = "BizPulse-Desktop/dist/win-unpacked/BizPulse ERP.exe"
        
        zip_exists = os.path.exists(zip_file)
        exe_exists = os.path.exists(exe_file)
        
        zip_size = 0
        exe_size = 0
        
        if zip_exists:
            zip_size = round(os.path.getsize(zip_file) / (1024 * 1024), 1)  # MB
        
        if exe_exists:
            exe_size = round(os.path.getsize(exe_file) / (1024 * 1024), 1)  # MB
        
        return jsonify({
            'available': zip_exists or exe_exists,
            'zip': {
                'available': zip_exists,
                'size_mb': zip_size,
                'download_url': '/download/desktop' if zip_exists else None
            },
            'exe': {
                'available': exe_exists,
                'size_mb': exe_size,
                'download_url': '/download/desktop/exe' if exe_exists else None
            },
            'version': '1.0.0',
            'build_date': '2024-12-23',
            'features': [
                'Desktop wrapper for web ERP',
                'System tray integration',
                'Auto-start with Windows',
                'Offline-ready architecture',
                'No installation required (portable)'
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug-routes')
def debug_routes():
    """Debug route to show all available routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        if 'invoice' in rule.rule.lower():
            routes.append(f"{rule.rule} -> {rule.endpoint}")
    
    html = "<h1>🔍 Invoice Routes Debug</h1>"
    html += "<h2>Available Invoice Routes:</h2><ul>"
    for route in routes:
        html += f"<li>{route}</li>"
    html += "</ul>"
    html += "<h2>Test Links:</h2>"
    html += "<ul>"
    html += "<li><a href='/retail/invoices-test'>Invoice Test Route</a></li>"
    html += "<li><a href='/retail/invoices'>Invoice Main Route</a></li>"
    html += "<li><a href='/retail/invoice/test-123'>Invoice Detail Route</a></li>"
    html += "<li><a href='/invoice-demo'>Invoice Demo Route</a></li>"
    html += "<li><a href='/api/invoices'>Invoice API</a></li>"
    html += "</ul>"
    html += "<p><a href='/retail/dashboard'>Back to Dashboard</a></p>"
    return html

@app.route('/test-navigation')
def test_navigation():
    return render_template('test_navigation.html')

@app.route('/test-permissions')
def test_permissions():
    return render_template('test_permissions.html')

@app.route('/sales-management')
def sales_management():
    return render_template('sales_management_wine.html')

@app.route('/debug-sales')
def debug_sales():
    return render_template('debug_sales_management.html')

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
    """Unified login for all user types with proper database authentication"""
    data = request.get_json()
    
    # Handle both login_id and loginId (mobile uses loginId)
    login_id = data.get('loginId') or data.get('login_id') or data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not login_id or not password:
        return jsonify({'message': 'Login ID and password are required'}), 400
    
    conn = get_db_connection()
    
    try:
        # First check users table (includes BizPulse admin users)
        user = conn.execute("SELECT id, first_name, last_name, email, business_name, business_type, password_hash, is_active FROM users WHERE email = ? AND is_active = 1", (login_id,)).fetchone()
        
        if user and hash_password(password) == user['password_hash']:
            # Determine if this is a BizPulse admin user
            bizpulse_emails = [
                'bizpulse.erp@gmail.com',
                'admin@bizpulse.com', 
                'support@bizpulse.com',
                'developer@bizpulse.com',
                'osman@bizpulse.com'
            ]
            
            is_bizpulse_admin = (
                user['email'].lower() in bizpulse_emails or 
                '@bizpulse.com' in user['email'].lower()
            )
            
            # Set session data
            session['user_id'] = user['id']
            session['user_type'] = 'admin' if is_bizpulse_admin else 'client'
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['email'] = user['email']
            session['username'] = user['email']  # Use email as username for BizPulse check
            session['business_name'] = user['business_name']
            session['business_type'] = user['business_type']
            session['is_super_admin'] = is_bizpulse_admin
            session.permanent = True
            
            conn.close()
            
            logger.info(f"✅ User login successful: {user['email']} (BizPulse: {is_bizpulse_admin})")
            
            return jsonify({
                "message": "Login successful",
                "token": "user-jwt-token",
                "user": {
                    "id": user['id'],
                    "name": f"{user['first_name']} {user['last_name']}",
                    "email": user['email'],
                    "username": user['email'],
                    "type": 'admin' if is_bizpulse_admin else 'client',
                    "business_name": user['business_name'],
                    "business_type": user['business_type'],
                    "is_super_admin": is_bizpulse_admin
                }
            })
        
        # Then check client database (business owners)
        client = conn.execute("SELECT id, company_name, contact_name, contact_email, username, password_hash, is_active FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (login_id, login_id)).fetchone()
        
        if client and hash_password(password) == client['password_hash']:
            # Set session data for client
            session['user_id'] = client['id']
            session['user_type'] = "client"
            session['user_name'] = client['contact_name'] or client['company_name']
            session['email'] = client['contact_email']
            session['username'] = client['username']
            session['company_name'] = client['company_name']
            session['is_super_admin'] = False
            session.permanent = True
            
            conn.close()
            return jsonify({
                "message": "Login successful",
                "token": "client-jwt-token",
                "user": {
                    "id": client['id'],
                    "name": client['contact_name'] or client['company_name'],
                    "email": client['contact_email'],
                    "username": client['username'],
                    "type": "client",
                    "company_name": client['company_name'],
                    "business_type": "retail",
                    "is_super_admin": False
                }
            })
        
        # Finally check staff and employee tables
        staff = conn.execute("SELECT s.id, s.name, s.email, s.username, s.password_hash, s.role, s.is_active, s.business_owner_id, c.company_name as business_name FROM staff s JOIN clients c ON s.business_owner_id = c.id WHERE (s.email = ? OR s.username = ?) AND s.is_active = 1", (login_id, login_id)).fetchone()
        
        if staff and hash_password(password) == staff['password_hash']:
            # Set session data for staff member
            session['user_id'] = staff['id']
            session['user_type'] = "staff"
            session['user_name'] = staff['name']
            session['email'] = staff['email']
            session['username'] = staff['username']
            session['business_owner_id'] = staff['business_owner_id']
            session['staff_role'] = staff['role']
            session['is_super_admin'] = False
            session.permanent = True
            
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
                    "business_type": "retail",
                    "is_super_admin": False
                }
            })
        
        # Check client users (employees)
        client_user = conn.execute("SELECT cu.id, cu.full_name, cu.email, cu.username, cu.password_hash, cu.is_active, cu.role, cu.client_id, c.company_name FROM client_users cu JOIN clients c ON cu.client_id = c.id WHERE (cu.email = ? OR cu.username = ?) AND cu.is_active = 1", (login_id, login_id)).fetchone()
        
        if client_user and hash_password(password) == client_user['password_hash']:
            # Set session data for employee user
            session['user_id'] = client_user['id']
            session['user_type'] = "employee"
            session['user_name'] = client_user['full_name']
            session['email'] = client_user['email']
            session['username'] = client_user['username']
            session['client_id'] = client_user['client_id']
            session['is_super_admin'] = False
            session.permanent = True
            
            # Update last login
            conn.execute("UPDATE client_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (client_user['id'],))
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
                    "business_type": "retail",
                    "is_super_admin": False
                }
            })
        
        conn.close()
        return jsonify({"message": "Invalid credentials"}), 401
        
    except Exception as e:
        conn.close()
        logger.error(f"Login error: {e}")
        return jsonify({"message": "Login error", "error": str(e)}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Generate password reset token and allow user to set new password"""
    data = request.get_json()
    email_or_username = data.get('email', '').strip() or data.get('username', '').strip()
    
    if not email_or_username:
        return jsonify({'message': 'Email or username is required'}), 400
    
    conn = get_db_connection()
    
    try:
        # Create password_reset_tokens table if it doesn't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_type TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                username TEXT,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        user_found = None
        user_type = None
        user_id = None
        username = None
        
        # Check in users table first
        user = conn.execute("SELECT id, email, first_name, last_name FROM users WHERE (email = ? OR email = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
        
        if user:
            user_found = user
            user_type = 'user'
            user_id = user['id']
            username = user['email']
        else:
            # Check in clients table
            client = conn.execute("SELECT id, contact_email, company_name, username FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
            
            if client:
                user_found = client
                user_type = 'client'
                user_id = client['id']
                username = client['username']
            else:
                # Check in client_users table (employees)
                client_user = conn.execute("SELECT id, email, full_name, username FROM client_users WHERE (email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
                
                if client_user:
                    user_found = client_user
                    user_type = 'client_user'
                    user_id = client_user['id']
                    username = client_user['username']
                else:
                    # Check in staff table
                    staff = conn.execute("SELECT id, email, name, username FROM staff WHERE (email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
                    
                    if staff:
                        user_found = staff
                        user_type = 'staff'
                        user_id = staff['id']
                        username = staff['username']
        
        if not user_found:
            # Return generic message for security (don't reveal if user exists)
            conn.close()
            return jsonify({
                'success': True,
                'message': 'If an account with this email/username exists, password reset instructions have been provided.',
                'show_reset_form': False
            }), 200
        
        # Generate reset token
        reset_token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=24)  # Token expires in 24 hours
        
        # Get email for the user
        if user_type == 'user':
            email = user_found['email']
        elif user_type == 'client':
            email = user_found['contact_email']
        elif user_type == 'client_user':
            email = user_found['email']
        elif user_type == 'staff':
            email = user_found['email']
        
        # Store reset token
        conn.execute('''
            INSERT INTO password_reset_tokens (id, user_id, user_type, token, email, username, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (generate_id(), user_id, user_type, reset_token, email, username, expires_at))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Password reset token generated successfully.',
            'reset_token': reset_token,
            'email': email,
            'username': username,
            'expires_in_hours': 24,
            'show_reset_form': True
        }), 200
        
    except Exception as e:
        conn.close()
        logger.error(f"Forgot password error: {e}")
        return jsonify({'message': 'Error processing request', 'error': str(e)}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    token = data.get('token', '').strip()
    new_password = data.get('new_password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()
    
    if not token or not new_password:
        return jsonify({'message': 'Token and new password are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400
    
    if len(new_password) < 6:
        return jsonify({'message': 'Password must be at least 6 characters long'}), 400
    
    conn = get_db_connection()
    
    try:
        # Find valid reset token
        cursor = conn.execute('''
            SELECT user_id, user_type, email, username, expires_at 
            FROM password_reset_tokens 
            WHERE token = ? AND expires_at > datetime('now')
        ''', (token,))
        
        reset_data = cursor.fetchone()
        
        if not reset_data:
            return jsonify({'message': 'Invalid or expired reset token'}), 400
        
        user_id, user_type, email, username, expires_at = reset_data
        
        # Hash the new password
        hashed_password = generate_password_hash(new_password)
        
        # Update user password based on user type
        if user_type == 'admin':
            conn.execute('''
                UPDATE admin_users 
                SET password = ? 
                WHERE id = ?
            ''', (hashed_password, user_id))
        else:
            conn.execute('''
                UPDATE client_users 
                SET password = ? 
                WHERE id = ?
            ''', (hashed_password, user_id))
        
        # Delete the used reset token
        conn.execute('DELETE FROM password_reset_tokens WHERE token = ?', (token,))
        
        conn.commit()
        
        return jsonify({
            'message': 'Password reset successfully',
            'success': True
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"Password reset error: {e}")
        return jsonify({'message': 'Failed to reset password'}), 500
    
    finally:
        conn.close()

@app.route('/api/auth/unified-login-demo', methods=['POST'])
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
        client = conn.execute("SELECT id, company_name, contact_email, username, password_hash, is_active FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (login_id, login_id)).fetchone()
        
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
        staff = conn.execute("SELECT s.id, s.name, s.email, s.username, s.password_hash, s.role, s.is_active, s.business_owner_id, c.company_name as business_name FROM staff s JOIN clients c ON s.business_owner_id = c.id WHERE (s.email = ? OR s.username = ?) AND s.is_active = 1", (login_id, login_id)).fetchone()
        
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
        client_user = conn.execute("SELECT cu.id, cu.full_name, cu.email, cu.username, cu.password_hash, cu.is_active, cu.role, cu.client_id, c.company_name FROM client_users cu JOIN clients c ON cu.client_id = c.id WHERE (cu.email = ? OR cu.username = ?) AND cu.is_active = 1 AND c.is_active = 1", (login_id, login_id)).fetchone()
        
        if client_user and hash_password(password) == client_user['password_hash']:
            # Set session data for employee user
            session['user_id'] = client_user['id']
            session['user_type'] = "employee"
            session['user_name'] = client_user['full_name']
            session['client_id'] = client_user['client_id']
            session['is_super_admin'] = False
            
            # Update last login
            conn.execute("UPDATE client_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (client_user['id'],))
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
    """Get current user information including role and profile data"""
    try:
        user_id = session.get('user_id')
        user_type = session.get('user_type')
        user_name = session.get('user_name')
        
        # If it's a client, get the actual contact name from database
        if user_type == 'client' and user_id:
            conn = get_db_connection()
            try:
                client = conn.execute("SELECT contact_name, company_name, contact_email, profile_picture FROM clients WHERE id = ?", (user_id,)).fetchone()
                
                if client:
                    # Use contact_name if available, otherwise use company_name
                    actual_name = client['contact_name'] or client['company_name'] or user_name
                    profile_picture = client['profile_picture']
                    email = client['contact_email']
                else:
                    actual_name = user_name
                    profile_picture = None
                    email = None
                    
            except Exception as e:
                print(f"Error getting client profile: {e}")
                actual_name = user_name
                profile_picture = None
                email = None
            finally:
                conn.close()
        else:
            actual_name = user_name
            profile_picture = None
            email = None
        
        return jsonify({
            "user_id": user_id,
            "user_type": user_type,
            "user_name": actual_name,
            "email": email or session.get('email'),  # Include session email as fallback
            "username": session.get('username'),     # Include username for BizPulse check
            "profile_picture": profile_picture,
            "is_super_admin": session.get('is_super_admin', False),
            "staff_role": session.get('staff_role')  # For staff members
        })
        
    except Exception as e:
        print(f"Error in get_user_info: {e}")
        return jsonify({
            "user_id": session.get('user_id'),
            "user_type": session.get('user_type'),
            "user_name": session.get('user_name'),
            "email": session.get('email'),           # Include session email
            "username": session.get('username'),     # Include username
            "profile_picture": None,
            "is_super_admin": session.get('is_super_admin', False),
            "staff_role": session.get('staff_role')
        })

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    user_id = generate_id()
    
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (id, email, password_hash, business_name, business_type) VALUES (?, ?, ?, ?, ?)", (
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
        products = conn.execute("SELECT id, name, code, barcode_data, price, stock FROM products WHERE is_active = 1 ORDER BY created_at DESC LIMIT 20").fetchall()
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
        conn.execute("""UPDATE products 
            SET barcode_data = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?""", (barcode, product_id))
        
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
        all_barcodes = conn.execute("""SELECT id, name, barcode_data FROM products 
            WHERE barcode_data IS NOT NULL AND barcode_data != '' AND is_active = 1""").fetchall()
        
        print(f"🔍 [BARCODE SEARCH] Available barcodes in database: {len(all_barcodes)}")
        for bc in all_barcodes:
            print(f"   - Product: {bc['name']}, Barcode: '{bc['barcode_data']}'")
        
        # EXACT MATCH ONLY - Primary lookup by barcode_data
        product = conn.execute("""SELECT * FROM products 
            WHERE barcode_data = ? AND is_active = 1
            LIMIT 1""", (barcode,)).fetchone()
        
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
            existing_barcode = conn.execute("""SELECT id, name FROM products 
                WHERE barcode_data = ? AND is_active = 1""", (barcode_data,)).fetchone()
            
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
            conn.execute("""INSERT INTO products (
                    id, code, name, category, price, cost, stock, min_stock, 
                    unit, business_type, barcode_data, barcode_image, image_url, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
                data.get('image_url'),  # Store product image URL
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

@app.route('/api/products/<product_id>', methods=['PUT'])
@require_auth
def update_product(product_id):
    """Update an existing product"""
    try:
        data = request.json
        print(f"[PRODUCT UPDATE] Updating product {product_id} with data: {data}")
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('price'):
            return jsonify({
                "success": False,
                "error": "Product name and price are required"
            }), 400
        
        conn = get_db_connection()
        
        # Check if product exists
        existing_product = conn.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)).fetchone()
        
        if not existing_product:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Product not found"
            }), 404
        
        # Extract and validate barcode data
        barcode_data = data.get('barcode_data', '').strip() if data.get('barcode_data') else None
        barcode_image = data.get('barcode_image')
        
        # Check if barcode already exists (excluding current product)
        if barcode_data:
            existing_barcode = conn.execute("""SELECT id, name FROM products 
                WHERE barcode_data = ? AND is_active = 1 AND id != ?""", (barcode_data, product_id)).fetchone()
            
            if existing_barcode:
                conn.close()
                return jsonify({
                    "success": False,
                    "error": f"Another product already exists with this barcode",
                    "existing_product": {
                        "id": existing_barcode['id'],
                        "name": existing_barcode['name']
                    },
                    "barcode": barcode_data
                }), 409
        
        # Update product
        try:
            conn.execute("""UPDATE products SET
                    code = ?, name = ?, category = ?, price = ?, cost = ?, 
                    stock = ?, min_stock = ?, unit = ?, business_type = ?,
                    barcode_data = ?, barcode_image = ?, image_url = ?
                WHERE id = ?""", (
                data.get('code', existing_product['code']),
                data['name'].strip(), 
                data.get('category', existing_product['category']),
                float(data['price']), 
                float(data.get('cost', existing_product['cost'])), 
                int(data.get('stock', existing_product['stock'])),
                int(data.get('min_stock', existing_product['min_stock'])), 
                data.get('unit', existing_product['unit']), 
                data.get('business_type', existing_product['business_type']),
                barcode_data,
                barcode_image,
                data.get('image_url', existing_product['image_url']),  # Handle image URL
                product_id
            ))
            
            conn.commit()
            print(f"[PRODUCT UPDATE] Successfully updated product: {product_id}")
            
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
            "message": "Product updated successfully", 
            "product": {
                "id": product_id,
                "name": data['name'],
                "image_url": data.get('image_url')
            }
        }), 200
        
    except ValueError as e:
        print(f"[PRODUCT UPDATE] ValueError: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"[PRODUCT UPDATE] Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to update product: {str(e)}"
        }), 500

@app.route('/api/products/<product_id>', methods=['DELETE'])
@require_auth
def delete_product(product_id):
    """Delete product completely from database"""
    try:
        print(f"[PRODUCT DELETE] Deleting product: {product_id}")
        
        conn = get_db_connection()
        
        # Check if product exists
        product = conn.execute("SELECT id, name, barcode_data FROM products WHERE id = ?", (product_id,)).fetchone()
        
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

# ============================================================================
# IMAGE RECOMMENDATION API - Production Ready
# ============================================================================

@app.route('/api/products/recommend-images', methods=['POST'])
def recommend_product_images():
    """
    Recommend product images based on name and category
    Uses Unsplash API for high-quality, royalty-free images
    """
    try:
        data = request.json
        product_name = data.get('product_name', '').strip()
        category = data.get('category', '').strip()
        
        if not product_name:
            return jsonify({
                'success': False,
                'error': 'Product name is required'
            }), 400
        
        # Build search query
        search_terms = []
        
        # Add product name (clean it up)
        clean_name = product_name.lower()
        # Remove common words that don't help with image search
        exclude_words = ['1kg', '500g', '250g', '1l', '500ml', 'pack', 'piece', 'pcs']
        for word in exclude_words:
            clean_name = clean_name.replace(word, '')
        
        search_terms.append(clean_name.strip())
        
        # Add category if provided
        if category and category.lower() != 'other':
            search_terms.append(category.lower())
        
        # Create search query
        search_query = ' '.join(search_terms)
        
        print(f"🔍 Image search for: '{product_name}' -> Query: '{search_query}'")
        
        # Try multiple search approaches for better results
        image_results = []
        
        # Method 1: Direct Unsplash search
        unsplash_images = search_unsplash_images(search_query)
        if unsplash_images:
            image_results.extend(unsplash_images)
        
        # Method 2: Fallback with category only if no results
        if len(image_results) < 3 and category:
            category_images = search_unsplash_images(category)
            if category_images:
                image_results.extend(category_images)
        
        # Method 3: Generic food/product images as last resort
        if len(image_results) < 3:
            generic_images = get_generic_product_images(category)
            image_results.extend(generic_images)
        
        # Remove duplicates and limit to 8 images
        seen_urls = set()
        unique_images = []
        for img in image_results:
            if img['url'] not in seen_urls and len(unique_images) < 8:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        if not unique_images:
            return jsonify({
                'success': False,
                'error': 'No suitable images found. Please try a different product name or upload your own image.'
            }), 404
        
        return jsonify({
            'success': True,
            'images': unique_images,
            'search_query': search_query,
            'total_found': len(unique_images)
        })
        
    except Exception as e:
        print(f"❌ Error in image recommendation: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch image recommendations. Please try again.'
        }), 500

def search_unsplash_images(query, per_page=6):
    """
    Search for actual product images based on product name
    Uses curated product-specific images for reliable results
    """
    try:
        # Clean and prepare search query
        clean_query = query.strip().lower()
        
        # Remove common size indicators that don't help with image search
        size_words = ['1kg', '500g', '250g', '1l', '500ml', '2kg', '5kg', 'pack', 'piece', 'pcs', 'box', 'bottle']
        for word in size_words:
            clean_query = clean_query.replace(word, '').strip()
        
        # Handle Hindi/Hinglish to English translation for better search
        hindi_to_english = {
            'haldi': 'turmeric',
            'dhaniya': 'coriander',
            'jeera': 'cumin',
            'atta': 'wheat flour',
            'chawal': 'rice',
            'dal': 'lentils',
            'namak': 'salt',
            'chini': 'sugar',
            'tel': 'oil',
            'doodh': 'milk',
            'pyaz': 'onion',
            'aloo': 'potato',
            'tamatar': 'tomato',
            'mirch': 'chili pepper',
            'adrak': 'ginger',
            'lehsun': 'garlic',
            'methi': 'fenugreek',
            'sarson': 'mustard',
            'til': 'sesame',
            'badam': 'almonds',
            'kaju': 'cashew',
            'pista': 'pistachio'
        }
        
        # Translate Hindi words to English for better search
        search_terms = []
        words = clean_query.split()
        for word in words:
            if word in hindi_to_english:
                search_terms.append(hindi_to_english[word])
            else:
                search_terms.append(word)
        
        # Create final search query
        final_query = ' '.join(search_terms)
        print(f"🔍 Searching for: '{query}' → '{final_query}'")
        
        images = []
        
        # Method 1: Use curated product-specific images (primary method)
        try:
            curated_images = get_product_fallback_images(final_query, per_page)
            if curated_images:
                images.extend(curated_images)
                print(f"✅ Found {len(curated_images)} curated product-specific images")
            else:
                print("⚠️ No curated images found for this product")
                
        except Exception as e:
            print(f"❌ Curated images failed: {e}")
        
        # Method 2: Try external API if we need more images (optional enhancement)
        if len(images) < per_page:
            try:
                import requests
                # Use Pixabay's free API
                pixabay_url = "https://pixabay.com/api/"
                params = {
                    'key': '9656065-a4094594c34f9ac14c7fc4c39',  # Free public key
                    'q': final_query,
                    'image_type': 'photo',
                    'category': 'food',
                    'min_width': 200,
                    'min_height': 200,
                    'per_page': per_page - len(images),
                    'safesearch': 'true'
                }
                
                response = requests.get(pixabay_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for hit in data.get('hits', []):
                        if len(images) >= per_page:
                            break
                        images.append({
                            'url': hit.get('webformatURL', ''),
                            'thumbnail': hit.get('previewURL', ''),
                            'title': f"{query.title()} - {hit.get('tags', '').title()}",
                            'source': 'Pixabay',
                            'search_term': final_query
                        })
                    
                    print(f"✅ Found {len(data.get('hits', []))} additional images from Pixabay")
                
            except Exception as e:
                print(f"❌ Pixabay search failed: {e}")
        
        # Remove duplicates and limit results
        seen_urls = set()
        unique_images = []
        for img in images:
            if img['url'] not in seen_urls and len(unique_images) < per_page:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        print(f"✅ Generated {len(unique_images)} images for '{query}'")
        return unique_images
        
    except Exception as e:
        print(f"❌ Image search error: {e}")
        return get_guaranteed_fallback_images(query)

def get_product_specific_terms(query):
    """
    Get specific search terms based on the product
    Returns actual product-related terms, not random categories
    """
    product_terms = {
        'rice': ['basmati rice', 'white rice', 'rice grains', 'rice bowl', 'cooked rice'],
        'turmeric': ['turmeric powder', 'haldi', 'turmeric root', 'golden spice', 'curcuma'],
        'coriander': ['coriander seeds', 'dhaniya', 'cilantro seeds', 'coriander powder'],
        'cumin': ['cumin seeds', 'jeera', 'cumin powder', 'whole cumin'],
        'wheat flour': ['wheat flour', 'atta', 'whole wheat', 'flour bag', 'wheat powder'],
        'lentils': ['dal', 'red lentils', 'yellow lentils', 'moong dal', 'toor dal'],
        'salt': ['table salt', 'sea salt', 'rock salt', 'white salt', 'salt crystals'],
        'sugar': ['white sugar', 'sugar crystals', 'sugar cubes', 'granulated sugar'],
        'oil': ['cooking oil', 'vegetable oil', 'sunflower oil', 'mustard oil', 'olive oil'],
        'milk': ['fresh milk', 'dairy milk', 'milk bottle', 'white milk', 'cow milk'],
        'onion': ['red onion', 'white onion', 'fresh onion', 'onion bulbs', 'sliced onion'],
        'potato': ['fresh potato', 'potatoes', 'potato tubers', 'boiled potato'],
        'tomato': ['red tomato', 'fresh tomato', 'ripe tomato', 'cherry tomato'],
        'biscuits': ['cookies', 'crackers', 'tea biscuits', 'sweet biscuits'],
        'noodles': ['instant noodles', 'pasta', 'ramen', 'wheat noodles'],
        'tea': ['tea leaves', 'black tea', 'green tea', 'tea cup', 'chai'],
        'coffee': ['coffee beans', 'ground coffee', 'coffee powder', 'instant coffee']
    }
    
    # Find matching terms based on query
    query_lower = query.lower()
    for key, terms in product_terms.items():
        if key in query_lower or any(key_word in query_lower for key_word in key.split()):
            return terms[:4]  # Return first 4 specific terms
    
    # If no specific match, return generic food terms with the product name
    return [f"{query} food", f"fresh {query}", f"{query} ingredient", f"{query} product"]

def get_guaranteed_fallback_images(query):
    """
    Guaranteed fallback images that always work
    """
    try:
        images = []
        
        # Use reliable Picsum IDs
        reliable_ids = [292, 326, 431, 488, 691, 715, 835, 884]
        
        for i, img_id in enumerate(reliable_ids):
            url = f"https://picsum.photos/300/300?random={img_id}"
            images.append({
                'url': url,
                'thumbnail': url,
                'title': f"{query.title()} - Fallback Image {i + 1}",
                'source': 'Picsum (Guaranteed)',
                'search_term': query
            })
        
        return images
        
    except Exception as e:
        print(f"❌ Even guaranteed fallback failed: {e}")
        # Last resort - return base64 placeholder
        placeholder_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Crect width='300' height='300' fill='%23f0f0f0'/%3E%3Ctext x='150' y='150' text-anchor='middle' dy='.3em' font-family='Arial' font-size='16' fill='%23999'%3EProduct Image%3C/text%3E%3C/svg%3E"
        
        return [{
            'url': placeholder_svg,
            'thumbnail': placeholder_svg,
            'title': f"{query.title()} - Placeholder",
            'source': 'SVG Placeholder',
            'search_term': query
        }]

def get_product_fallback_images(query, count=6):
    """
    Get curated product-specific fallback images
    """
    try:
        # Product-specific image mappings with real URLs
        product_image_map = {
            'rice': [
                'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop',  # Basmati rice
                'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Rice grains
                'https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=300&h=300&fit=crop',  # Rice bowl
                'https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=300&h=300&fit=crop',  # White rice
                'https://images.unsplash.com/photo-1603048297172-c92544798d5a?w=300&h=300&fit=crop',  # Rice field
                'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop'   # Cooked rice
            ],
            'turmeric': [
                'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop',  # Turmeric powder
                'https://images.unsplash.com/photo-1609501676725-7186f734b2b0?w=300&h=300&fit=crop',  # Fresh turmeric
                'https://images.unsplash.com/photo-1615485925763-4d5b3a9c3b3a?w=300&h=300&fit=crop',  # Turmeric root
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop',  # Spices
                'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Golden spice
                'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop'   # Haldi powder
            ],
            'wheat flour': [
                'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Flour
                'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Wheat
                'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Atta
                'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Wheat grains
                'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # White flour
                'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop'   # Whole wheat
            ],
            'sugar': [
                'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar cubes
                'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop',  # White sugar
                'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar crystals
                'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop',  # Granulated sugar
                'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar bowl
                'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop'   # Sweet sugar
            ],
            'oil': [
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Cooking oil
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Oil bottle
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Olive oil
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Vegetable oil
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Sunflower oil
                'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop'   # Mustard oil
            ]
        }
        
        images = []
        query_lower = query.lower()
        
        # Find matching product images
        for product, urls in product_image_map.items():
            if product in query_lower or any(word in query_lower for word in product.split()):
                for i, url in enumerate(urls[:count]):
                    images.append({
                        'url': url,
                        'thumbnail': url,
                        'title': f"{query.title()} - {product.title()} {i+1}",
                        'source': 'Curated Unsplash',
                        'search_term': product
                    })
                break
        
        # If no specific match found, use generic food images
        if not images:
            generic_food_urls = [
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop',  # Spices
                'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Ingredients
                'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Food items
                'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Grains
                'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop',  # Food products
                'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop'   # Kitchen items
            ]
            
            for i, url in enumerate(generic_food_urls[:count]):
                images.append({
                    'url': url,
                    'thumbnail': url,
                    'title': f"{query.title()} - Food Product {i+1}",
                    'source': 'Generic Food Images',
                    'search_term': query
                })
        
        return images[:count]
        
    except Exception as e:
        print(f"❌ Fallback images failed: {e}")
        return []

def get_product_specific_terms(query):
    """
    Get specific search terms based on the product
    """
    product_terms = {
        'turmeric': ['turmeric powder', 'haldi', 'turmeric root', 'golden spice', 'curcuma'],
        'coriander': ['coriander seeds', 'dhaniya', 'cilantro seeds', 'coriander powder'],
        'cumin': ['cumin seeds', 'jeera', 'cumin powder', 'whole cumin'],
        'wheat flour': ['wheat flour', 'atta', 'whole wheat', 'flour bag'],
        'rice': ['basmati rice', 'white rice', 'rice grains', 'rice bag'],
        'lentils': ['dal', 'red lentils', 'yellow lentils', 'moong dal', 'toor dal'],
        'salt': ['table salt', 'sea salt', 'rock salt', 'white salt'],
        'sugar': ['white sugar', 'sugar crystals', 'sugar cubes', 'granulated sugar'],
        'oil': ['cooking oil', 'vegetable oil', 'sunflower oil', 'mustard oil'],
        'milk': ['fresh milk', 'dairy milk', 'milk bottle', 'white milk'],
        'onion': ['red onion', 'white onion', 'fresh onion', 'onion bulbs'],
        'potato': ['fresh potato', 'potatoes', 'potato tubers'],
        'tomato': ['red tomato', 'fresh tomato', 'ripe tomato'],
        'chili pepper': ['red chili', 'green chili', 'hot pepper', 'chili powder'],
        'ginger': ['fresh ginger', 'ginger root', 'adrak'],
        'garlic': ['garlic cloves', 'fresh garlic', 'garlic bulbs']
    }
    
    # Find matching terms
    query_lower = query.lower()
    for key, terms in product_terms.items():
        if key in query_lower or any(term in query_lower for term in terms):
            return terms[:4]  # Return first 4 specific terms
    
    # Default terms if no specific match
    return [query, f"{query} ingredient", f"{query} spice", f"{query} food"]

def get_fallback_product_images(search_query, original_query):
    """
    Fallback method using reliable image sources
    """
    try:
        images = []
        
        # Use Lorem Picsum with food-related IDs as last resort
        food_ids = [292, 326, 431, 488, 691, 715, 835, 884, 918, 1059]
        
        for i, pic_id in enumerate(food_ids[:4]):
            # Add some randomization based on query
            random_id = pic_id + (hash(search_query) % 100)
            url = f"https://picsum.photos/300/300?random={random_id}"
            
            images.append({
                'url': url,
                'thumbnail': url,
                'title': f"{original_query.title()} - Image {i + 1}",
                'source': 'Picsum (Fallback)',
                'search_term': search_query
            })
        
        return images
        
    except Exception as e:
        print(f"❌ Fallback images error: {e}")
        return []

def get_generic_product_images(category):
    """
    Get generic product images based on category
    Fallback when specific search fails
    """
    import urllib.parse
    
    category_mappings = {
        'grains': 'rice,wheat,grain',
        'pulses': 'lentils,beans,dal',
        'cooking': 'oil,cooking,kitchen',
        'beverages': 'tea,coffee,drink',
        'sweeteners': 'sugar,honey,sweet',
        'dairy': 'milk,cheese,dairy',
        'snacks': 'snacks,chips,biscuits',
        'spices': 'spices,herbs,masala',
        'vegetables': 'vegetables,fresh,organic',
        'fruits': 'fruits,fresh,organic',
        'household': 'cleaning,household,supplies',
        'personal care': 'soap,shampoo,care'
    }
    
    # Get category-specific search term
    search_term = category_mappings.get(category.lower(), 'food,product,grocery')
    
    try:
        images = []
        encoded_term = urllib.parse.quote(search_term)
        
        # Generate multiple generic images
        for i in range(4):
            url = f"https://source.unsplash.com/300x300/?{encoded_term}&sig={hash(category + str(i)) % 10000}"
            images.append({
                'url': url,
                'thumbnail': url,
                'title': f"{category.title()} Product - Image {i + 1}",
                'source': 'Unsplash (Generic)'
            })
        
        return images
        
    except Exception as e:
        print(f"❌ Generic images error: {e}")
        return get_fallback_images(category)

def get_fallback_images(query):
    """
    Ultimate fallback - guaranteed to work images
    """
    try:
        # Use Picsum Photos (Lorem Ipsum for photos) - always reliable
        fallback_images = []
        
        # Predefined image IDs that work well for products
        image_ids = [292, 326, 431, 488, 691, 715, 835, 884]
        
        for i, img_id in enumerate(image_ids):
            url = f"https://picsum.photos/300/300?random={img_id}"
            fallback_images.append({
                'url': url,
                'thumbnail': url,
                'title': f"{query.title()} - Fallback Image {i + 1}",
                'source': 'Picsum Photos'
            })
        
        return fallback_images
        
    except Exception as e:
        print(f"❌ Even fallback failed: {e}")
        # Last resort - return placeholder data URLs
        return [{
            'url': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><rect width="300" height="300" fill="%23f0f0f0"/><text x="150" y="150" text-anchor="middle" dy=".3em" font-family="Arial" font-size="16" fill="%23999">Product Image</text></svg>',
            'thumbnail': 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><rect width="300" height="300" fill="%23f0f0f0"/><text x="150" y="150" text-anchor="middle" dy=".3em" font-family="Arial" font-size="16" fill="%23999">Product Image</text></svg>',
            'title': f"{query.title()} - Placeholder",
            'source': 'Placeholder'
        }]

# ============================================================================

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
    conn.execute("""INSERT INTO customers (id, name, phone, email, address, credit_limit)
        VALUES (?, ?, ?, ?, ?, ?)""", (
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
    total_sales = conn.execute("""SELECT SUM(total_amount) as total, COUNT(*) as count
        FROM bills 
        WHERE DATE(created_at) BETWEEN ? AND ?""", (start_date, end_date)).fetchone()
    
    # Daily sales
    daily_sales = conn.execute("""SELECT DATE(created_at) as date, SUM(total_amount) as sales, COUNT(*) as transactions
        FROM bills 
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date""", (start_date, end_date)).fetchall()
    
    # Top products
    top_products = conn.execute("""SELECT bi.product_name, SUM(bi.quantity) as quantity, SUM(bi.total_price) as sales
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        WHERE DATE(b.created_at) BETWEEN ? AND ?
        GROUP BY bi.product_name
        ORDER BY sales DESC
        LIMIT 10""", (start_date, end_date)).fetchall()
    
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
    conn.execute("""INSERT INTO hotel_guests (id, name, phone, email, address, id_proof, guest_count, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        
        # Today's sales and revenue from sales table (mobile ERP style)
        today_stats = conn.execute("""SELECT 
                COUNT(*) as count,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id
            WHERE s.sale_date = ?""", (today,)).fetchone()
        
        # Yesterday's sales and revenue
        yesterday_stats = conn.execute("""SELECT 
                COUNT(*) as count,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id
            WHERE s.sale_date = ?""", (yesterday,)).fetchone()
        
        # Week's sales and revenue
        week_stats = conn.execute("""SELECT 
                COUNT(*) as count,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id
            WHERE s.sale_date >= ?""", (week_start,)).fetchone()
        
        # Month's sales and revenue
        month_stats = conn.execute("""SELECT 
                COUNT(*) as count,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id
            WHERE s.sale_date >= ?""", (month_start,)).fetchone()
        
        # All time sales and revenue
        all_time_stats = conn.execute("""SELECT 
                COUNT(*) as count,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue
            FROM sales s
            LEFT JOIN bills b ON s.bill_id = b.id""").fetchone()
        
        # Top products today (mobile ERP style)
        top_products = conn.execute("""SELECT 
                product_name,
                SUM(quantity) as quantity,
                SUM(total_price) as revenue
            FROM sales 
            WHERE sale_date = ?
            GROUP BY product_id, product_name
            ORDER BY quantity DESC
            LIMIT 5""", (today,)).fetchall()
        
        # Recent transactions from bills table
        recent_transactions = conn.execute("""SELECT b.bill_number, b.total_amount, b.created_at, c.name as customer_name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            ORDER BY b.created_at DESC
            LIMIT 10""").fetchall()
        
        conn.close()
        
        return jsonify({
            "today": {
                "count": today_stats['count'],
                "total_sales": float(today_stats['total_sales']),
                "total_revenue": float(today_stats['total_revenue']),
                "total": float(today_stats['total_sales'])  # Keep for backward compatibility
            },
            "yesterday": {
                "count": yesterday_stats['count'],
                "total_sales": float(yesterday_stats['total_sales']),
                "total_revenue": float(yesterday_stats['total_revenue']),
                "total": float(yesterday_stats['total_sales'])  # Keep for backward compatibility
            },
            "week": {
                "count": week_stats['count'],
                "total_sales": float(week_stats['total_sales']),
                "total_revenue": float(week_stats['total_revenue']),
                "total": float(week_stats['total_sales'])  # Keep for backward compatibility
            },
            "month": {
                "count": month_stats['count'],
                "total_sales": float(month_stats['total_sales']),
                "total_revenue": float(month_stats['total_revenue']),
                "total": float(month_stats['total_sales'])  # Keep for backward compatibility
            },
            "all_time": {
                "count": all_time_stats['count'],
                "total_sales": float(all_time_stats['total_sales']),
                "total_revenue": float(all_time_stats['total_revenue']),
                "total": float(all_time_stats['total_sales'])  # Keep for backward compatibility
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
        sales_query = f"""SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM bills WHERE {date_filter}"""
        sales_data = conn.execute(sales_query, params).fetchone()
        
        # Get top products for the period
        products_query = f"""SELECT bi.product_name, SUM(bi.quantity) as quantity, 
                   SUM(bi.total_price) as sales, COUNT(DISTINCT b.id) as orders
            FROM bill_items bi
            JOIN bills b ON bi.bill_id = b.id
            WHERE {date_filter}
            GROUP BY bi.product_name
            ORDER BY sales DESC
            LIMIT 5"""
        top_products = conn.execute(products_query, params).fetchall()
        
        # Get recent transactions for the period
        transactions_query = f"""SELECT b.bill_number, b.total_amount, b.created_at, 
                   c.name as customer_name, b.status
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE {date_filter}
            ORDER BY b.created_at DESC
            LIMIT 10"""
        recent_transactions = conn.execute(transactions_query, params).fetchall()
        
        # Get payment methods breakdown
        payments_query = f"""SELECT p.method, COUNT(*) as count, SUM(p.amount) as total
            FROM payments p
            JOIN bills b ON p.bill_id = b.id
            WHERE {date_filter}
            GROUP BY p.method
            ORDER BY total DESC"""
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
        inventory = conn.execute("""SELECT 
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
                p.name""", (today_ist, today_ist, today_ist)).fetchall()
        
        # Get inventory summary statistics
        summary = conn.execute("""SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN stock <= 0 THEN 1 END) as out_of_stock_count,
                COUNT(CASE WHEN stock <= min_stock AND stock > 0 THEN 1 END) as low_stock_count,
                COUNT(CASE WHEN stock > min_stock THEN 1 END) as good_stock_count,
                COALESCE(SUM(stock * cost), 0) as total_inventory_value,
                COALESCE(SUM(stock * price), 0) as total_selling_value,
                COALESCE(SUM(stock * (price - cost)), 0) as potential_profit
            FROM products 
            WHERE is_active = 1""").fetchone()
        
        # Get top selling products (last 30 days)
        top_selling = conn.execute("""SELECT 
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
            LIMIT 10""", (today_ist,)).fetchall()
        
        # Get products needing restock (critical alerts)
        restock_alerts = conn.execute("""SELECT 
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
                days_remaining ASC""", (today_ist,)).fetchall()
        
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
        product = conn.execute("SELECT id, name, stock FROM products WHERE id = ? AND is_active = 1", (product_id,)).fetchone()
        
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
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        
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
        alerts = conn.execute("""SELECT 
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
                days_remaining ASC""", (today_ist, today_ist)).fetchall()
        
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
    hourly_sales = conn.execute("""SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour""", (date,)).fetchall()
    
    # Get category-wise sales for the date
    category_sales = conn.execute("""SELECT 
            p.category,
            COUNT(DISTINCT b.id) as transactions,
            COALESCE(SUM(bi.total_price), 0) as sales,
            COALESCE(SUM(bi.quantity), 0) as quantity_sold
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE DATE(b.created_at) = ?
        GROUP BY p.category
        ORDER BY sales DESC""", (date,)).fetchall()
    
    # Get hourly category breakdown
    hourly_category_sales = conn.execute("""SELECT 
            strftime('%H', b.created_at) as hour,
            p.category,
            COALESCE(SUM(bi.total_price), 0) as sales,
            COALESCE(SUM(bi.quantity), 0) as quantity
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE DATE(b.created_at) = ?
        GROUP BY strftime('%H', b.created_at), p.category
        ORDER BY hour, sales DESC""", (date,)).fetchall()
    
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
    category_details = conn.execute(f"""SELECT 
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
        ORDER BY total_sales DESC""").fetchall()
    
    # Get top selling products per category
    top_products_per_category = conn.execute(f"""SELECT 
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
        ORDER BY p.category, sales DESC""").fetchall()
    
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
    low_stock_items = conn.execute("""SELECT 
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
            p.stock ASC""").fetchall()
    
    # Get category-wise low stock summary
    category_summary = conn.execute("""SELECT 
            p.category,
            COUNT(*) as low_stock_count,
            SUM(p.min_stock - p.stock) as total_shortage,
            SUM((p.min_stock - p.stock) * p.cost) as total_reorder_cost,
            AVG(p.stock * 100.0 / p.min_stock) as avg_stock_percentage
        FROM products p
        WHERE p.is_active = 1 AND p.stock <= p.min_stock
        GROUP BY p.category
        ORDER BY low_stock_count DESC""").fetchall()
    
    # Get recent stock movements (if you have a stock_movements table)
    # For now, we'll simulate this with recent bill items
    recent_movements = conn.execute("""SELECT 
            bi.product_name,
            bi.quantity,
            b.created_at,
            'sale' as movement_type
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.id
        JOIN products p ON bi.product_id = p.id
        WHERE p.stock <= p.min_stock
        ORDER BY b.created_at DESC
        LIMIT 20""").fetchall()
    
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
            conn.execute("""UPDATE products 
                SET stock = ?, cost = ?
                WHERE id = ?""", (new_stock, cost_per_unit, product_id))
        else:
            conn.execute("""UPDATE products 
                SET stock = ?
                WHERE id = ?""", (new_stock, product_id))
        
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
        conn.execute("""UPDATE products 
            SET min_stock = ?
            WHERE id = ?""", (new_min_stock, product_id))
        
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
    today_stats = conn.execute("""SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?""", (today,)).fetchone()
    
    # Current hour stats
    current_hour_stats = conn.execute("""SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?""", (today, current_hour)).fetchone()
    
    # Recent transactions (last 5)
    recent_transactions = conn.execute("""SELECT 
            b.bill_number,
            b.total_amount,
            b.created_at,
            c.name as customer_name,
            strftime('%H:%M', b.created_at) as time
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE DATE(b.created_at) = ?
        ORDER BY b.created_at DESC
        LIMIT 5""", (today,)).fetchall()
    
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
    low_stock = conn.execute("""SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC""").fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute("""SELECT COUNT(*) as count FROM products 
        WHERE is_active = 1 AND stock = 0""").fetchone()
    
    # Total inventory value
    inventory_value = conn.execute("SELECT COALESCE(SUM(stock * cost), 0) as value FROM products WHERE is_active = 1").fetchone()
    
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
    hourly_sales = conn.execute("""SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour""", (date,)).fetchall()
    
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
        bill = conn.execute("""SELECT id, total_amount, created_at 
            FROM bills 
            WHERE id = ?""", (bill_id,)).fetchone()
        
        if not bill:
            return jsonify({"error": "Bill not found"}), 404
        
        # Get current hour's data
        current_hour = datetime.now().strftime('%H')
        today = datetime.now().strftime('%Y-%m-%d')
        
        hourly_stats = conn.execute("""SELECT 
                COUNT(*) as transactions,
                COALESCE(SUM(total_amount), 0) as sales
            FROM bills 
            WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?""", (today, current_hour)).fetchone()
        
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
    today_stats = conn.execute("""SELECT 
            COUNT(*) as total_transactions,
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(AVG(total_amount), 0) as avg_order_value
        FROM bills 
        WHERE DATE(created_at) = ?""", (today,)).fetchone()
    
    # Current hour stats
    current_hour_stats = conn.execute("""SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?""", (today, current_hour)).fetchone()
    
    # Last hour stats for comparison
    last_hour = str(int(current_hour) - 1).zfill(2) if int(current_hour) > 0 else '23'
    last_hour_date = today if int(current_hour) > 0 else (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    last_hour_stats = conn.execute("""SELECT 
            COUNT(*) as transactions,
            COALESCE(SUM(total_amount), 0) as sales
        FROM bills 
        WHERE DATE(created_at) = ? AND strftime('%H', created_at) = ?""", (last_hour_date, last_hour)).fetchone()
    
    # Recent transactions (last 5)
    recent_transactions = conn.execute("""SELECT 
            b.bill_number,
            b.total_amount,
            b.created_at,
            c.name as customer_name,
            strftime('%H:%M', b.created_at) as time
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE DATE(b.created_at) = ?
        ORDER BY b.created_at DESC
        LIMIT 5""", (today,)).fetchall()
    
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
    low_stock = conn.execute("""SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC""").fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute("""SELECT COUNT(*) as count FROM products 
        WHERE is_active = 1 AND stock = 0""").fetchone()
    
    # Total inventory value
    inventory_value = conn.execute("SELECT COALESCE(SUM(stock * cost), 0) as value FROM products WHERE is_active = 1").fetchone()
    
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
    low_stock = conn.execute("""SELECT * FROM products 
        WHERE is_active = 1 AND stock <= min_stock 
        ORDER BY stock ASC""").fetchall()
    
    # Out of stock items
    out_of_stock = conn.execute("""SELECT * FROM products 
        WHERE is_active = 1 AND stock = 0""").fetchall()
    
    # Total inventory value
    inventory_value = conn.execute("""SELECT SUM(stock * cost) as total_cost, SUM(stock * price) as total_value
        FROM products WHERE is_active = 1""").fetchone()
    
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
    
    # Total sales and revenue
    total_stats = conn.execute("""SELECT 
            COUNT(*) as count, 
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(SUM(CASE 
                WHEN payment_status = 'paid' OR is_credit = 0 THEN total_amount
                WHEN payment_status = 'partial' THEN credit_paid_amount
                ELSE 0 
            END), 0) as total_revenue
        FROM bills WHERE business_type = ?""", (business_type,)).fetchone()
    
    # Daily sales and revenue for last 7 days
    daily_stats = conn.execute("""SELECT 
            DATE(created_at) as date, 
            COUNT(*) as count, 
            COALESCE(SUM(total_amount), 0) as total_sales,
            COALESCE(SUM(CASE 
                WHEN payment_status = 'paid' OR is_credit = 0 THEN total_amount
                WHEN payment_status = 'partial' THEN credit_paid_amount
                ELSE 0 
            END), 0) as total_revenue
        FROM bills 
        WHERE business_type = ? AND DATE(created_at) >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date""", (business_type,)).fetchall()
    
    # Top products (sales value, not revenue)
    top_products = conn.execute("""SELECT p.name, SUM(bi.quantity) as quantity, SUM(bi.total_price) as sales_value
        FROM bill_items bi
        JOIN products p ON bi.product_id = p.id
        JOIN bills b ON bi.bill_id = b.id
        WHERE b.business_type = ?
        GROUP BY p.id, p.name
        ORDER BY sales_value DESC
        LIMIT 5""", (business_type,)).fetchall()
    
    conn.close()
    
    return jsonify({
        "total_stats": {
            "count": total_stats['count'],
            "total_sales": float(total_stats['total_sales']),
            "total_revenue": float(total_stats['total_revenue'])
        },
        "daily_stats": [dict(row) for row in daily_stats],
        "top_products": [dict(row) for row in top_products]
    })

# Sales Module - Detailed Sales Data APIs
@app.route('/api/sales', methods=['GET', 'POST'])
def sales_api():
    """Sales API - GET for listing with date filters, POST for creating bills"""
    
    # Import datetime at function level to avoid conflicts
    from datetime import datetime, timedelta
    
    if request.method == 'GET':
        # GET: Return sales data with proper date filtering
        
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
            # This Week = Last 7 days from today
            week_start = now - timedelta(days=6)  # 6 days ago + today = 7 days
            week_start_str = week_start.strftime('%Y-%m-%d')
            week_end_str = now.strftime('%Y-%m-%d')
            date_condition = "DATE(s.created_at) BETWEEN ? AND ?"
            params = [week_start_str, week_end_str]
            print(f"🔍 [SALES API] Week filter (Last 7 days): {week_start_str} to {week_end_str}")
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
        sales = conn.execute(f"""SELECT 
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
            LIMIT ?""", params + [limit]).fetchall()
        
        # Get summary statistics - separate sales and revenue
        summary = conn.execute(f"""SELECT 
                COUNT(DISTINCT s.bill_id) as total_bills,
                COUNT(*) as total_items,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(CASE 
                    WHEN b.payment_status = 'paid' OR b.is_credit = 0 THEN s.total_price
                    WHEN b.payment_status = 'partial' THEN (s.total_price * b.credit_paid_amount / b.total_amount)
                    ELSE 0 
                END), 0) as total_revenue,
                COALESCE(SUM(s.quantity), 0) as total_quantity,
                COALESCE(AVG(s.unit_price), 0) as avg_unit_price,
                COALESCE(SUM(s.total_price - (p.cost * s.quantity)), 0) as total_profit
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            LEFT JOIN bills b ON s.bill_id = b.id
            WHERE {date_condition}""", params).fetchone()
        
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
            
            # Handle different field names from frontend
            # Frontend sends 'total', backend expects 'total_amount'
            if data.get('total') and not data.get('total_amount'):
                data['total_amount'] = data['total']
            
            # Frontend sends 'cgst' and 'sgst', backend expects 'tax_amount'
            if not data.get('tax_amount'):
                cgst = data.get('cgst', 0)
                sgst = data.get('sgst', 0)
                data['tax_amount'] = cgst + sgst
            
            # Set default values if missing
            if not data.get('total_amount'):
                data['total_amount'] = 100.0  # Default to avoid error
            if not data.get('subtotal'):
                data['subtotal'] = data.get('total_amount', 100.0)
            if not data.get('business_type'):
                data['business_type'] = 'retail'
            
            print(f"📝 [SALES API] Using total_amount: {data['total_amount']}")
            
            # Get current time for all operations
            current_time = datetime.now()
            
            conn = get_db_connection()
            
            # Generate bill details
            bill_id = generate_id()
            bill_number = f"BILL-{current_time.strftime('%Y%m%d')}-{bill_id[:8]}"
            
            # Handle customer creation if name provided (use separate connection)
            customer_id = data.get('customer_id')
            customer_name = data.get('customer_name', 'Walk-in Customer')
            customer_phone = data.get('customer_phone')
            
            # Create customer if name provided and not exists
            if customer_name and customer_name != 'Walk-in Customer' and not customer_id:
                try:
                    # Use separate connection for customer operations
                    customer_conn = get_db_connection()
                    
                    # Check if customer exists by phone
                    if customer_phone:
                        existing_customer = customer_conn.execute(
                            'SELECT id FROM customers WHERE phone = ?', (customer_phone,)
                        ).fetchone()
                        if existing_customer:
                            customer_id = existing_customer['id']
                    
                    # Create new customer if not found
                    if not customer_id:
                        customer_id = generate_id()
                        customer_conn.execute("""INSERT INTO customers (id, name, phone, created_at)
                            VALUES (?, ?, ?, ?)""", (customer_id, customer_name, customer_phone, current_time.strftime('%Y-%m-%d %H:%M:%S')))
                        customer_conn.commit()
                        print(f"📝 [SALES API] Created new customer: {customer_name}")
                    
                    customer_conn.close()
                    
                except Exception as e:
                    print(f"⚠️ [SALES API] Customer creation failed: {str(e)}")
                    # Continue without customer_id
                    customer_id = None
            
            # Start transaction for bill creation
            conn.execute('BEGIN TRANSACTION')
            
            try:
                # Create bill record with timestamp and proper payment handling
                bill_timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine payment status based on payment method
                payment_method = data.get('payment_method', 'cash')
                is_credit = payment_method == 'credit' or data.get('is_credit', False)
                
                if is_credit:
                    payment_status = 'pending'
                    credit_amount = data['total_amount']
                    credit_paid_amount = 0
                    credit_balance = data['total_amount']
                    credit_due_date = data.get('credit_due_date')
                else:
                    payment_status = 'paid'
                    credit_amount = 0
                    credit_paid_amount = data['total_amount']
                    credit_balance = 0
                    credit_due_date = None
                
                conn.execute("""INSERT INTO bills (
                        id, bill_number, customer_id, customer_name, business_type, 
                        subtotal, tax_amount, discount_amount, total_amount, 
                        payment_status, payment_method, is_credit, 
                        credit_amount, credit_paid_amount, credit_balance, credit_due_date,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    bill_id, bill_number, customer_id, customer_name,
                    data.get('business_type', 'retail'),
                    data.get('subtotal', 0), data.get('tax_amount', 0), 
                    data.get('discount_amount', 0), data['total_amount'],
                    payment_status, payment_method, is_credit,
                    credit_amount, credit_paid_amount, credit_balance, credit_due_date,
                    'completed', bill_timestamp
                ))
                
                # Get customer name if exists
                if customer_id and not customer_name:
                    customer = conn.execute('SELECT name FROM customers WHERE id = ?', (customer_id,)).fetchone()
                    customer_name = customer['name'] if customer else 'Walk-in Customer'
                
                # Process each item
                for item in data['items']:
                    # Handle different field names from frontend
                    # Frontend sends: id, name, price
                    # Backend expects: product_id, product_name, unit_price
                    product_id = item.get('product_id') or item.get('id') or 'default-product'
                    product_name = item.get('product_name') or item.get('name') or 'Unknown Product'
                    quantity = item.get('quantity', 1)
                    unit_price = item.get('unit_price') or item.get('price', 0)
                    total_price = item.get('total_price') or (unit_price * quantity)
                    
                    # Create bill item
                    item_id = generate_id()
                    conn.execute("""INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price, tax_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
                        item_id, bill_id, product_id, product_name,
                        quantity, unit_price, total_price, 
                        item.get('tax_rate', 18)
                    ))
                    
                    # Update product stock - skip if default
                    if product_id != 'default-product':
                        conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
                    
                    # Get product details for sales entry
                    product = None
                    if product_id != 'default-product':
                        product = conn.execute("SELECT category, cost FROM products WHERE id = ?", (product_id,)).fetchone()
                    
                    # Create sales entry
                    sale_id = generate_id()
                    sale_date_str = current_time.strftime('%Y-%m-%d')
                    sale_time_str = current_time.strftime('%H:%M:%S')
                    
                    # Calculate proportional tax and discount for this item
                    subtotal = data.get('subtotal', data['total_amount'])
                    item_tax = (total_price / subtotal) * data.get('tax_amount', 0) if subtotal > 0 else 0
                    item_discount = (total_price / subtotal) * data.get('discount_amount', 0) if subtotal > 0 else 0
                    
                    conn.execute("""INSERT INTO sales (
                            id, bill_id, bill_number, customer_id, customer_name,
                            product_id, product_name, category, quantity, unit_price,
                            total_price, tax_amount, discount_amount, payment_method,
                            sale_date, sale_time, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        sale_id, bill_id, bill_number, customer_id, customer_name,
                        product_id, product_name, 
                        product['category'] if product else 'General',
                        quantity, unit_price, total_price,
                        item_tax, item_discount, data.get('payment_method', 'cash'),
                        sale_date_str, sale_time_str, bill_timestamp
                    ))
                
                # Add payment record
                payment_method = data.get('payment_method', 'cash')
                if payment_method:
                    payment_id = generate_id()
                    
                    # For credit bills, set paid amount to 0 and create balance due
                    if payment_method == 'credit':
                        paid_amount = 0
                        balance_due = data['total_amount']
                        
                        # Add balance_due to sales records for credit tracking
                        conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                            WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                        
                        # Create payment record with 0 amount for credit
                        conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                            VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, bill_timestamp))
                        
                        print(f"💳 [SALES API] Credit bill created: {bill_number} - Amount: ₹{data['total_amount']}")
                    else:
                        # Regular payment - full amount paid
                        paid_amount = data['total_amount']
                        balance_due = 0
                        
                        # Update sales records
                        conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                            WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                        
                        # Create payment record
                        conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                            VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, bill_timestamp))
                
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
    """Get all sales entries with proper date filtering and bill grouping"""
    from datetime import datetime, timedelta
    
    # Get filter parameters
    date_filter = request.args.get('filter', '')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    category = request.args.get('category', 'all')
    payment_method = request.args.get('payment_method', 'all')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 15))  # 15 records per page
    
    # Get current date in local time
    now = datetime.now()
    
    # Validate and set date range
    if date_filter == 'today':
        start_date = now.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_filter == 'yesterday':
        yesterday = now - timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = start_date
    elif date_filter == 'week':
        # This Week = Last 7 days from today
        week_start = now - timedelta(days=6)  # 6 days ago + today = 7 days
        start_date = week_start.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
        print(f"🔍 [SALES ALL API] Week filter (Last 7 days): {start_date} to {end_date}")
    elif date_filter == 'month':
        month_start = now.replace(day=1)
        start_date = month_start.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    elif date_filter == 'all':
        # Get all data - set a very wide date range
        start_date = '2020-01-01'  # Far back start date
        end_date = now.strftime('%Y-%m-%d')  # Today as end date
    elif date_filter == 'custom':
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "Custom filter requires startDate and endDate"}), 400
    else:
        if not start_date or not end_date:
            return jsonify({"success": False, "error": "Missing startDate or endDate parameters"}), 400
    
    # Validate date format and range
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if start_dt > end_dt:
            return jsonify({"success": False, "error": "startDate cannot be greater than endDate"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    conn = get_db_connection()
    
    # First, get grouped bills (one row per bill with product list)
    bills_query = '''
        SELECT 
            s.bill_id,
            s.bill_number,
            s.customer_id,
            s.customer_name,
            s.payment_method,
            s.sale_date as date,
            s.sale_time as time,
            s.created_at,
            COUNT(s.id) as total_items,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_amount,
            SUM(s.tax_amount) as tax_amount,
            SUM(s.discount_amount) as discount_amount,
            MAX(s.paid_amount) as paid_amount,
            MAX(s.balance_due) as balance_due,
            GROUP_CONCAT(s.product_name || ' (' || s.quantity || 'x)', ', ') as product_list,
            SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)) as profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
    '''
    
    params = [start_date, end_date]
    
    # Add category filter
    if category != 'all':
        bills_query += ' AND s.category = ?'
        params.append(category)
    
    # Add payment method filter
    if payment_method != 'all':
        bills_query += ' AND s.payment_method = ?'
        params.append(payment_method)
    
    bills_query += '''
        GROUP BY s.bill_id, s.bill_number, s.customer_id, s.customer_name, 
                 s.payment_method, s.sale_date, s.sale_time, s.created_at
        ORDER BY s.created_at DESC
    '''
    
    # Get total count for pagination
    count_query = f"""SELECT COUNT(DISTINCT s.bill_id) as total_bills
        FROM sales s
        WHERE DATE(s.created_at) BETWEEN ? AND ?"""
    count_params = [start_date, end_date]
    
    if category != 'all':
        count_query += ' AND s.category = ?'
        count_params.append(category)
    
    if payment_method != 'all':
        count_query += ' AND s.payment_method = ?'
        count_params.append(payment_method)
    
    total_bills = conn.execute(count_query, count_params).fetchone()['total_bills']
    
    # Add pagination
    offset = (page - 1) * per_page
    bills_query += f' LIMIT {per_page} OFFSET {offset}'
    
    bills = conn.execute(bills_query, params).fetchall()
    
    # Convert to list of dicts and add serial numbers
    bills_list = []
    for i, bill in enumerate(bills):
        bill_dict = dict(bill)
        bill_dict['serial_no'] = offset + i + 1  # Serial number with pagination
        bills_list.append(bill_dict)
    
    # Get summary statistics with separate net profit and receivable profit
    summary_query = '''
        SELECT 
            COUNT(DISTINCT s.bill_id) as total_bills,
            COUNT(*) as total_items,
            COALESCE(SUM(s.quantity), 0) as total_quantity,
            COALESCE(SUM(s.total_price), 0) as total_sales,
            COALESCE(SUM(s.tax_amount), 0) as total_tax,
            COALESCE(SUM(s.discount_amount), 0) as total_discount,
            COALESCE(AVG(s.total_price), 0) as avg_sale_value,
            COALESCE(SUM(CASE 
                WHEN b.payment_status = 'paid' OR b.is_credit = 0 
                THEN (s.total_price - (COALESCE(p.cost, 0) * s.quantity))
                WHEN b.payment_status = 'partial' 
                THEN ((s.total_price - (COALESCE(p.cost, 0) * s.quantity)) * b.credit_paid_amount / b.total_amount)
                ELSE 0 
            END), 0) as net_profit,
            COALESCE(SUM(CASE 
                WHEN b.payment_status = 'pending' OR (b.is_credit = 1 AND b.payment_status != 'paid')
                THEN (s.total_price - (COALESCE(p.cost, 0) * s.quantity))
                WHEN b.payment_status = 'partial' 
                THEN ((s.total_price - (COALESCE(p.cost, 0) * s.quantity)) * b.credit_balance / b.total_amount)
                ELSE 0 
            END), 0) as receivable_profit,
            COALESCE(SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)), 0) as total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.id
        LEFT JOIN bills b ON s.bill_id = b.id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
    '''
    
    summary_params = [start_date, end_date]
    
    if category != 'all':
        summary_query += ' AND s.category = ?'
        summary_params.append(category)
    
    if payment_method != 'all':
        summary_query += ' AND s.payment_method = ?'
        summary_params.append(payment_method)
    
    summary = conn.execute(summary_query, summary_params).fetchone()
    
    conn.close()
    
    # Calculate pagination info
    total_pages = (total_bills + per_page - 1) // per_page
    
    return jsonify({
        'success': True,
        'bills': bills_list,  # Changed from 'sales' to 'bills' for clarity
        'summary': dict(summary) if summary else {},
        'pagination': {
            'current_page': page,
            'per_page': per_page,
            'total_records': total_bills,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        'filters': {
            'filter': date_filter,
            'startDate': start_date,
            'endDate': end_date,
            'category': category,
            'payment_method': payment_method,
            'page': page,
            'per_page': per_page
        },
        'debug_info': {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'query_dates': f"{start_date} to {end_date}"
        }
    })

@app.route('/api/sales/by-product', methods=['GET'])
def get_sales_by_product():
    """Get sales grouped by product"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    product_sales = conn.execute("""SELECT 
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
        ORDER BY total_sales DESC""", (date_from, date_to)).fetchall()
    
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
    
    category_sales = conn.execute("""SELECT 
            s.category,
            COUNT(DISTINCT s.bill_id) as transactions,
            COUNT(DISTINCT s.product_id) as unique_products,
            SUM(s.quantity) as total_quantity,
            SUM(s.total_price) as total_sales,
            AVG(s.total_price) as avg_sale_value
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.category
        ORDER BY total_sales DESC""", (date_from, date_to)).fetchall()
    
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
    
    customer_sales = conn.execute("""SELECT 
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
        ORDER BY total_sales DESC""", (date_from, date_to)).fetchall()
    
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
    
    daily_summary = conn.execute("""SELECT 
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
        ORDER BY s.sale_date DESC""", (date_from, date_to)).fetchall()
    
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
        from io import StringIO
        from datetime import datetime, timedelta
        import sqlite3
        
        # Get filters - updated to match the frontend
        filter_type = request.args.get('filter', 'today')  # today, yesterday, week, month, all, custom
        payment_method = request.args.get('payment_method', 'all')
        export_format = request.args.get('format', 'csv')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        # Get current date
        now = datetime.now()
        
        # Build date filter based on filter type
        if filter_type == 'today':
            date_start = now.strftime('%Y-%m-%d')
            date_end = date_start
        elif filter_type == 'yesterday':
            yesterday = now - timedelta(days=1)
            date_start = yesterday.strftime('%Y-%m-%d')
            date_end = date_start
        elif filter_type == 'week':
            # Last 7 days from today
            week_start = now - timedelta(days=6)
            date_start = week_start.strftime('%Y-%m-%d')
            date_end = now.strftime('%Y-%m-%d')
        elif filter_type == 'month':
            month_start = now.replace(day=1)
            date_start = month_start.strftime('%Y-%m-%d')
            date_end = now.strftime('%Y-%m-%d')
        elif filter_type == 'all':
            date_start = '2020-01-01'  # Far back start date
            date_end = now.strftime('%Y-%m-%d')
        elif filter_type == 'custom' and start_date and end_date:
            date_start = start_date
            date_end = end_date
        else:
            # Default to today
            date_start = now.strftime('%Y-%m-%d')
            date_end = date_start
        
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Ensure we get dict-like rows
        
        # Get ALL sales data for export (no pagination limits)
        query = '''
            SELECT 
                s.bill_id,
                s.bill_number,
                s.customer_name,
                s.payment_method,
                s.sale_date,
                DATE(s.created_at) as created_date,
                s.created_at,
                SUM(s.total_price) as total_amount,
                COUNT(s.id) as total_items,
                SUM(s.quantity) as total_quantity
            FROM sales s
            WHERE DATE(s.created_at) BETWEEN ? AND ?
        '''
        
        params = [date_start, date_end]
        
        # Add payment method filter
        if payment_method != 'all':
            query += ' AND s.payment_method = ?'
            params.append(payment_method)
        
        query += '''
            GROUP BY s.bill_id, s.bill_number, s.customer_name, 
                     s.payment_method, s.sale_date, s.created_at
            ORDER BY s.created_at DESC
        '''
        
        # NO LIMIT - Export ALL data for the filter
        sales = conn.execute(query, params).fetchall()
        
        # Debug: Print query and results
        print(f"🔍 [SALES EXPORT] Date Range: {date_start} to {date_end}")
        print(f"🔍 [SALES EXPORT] Filter: {filter_type}")
        print(f"🔍 [SALES EXPORT] Payment Method: {payment_method}")
        print(f"🔍 [SALES EXPORT] Results count: {len(sales)}")
        if sales:
            print(f"🔍 [SALES EXPORT] First result: {dict(sales[0])}")
            print(f"🔍 [SALES EXPORT] Last result: {dict(sales[-1])}")
        
        # If no results, try a simpler query to get ALL data without date filter
        if not sales:
            print("🔍 [SALES EXPORT] No results with date filter, trying without date filter...")
            simple_query = '''
                SELECT 
                    s.bill_id,
                    s.bill_number,
                    s.customer_name,
                    s.payment_method,
                    s.sale_date,
                    DATE(s.created_at) as created_date,
                    s.created_at,
                    SUM(s.total_price) as total_amount,
                    COUNT(s.id) as total_items,
                    SUM(s.quantity) as total_quantity
                FROM sales s
                GROUP BY s.bill_id, s.bill_number, s.customer_name, 
                         s.payment_method, s.sale_date, s.created_at
                ORDER BY s.created_at DESC
            '''
            
            sales = conn.execute(simple_query).fetchall()
            print(f"🔍 [SALES EXPORT] Without date filter: {len(sales)} results")
        
        # If still no results, check if sales table has any data
        if not sales:
            total_count = conn.execute("SELECT COUNT(*) as count FROM sales").fetchone()
            print(f"🔍 [SALES EXPORT] Total sales in DB: {total_count['count']}")
            
            if total_count['count'] == 0:
                print("🔍 [SALES EXPORT] Database is empty - creating sample data message")
                # Create a message row indicating no data
                sales = [{
                    'bill_id': 'NO-DATA',
                    'bill_number': 'NO-DATA', 
                    'customer_name': f'No sales found for {filter_type} filter',
                    'payment_method': 'N/A',
                    'date': date_start,
                    'created_at': f'{date_start} 00:00:00',
                    'total_amount': 0.00,
                    'total_items': 0,
                    'total_quantity': 0
                }]
        
        conn.close()
        
        if export_format == 'whatsapp':
            # Create WhatsApp message
            total_amount = sum(sale['total_amount'] for sale in sales)
            total_bills = len(sales)
            
            message = ("📊 *Sales Report - " + filter_type.title() + "*\n"
                      "📅 Period: " + date_start + " to " + date_end + "\n\n"
                      "📈 *Summary:*\n"
                      "• Total Bills: " + str(total_bills) + "\n"
                      "• Total Amount: ₹" + f"{total_amount:,.2f}" + "\n\n"
                      "Generated: " + datetime.now().strftime('%d/%m/%Y %I:%M %p') + "\n\n"
                      "🏪 *BizPulse ERP*")
            
            return message
        
        # Create CSV export
        output = StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Write header
        writer.writerow([
            'Bill Number', 'Date', 'Customer Name', 'Total Amount', 
            'Items', 'Quantity', 'Payment Method'
        ])
        
        # Write data - ALL transactions for the selected filter
        if not sales:
            # If no sales data, add just ONE message row (not many empty rows)
            # Format date range for display
            try:
                start_obj = datetime.strptime(date_start, '%Y-%m-%d')
                end_obj = datetime.strptime(date_end, '%Y-%m-%d')
                date_range = f"{start_obj.strftime('%d/%m/%Y')} to {end_obj.strftime('%d/%m/%Y')}"
            except:
                date_range = f'{date_start} to {date_end}'
                
            writer.writerow([
                'No Data', 
                date_range, 
                f'No sales found for {filter_type} filter', 
                '0.00', 
                '0', 
                '0', 
                'N/A'
            ])
        else:
            print(f"🔍 [SALES EXPORT] Writing {len(sales)} rows to CSV")
            successful_rows = 0
            
            for i, sale in enumerate(sales):
                try:
                    # Convert row to dict if it's not already
                    if hasattr(sale, 'keys'):
                        sale_dict = dict(sale)
                    else:
                        sale_dict = sale
                    
                    # Debug first row
                    if i == 0:
                        print(f"🔍 [SALES EXPORT] First row data: {sale_dict}")
                    
                    # Get date with better formatting - prioritize created_date over sale_date
                    sale_date = None
                    
                    # Try different date fields in order of preference
                    if sale_dict.get('created_date'):
                        sale_date = str(sale_dict['created_date'])
                    elif sale_dict.get('sale_date'):
                        sale_date = str(sale_dict['sale_date'])
                    elif sale_dict.get('created_at'):
                        created_at = str(sale_dict['created_at'])
                        # Extract just the date part (YYYY-MM-DD)
                        if ' ' in created_at:
                            sale_date = created_at.split(' ')[0]
                        else:
                            sale_date = created_at[:10]
                    
                    # If still no date, use filter date
                    if not sale_date or sale_date == 'None' or sale_date == 'NULL':
                        sale_date = date_start
                    
                    # Ensure date is in Excel-friendly format (YYYY-MM-DD)
                    try:
                        # Parse and reformat date to ensure consistency and Excel compatibility
                        from datetime import datetime
                        if len(sale_date) >= 10:
                            # Parse the date (assuming YYYY-MM-DD format from database)
                            date_obj = datetime.strptime(sale_date[:10], '%Y-%m-%d')
                            # Keep as YYYY-MM-DD format for Excel compatibility (avoids #### width issues)
                            sale_date = date_obj.strftime('%Y-%m-%d')
                        else:
                            # If date is short, try to parse it as is
                            date_obj = datetime.strptime(date_start, '%Y-%m-%d')
                            sale_date = date_obj.strftime('%Y-%m-%d')
                    except Exception as date_error:
                        print(f"⚠️ [SALES EXPORT] Date parsing error for '{sale_date}': {date_error}")
                        # Fallback to filter date in YYYY-MM-DD format
                        try:
                            date_obj = datetime.strptime(date_start, '%Y-%m-%d')
                            sale_date = date_obj.strftime('%Y-%m-%d')
                        except:
                            sale_date = date_start  # Last resort
                    
                    # Debug first few rows to see date issues
                    if i < 3:
                        print(f"🔍 [SALES EXPORT] Row {i+1} date fields:")
                        print(f"   - date: {sale_dict.get('date')}")
                        print(f"   - sale_date: {sale_dict.get('sale_date')}")
                        print(f"   - created_at: {sale_dict.get('created_at')}")
                        print(f"   - final sale_date: {sale_date}")
                    
                    # Get values with proper fallbacks
                    bill_number = sale_dict.get('bill_number') or sale_dict.get('bill_id') or f'BILL-{i+1}'
                    customer_name = sale_dict.get('customer_name') or 'Walk-in Customer'
                    total_amount = float(sale_dict.get('total_amount') or 0)
                    total_items = int(sale_dict.get('total_items') or 0)
                    total_quantity = int(sale_dict.get('total_quantity') or 0)
                    payment_method = sale_dict.get('payment_method') or 'Cash'
                    
                    writer.writerow([
                        bill_number,
                        sale_date,
                        customer_name,
                        f"{total_amount:.2f}",
                        total_items,
                        total_quantity,
                        payment_method
                    ])
                    successful_rows += 1
                    
                except Exception as row_error:
                    print(f"❌ [SALES EXPORT] Row {i+1} error: {row_error}")
                    print(f"❌ [SALES EXPORT] Problem row type: {type(sale)}")
                    print(f"❌ [SALES EXPORT] Problem row: {sale}")
                    
                    # Only add error row if we have less than 5 errors (limit error rows)
                    if (len(sales) - successful_rows) <= 5:
                        writer.writerow([f'ERROR-ROW-{i+1}', date_start, 'Data processing error', '0.00', '0', '0', 'ERROR'])
            
            print(f"✅ [SALES EXPORT] Successfully wrote {successful_rows} out of {len(sales)} rows")
        
        # Create response with UTF-8 BOM for better Excel compatibility
        output.seek(0)
        csv_data = output.getvalue()
        
        # Add UTF-8 BOM for Excel compatibility
        csv_data_with_bom = '\ufeff' + csv_data
        
        response = make_response(csv_data_with_bom)
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename="sales_export_{filter_type}_{date_start}.csv"'
        response.headers['Cache-Control'] = 'no-cache'
        
        return response
        
    except Exception as e:
        print(f"❌ [SALES EXPORT] Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sales/payment-methods', methods=['GET'])
def get_sales_by_payment_method():
    """Get sales breakdown by payment method"""
    date_from = request.args.get('from', datetime.now().strftime('%Y-%m-%d'))
    date_to = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    payment_breakdown = conn.execute("""SELECT 
            s.payment_method,
            COUNT(DISTINCT s.bill_id) as transactions,
            SUM(s.total_price) as total_amount,
            AVG(s.total_price) as avg_transaction_value
        FROM sales s
        WHERE s.sale_date BETWEEN ? AND ?
        GROUP BY s.payment_method
        ORDER BY total_amount DESC""", (date_from, date_to)).fetchall()
    
    conn.close()
    
    return jsonify({
        'payment_breakdown': [dict(row) for row in payment_breakdown],
        'date_range': {
            'from': date_from,
            'to': date_to
        }
    })

# ============================================================================
# CREDIT MANAGEMENT MODULE - Premium Credit Tracking System
# ============================================================================

@app.route('/api/credit/summary', methods=['GET'])
@require_auth
def get_credit_summary():
    """Get comprehensive credit summary with outstanding amounts and analytics"""
    try:
        conn = get_db_connection()
        
        # Total outstanding credit amount
        total_outstanding = conn.execute("""SELECT COALESCE(SUM(credit_balance), 0) as total
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial') AND credit_balance > 0""").fetchone()['total']
        
        # Number of customers with outstanding credit
        customers_with_credit = conn.execute("""SELECT COUNT(DISTINCT customer_id) as count
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial') AND credit_balance > 0""").fetchone()['count']
        
        # Total credit bills count
        total_credit_bills = conn.execute("""SELECT COUNT(*) as count
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial')""").fetchone()['count']
        
        # Total credit sales amount
        total_credit_sales = conn.execute("""SELECT COALESCE(SUM(total_amount), 0) as total
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial')""").fetchone()['total']
        
        # Total received amount (payments made on credit bills)
        total_received = conn.execute("""SELECT COALESCE(SUM(total_amount - credit_balance), 0) as total
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial')""").fetchone()['total']
        
        # Overdue credit bills (past due date)
        overdue_bills = conn.execute("""SELECT COUNT(*) as count, COALESCE(SUM(credit_balance), 0) as amount
            FROM bills 
            WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial') AND credit_balance > 0 
            AND credit_due_date < DATE('now')""").fetchone()
        
        # Credit collection this month
        current_month = datetime.now().strftime('%Y-%m')
        monthly_collections = conn.execute("""SELECT COALESCE(SUM(amount), 0) as total
            FROM credit_transactions 
            WHERE transaction_type = 'payment' 
            AND strftime('%Y-%m', created_at) = ?""", (current_month,)).fetchone()['total']
        
        # Top customers by outstanding credit
        top_credit_customers = conn.execute("""SELECT 
                c.name as customer_name,
                c.phone,
                SUM(b.credit_balance) as total_outstanding,
                COUNT(b.id) as credit_bills_count,
                MIN(b.credit_due_date) as earliest_due_date
            FROM bills b
            JOIN customers c ON b.customer_id = c.id
            WHERE (b.is_credit = 1 OR b.payment_method = 'credit' OR b.payment_method = 'partial') AND b.credit_balance > 0
            GROUP BY b.customer_id, c.name, c.phone
            ORDER BY total_outstanding DESC
            LIMIT 10""").fetchall()
        
        # Recent credit transactions
        recent_transactions = conn.execute("""SELECT 
                ct.id,
                ct.amount,
                ct.transaction_type,
                ct.payment_method,
                ct.created_at,
                c.name as customer_name,
                b.bill_number
            FROM credit_transactions ct
            JOIN customers c ON ct.customer_id = c.id
            JOIN bills b ON ct.bill_id = b.id
            ORDER BY ct.created_at DESC
            LIMIT 10""").fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "summary": {
                "total_outstanding": float(total_outstanding),
                "customers_with_credit": customers_with_credit,
                "total_credit_bills": total_credit_bills,
                "total_credit_sales": float(total_credit_sales),
                "total_received": float(total_received),
                "overdue_count": overdue_bills['count'],
                "overdue_amount": float(overdue_bills['amount']),
                "monthly_collections": float(monthly_collections)
            },
            "top_customers": [dict(row) for row in top_credit_customers],
            "recent_transactions": [dict(row) for row in recent_transactions],
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Credit summary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/export', methods=['GET'])
@require_auth
def export_credit_bills():
    """Export credit bills data in multiple formats (PDF, Excel, CSV, WhatsApp)"""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Get filters
        status = request.args.get('status', 'all')
        date_range = request.args.get('date_range', 'all')
        customer = request.args.get('customer', 'all')
        export_format = request.args.get('format', 'csv')
        
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # Build query for credit bills (same as credit bills API)
        query = """
        SELECT 
            b.id, b.bill_number, 
            COALESCE(c.name, b.customer_name, 'Walk-in Customer') as customer_name,
            b.total_amount,
            COALESCE(b.credit_paid_amount, 0) as paid_amount,
            COALESCE(b.credit_balance, b.total_amount) as balance_due,
            b.created_at, b.payment_method, b.payment_status,
            b.credit_due_date as due_date,
            CASE 
                WHEN b.payment_method = 'partial' THEN 'Partial Payment'
                WHEN b.credit_balance = 0 THEN 'Paid'
                WHEN b.credit_due_date < DATE('now') AND b.credit_balance > 0 THEN 'Overdue'
                WHEN b.credit_balance > 0 THEN 'Due'
                ELSE 'Due'
            END as status_text
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE (b.is_credit = 1 OR b.payment_method = 'credit' OR b.payment_method = 'partial' OR b.credit_balance > 0)
        """
        params = []
        
        # Apply status filters
        if status == 'pending':
            query += " AND b.credit_paid_amount = 0"
        elif status == 'partial':
            query += " AND b.credit_paid_amount > 0 AND b.credit_balance > 0"
        elif status == 'overdue':
            query += " AND b.credit_due_date < DATE('now') AND b.credit_balance > 0"
        
        # Apply customer filter
        if customer != 'all':
            query += " AND (c.name = ? OR b.customer_name = ?)"
            params.extend([customer, customer])
        
        # Apply date filters
        if date_range == 'today':
            query += " AND DATE(b.created_at) = DATE('now')"
        elif date_range == 'week':
            query += " AND b.created_at >= DATE('now', '-7 days')"
        elif date_range == 'month':
            query += " AND b.created_at >= DATE('now', '-30 days')"
        
        # Order by creation date
        query += " ORDER BY b.created_at DESC LIMIT 1000"
        
        bills = conn.execute(query, params).fetchall()
        conn.close()
        
        if export_format.lower() == 'csv':
            # Create CSV export
            output = StringIO()
            writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Write header
            writer.writerow([
                'Bill Number', 'Date', 'Customer Name', 'Total Amount', 
                'Paid Amount', 'Balance Due', 'Due Date', 'Status', 'Payment Method'
            ])
            
            # Write data
            for bill in bills:
                # Format due date
                due_date = bill['due_date'] if bill['due_date'] else 'Not set'
                if bill['due_date']:
                    try:
                        from datetime import datetime, timedelta
                        created_date = datetime.strptime(bill['created_at'], '%Y-%m-%d %H:%M:%S')
                        due_date = (created_date + timedelta(days=30)).strftime('%Y-%m-%d')
                    except:
                        due_date = 'Not set'
                
                writer.writerow([
                    bill['bill_number'] or bill['id'],
                    bill['created_at'][:10] if bill['created_at'] else 'N/A',  # Date only
                    bill['customer_name'],
                    f"{bill['total_amount']:.2f}",
                    f"{bill['paid_amount']:.2f}",
                    f"{bill['balance_due']:.2f}",
                    due_date,
                    bill['status_text'],
                    bill['payment_method']
                ])
            
            # Create response
            output.seek(0)
            csv_data = output.getvalue()
            
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv; charset=utf-8'
            response.headers['Content-Disposition'] = f'attachment; filename="credit_bills_{date_range}_{status}.csv"'
            response.headers['Cache-Control'] = 'no-cache'
            
            return response
            
        elif export_format.lower() == 'whatsapp':
            # WhatsApp format - return JSON with message
            total_bills = len(bills)
            total_outstanding = sum(bill['balance_due'] for bill in bills)
            total_amount = sum(bill['total_amount'] for bill in bills)
            
            message = ("📋 *Credit Bills Report*\n\n"
                      "📅 Date Range: " + date_range.title() + "\n"
                      "📊 Status Filter: " + status.title() + "\n\n"
                      "📈 *Summary:*\n"
                      "• Total Bills: " + str(total_bills) + "\n"
                      "• Total Amount: ₹" + f"{total_amount:,.2f}" + "\n"
                      "• Outstanding: ₹" + f"{total_outstanding:,.2f}" + "\n"
                      "• Collected: ₹" + f"{total_amount - total_outstanding:,.2f}" + "\n\n"
                      "Generated: " + datetime.now().strftime('%d/%m/%Y %I:%M %p'))
            
            return jsonify({
                "success": True,
                "message": "WhatsApp report generated",
                "whatsapp_message": message,
                "total_bills": total_bills,
                "total_outstanding": total_outstanding
            })
            
        else:
            # For PDF and Excel, return CSV for now (can be enhanced later)
            return export_credit_bills()  # Recursive call with CSV format
            
    except Exception as e:
        print(f"❌ Credit export error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/bills', methods=['GET'])
@require_auth
def get_credit_bills():
    """Get all credit bills with filtering options"""
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        date_range = request.args.get('date_range', 'all')
        customer = request.args.get('customer', 'all')
        
        print(f"🔍 Credit bills API called with filters: status={status}, date_range={date_range}, customer={customer}")
        
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # Base query for credit bills from bills table (more accurate)
        query = """
        SELECT 
            b.id, b.bill_number, 
            COALESCE(c.name, b.customer_name, 'Walk-in Customer') as customer_name,
            b.total_amount,
            COALESCE(b.credit_paid_amount, 0) as paid_amount,
            COALESCE(b.credit_balance, b.total_amount) as balance_due,
            b.created_at, b.payment_method, b.payment_status,
            b.credit_due_date as due_date,
            CASE 
                WHEN b.payment_method = 'partial' THEN 'Partial Payment'
                WHEN b.credit_balance = 0 THEN 'Paid'
                WHEN b.credit_due_date < DATE('now') AND b.credit_balance > 0 THEN 'Overdue'
                WHEN b.credit_balance > 0 THEN 'Due'
                ELSE 'Due'
            END as status_text
        FROM bills b
        LEFT JOIN customers c ON b.customer_id = c.id
        WHERE (b.is_credit = 1 OR b.payment_method = 'credit' OR b.payment_method = 'partial' OR b.credit_balance > 0)
        """
        params = []
        
        # Apply status filters
        if status == 'pending':
            query += " AND b.credit_paid_amount = 0"
        elif status == 'partial':
            query += " AND b.credit_paid_amount > 0 AND b.credit_balance > 0"
        elif status == 'overdue':
            query += " AND b.credit_due_date < DATE('now') AND b.credit_balance > 0"
        
        # Apply customer filter
        if customer != 'all':
            query += " AND (c.name = ? OR b.customer_name = ?)"
            params.extend([customer, customer])
        
        # Apply date filters
        if date_range == 'today':
            query += " AND DATE(b.created_at) = DATE('now')"
        elif date_range == 'yesterday':
            query += " AND DATE(b.created_at) = DATE('now', '-1 day')"
        elif date_range == 'week':
            query += " AND b.created_at >= DATE('now', '-7 days')"
        elif date_range == 'month':
            query += " AND b.created_at >= DATE('now', '-30 days')"
        
        # Order by creation date
        query += " ORDER BY b.created_at DESC"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        bills = cursor.fetchall()
        
        print(f"✅ Found {len(bills)} credit bills")
        
        # Convert to list of dicts and add due dates
        bill_list = []
        for bill in bills:
            bill_dict = dict(bill)
            # Add due date (30 days from creation)
            from datetime import datetime, timedelta
            try:
                created_date = datetime.strptime(bill_dict['created_at'], '%Y-%m-%d %H:%M:%S')
                due_date = created_date + timedelta(days=30)
                bill_dict['due_date'] = due_date.strftime('%Y-%m-%d')
            except:
                bill_dict['due_date'] = None
            bill_list.append(bill_dict)
        
        # Calculate statistics from bills table
        stats_query = """
        SELECT 
            COUNT(*) as total_bills,
            SUM(COALESCE(credit_balance, total_amount)) as pending_amount,
            COUNT(CASE WHEN credit_due_date < DATE('now') AND credit_balance > 0 THEN 1 END) as overdue_bills,
            SUM(total_amount) as total_amount,
            SUM(COALESCE(credit_paid_amount, 0)) as received_amount
        FROM bills 
        WHERE (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial' OR credit_balance > 0)
        """
        
        cursor.execute(stats_query)
        stats = dict(cursor.fetchone())
        
        # Get unique customers with credit bills
        cursor.execute("""
            SELECT DISTINCT COALESCE(c.name, b.customer_name, 'Walk-in Customer') as name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE (b.is_credit = 1 OR b.payment_method = 'credit' OR b.payment_method = 'partial' OR b.credit_balance > 0)
            AND COALESCE(c.name, b.customer_name) IS NOT NULL 
            AND COALESCE(c.name, b.customer_name) != ''
        """)
        customers = [{'id': row[0], 'name': row[0]} for row in cursor.fetchall()]
        
        conn.close()
        
        response_data = {
            "success": True,
            "bills": bill_list,
            "stats": stats,
            "customers": customers
        }
        
        print(f"📤 Returning {len(bill_list)} bills, {len(customers)} customers")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Credit bills error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/bills/debug', methods=['GET'])
def get_credit_bills_debug():
    """Fast debug version of credit bills API without authentication"""
    try:
        # Get query parameters
        date_range = request.args.get('date_range', 'today')
        status = request.args.get('status', 'all')
        customer = request.args.get('customer', 'all')
        
        print(f"🔍 FAST DEBUG: Credit bills API called with date_range={date_range}")
        
        conn = get_db_connection()
        
        # Ultra-fast query - minimal joins, indexed columns only
        query = """
        SELECT 
            id, bill_number, 
            COALESCE(customer_name, 'Walk-in Customer') as customer_name,
            total_amount,
            COALESCE(credit_paid_amount, 0) as paid_amount,
            COALESCE(credit_balance, total_amount) as balance_due,
            created_at, payment_method, payment_status
        FROM bills 
        WHERE is_credit = 1
        """
        
        # Apply date filters using indexed created_at column
        if date_range == 'today':
            query += " AND DATE(created_at) = DATE('now')"
        elif date_range == 'yesterday':
            query += " AND DATE(created_at) = DATE('now', '-1 day')"
        elif date_range == 'week':
            query += " AND created_at >= DATE('now', '-7 days')"
        elif date_range == 'month':
            query += " AND created_at >= DATE('now', '-30 days')"
        
        # Apply status filter
        if status == 'pending':
            query += " AND COALESCE(credit_paid_amount, 0) = 0"
        elif status == 'partial':
            query += " AND COALESCE(credit_paid_amount, 0) > 0 AND COALESCE(credit_balance, total_amount) > 0"
        elif status == 'overdue':
            query += " AND credit_due_date < DATE('now') AND COALESCE(credit_balance, total_amount) > 0"
        
        # Apply customer filter
        if customer != 'all':
            query += " AND customer_name = ?"
        
        query += " ORDER BY created_at DESC LIMIT 100"  # Limit for performance
        
        cursor = conn.cursor()
        if customer != 'all':
            cursor.execute(query, (customer,))
        else:
            cursor.execute(query)
        
        bills = cursor.fetchall()
        
        print(f"✅ FAST DEBUG: Found {len(bills)} credit bills for {date_range}")
        
        # Convert to list of dicts - minimal processing
        bill_list = []
        total_amount = 0
        pending_amount = 0
        received_amount = 0
        
        for bill in bills:
            bill_dict = {
                'id': bill[0],
                'bill_number': bill[1] or bill[0],
                'customer_name': bill[2],
                'total_amount': float(bill[3] or 0),
                'paid_amount': float(bill[4] or 0),
                'balance_due': float(bill[5] or 0),
                'created_at': bill[6],
                'payment_method': bill[7],
                'payment_status': bill[8]
            }
            
            # Calculate stats while iterating (faster than separate queries)
            total_amount += bill_dict['total_amount']
            pending_amount += bill_dict['balance_due']
            received_amount += bill_dict['paid_amount']
            
            bill_list.append(bill_dict)
        
        # Fast stats calculation
        stats = {
            "total_bills": len(bills),
            "pending_amount": pending_amount,
            "total_amount": total_amount,
            "received_amount": received_amount
        }
        
        conn.close()
        
        response_data = {
            "success": True,
            "bills": bill_list,
            "stats": stats,
            "customers": []  # Skip customers for speed
        }
        
        print(f"📤 FAST DEBUG: Returning response with {len(bill_list)} bills")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ FAST DEBUG: Credit bills error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/payment', methods=['POST'])
@require_auth
def record_credit_payment():
    """Record a credit payment received against a bill"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['bill_id', 'amount', 'payment_mode']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        bill_id = data['bill_id']
        payment_amount = float(data['amount'])
        payment_mode = data['payment_mode']  # cash, upi, card, bank_transfer, cheque
        reference_number = data.get('reference_number', '')
        notes = data.get('notes', '')
        received_date = data.get('received_date', datetime.now().strftime('%Y-%m-%d'))
        
        if payment_amount <= 0:
            return jsonify({"success": False, "error": "Payment amount must be greater than 0"}), 400
        
        conn = get_db_connection()
        
        # Get bill details
        bill = conn.execute("""SELECT id, customer_id, credit_balance, credit_paid_amount, bill_number, total_amount
            FROM bills 
            WHERE id = ? AND (is_credit = 1 OR payment_method = 'credit' OR payment_method = 'partial')""", (bill_id,)).fetchone()
        
        if not bill:
            conn.close()
            return jsonify({"success": False, "error": "Credit bill not found"}), 404
        
        current_balance = bill['credit_balance'] or bill['total_amount']
        
        if payment_amount > current_balance:
            conn.close()
            return jsonify({"success": False, "error": f"Payment amount (₹{payment_amount}) exceeds outstanding balance (₹{current_balance})"}), 400
        
        # Record credit transaction
        transaction_id = generate_id()
        conn.execute("""INSERT INTO credit_transactions (
                id, bill_id, customer_id, transaction_type, amount, 
                payment_method, reference_number, notes, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            transaction_id, bill_id, bill['customer_id'], 'received', 
            payment_amount, payment_mode, reference_number, notes, 
            session.get('user_id', 'system'), received_date + ' ' + datetime.now().strftime('%H:%M:%S')
        ))
        
        # Update bill credit balance
        new_balance = current_balance - payment_amount
        new_paid_amount = (bill.get('credit_paid_amount', 0) or 0) + payment_amount
        
        # Determine new payment status
        if new_balance <= 0:
            new_payment_status = 'paid'
        elif new_paid_amount > 0:
            new_payment_status = 'partial'
        else:
            new_payment_status = 'unpaid'
        
        conn.execute("""UPDATE bills 
            SET credit_balance = ?, 
                credit_paid_amount = ?,
                payment_status = ?
            WHERE id = ?""", (new_balance, new_paid_amount, new_payment_status, bill_id))
        
        # Update customer balance if customer exists
        if bill['customer_id']:
            conn.execute("""UPDATE customers 
                SET current_balance = current_balance - ?
                WHERE id = ?""", (payment_amount, bill['customer_id']))
        
        # Update sales records for this bill
        conn.execute("""UPDATE sales 
            SET paid_amount = COALESCE(paid_amount, 0) + ?,
                balance_due = COALESCE(balance_due, total_price) - ?
            WHERE bill_id = ?""", (payment_amount / (bill['total_amount'] or 1) * 100, payment_amount / (bill['total_amount'] or 1) * 100, bill_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Payment of ₹{payment_amount:,.2f} received successfully via {payment_mode.upper()}",
            "transaction_id": transaction_id,
            "bill_number": bill['bill_number'],
            "remaining_balance": round(new_balance, 2),
            "payment_amount": round(payment_amount, 2),
            "payment_mode": payment_mode,
            "payment_status": new_payment_status
        })
        
    except Exception as e:
        print(f"❌ Credit payment receive error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/customer/<customer_id>', methods=['GET'])
@require_auth
def get_customer_credit_history(customer_id):
    """Get complete credit history for a specific customer"""
    try:
        conn = get_db_connection()
        
        # Get customer details
        customer = conn.execute("""SELECT id, name, phone, email, credit_limit, current_balance
            FROM customers 
            WHERE id = ?""", (customer_id,)).fetchone()
        
        if not customer:
            conn.close()
            return jsonify({"success": False, "error": "Customer not found"}), 404
        
        # Get all credit bills for this customer
        credit_bills = conn.execute("""SELECT 
                id, bill_number, total_amount, credit_amount, 
                credit_balance, credit_due_date, created_at,
                CASE 
                    WHEN credit_balance = 0 THEN 'paid'
                    WHEN credit_due_date < DATE('now') AND credit_balance > 0 THEN 'overdue'
                    WHEN credit_balance > 0 THEN 'outstanding'
                    ELSE 'unknown'
                END as status
            FROM bills 
            WHERE customer_id = ? AND is_credit = 1
            ORDER BY created_at DESC""", (customer_id,)).fetchall()
        
        # Get all credit transactions for this customer
        credit_transactions = conn.execute("""SELECT 
                ct.id, ct.amount, ct.transaction_type, ct.payment_method,
                ct.reference_number, ct.notes, ct.created_at,
                b.bill_number
            FROM credit_transactions ct
            JOIN bills b ON ct.bill_id = b.id
            WHERE ct.customer_id = ?
            ORDER BY ct.created_at DESC""", (customer_id,)).fetchall()
        
        # Calculate summary
        total_credit_given = sum(float(bill['credit_amount'] or 0) for bill in credit_bills)
        total_outstanding = sum(float(bill['credit_balance'] or 0) for bill in credit_bills)
        total_paid = total_credit_given - total_outstanding
        
        conn.close()
        
        return jsonify({
            "success": True,
            "customer": dict(customer),
            "summary": {
                "total_credit_given": total_credit_given,
                "total_outstanding": total_outstanding,
                "total_paid": total_paid,
                "credit_bills_count": len(credit_bills)
            },
            "credit_bills": [dict(row) for row in credit_bills],
            "transactions": [dict(row) for row in credit_transactions]
        })
        
    except Exception as e:
        print(f"❌ Customer credit history error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/analytics', methods=['GET'])
@require_auth
def get_credit_analytics():
    """Get credit analytics and insights"""
    try:
        conn = get_db_connection()
        
        # Monthly credit trends (last 12 months)
        monthly_trends = conn.execute("""SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as credit_bills_count,
                SUM(credit_amount) as credit_given,
                SUM(CASE WHEN credit_balance = 0 THEN credit_amount ELSE 0 END) as credit_collected
            FROM bills 
            WHERE is_credit = 1 
            AND created_at >= DATE('now', '-12 months')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY month""").fetchall()
        
        # Credit collection efficiency
        collection_stats = conn.execute("""SELECT 
                COUNT(*) as total_credit_bills,
                COUNT(CASE WHEN credit_balance = 0 THEN 1 END) as fully_paid_bills,
                COUNT(CASE WHEN credit_balance > 0 AND credit_due_date < DATE('now') THEN 1 END) as overdue_bills,
                AVG(CASE WHEN credit_balance = 0 
                    THEN julianday(
                        COALESCE(
                            (SELECT MAX(created_at) FROM credit_transactions 
                             WHERE bill_id = bills.id AND transaction_type = 'payment'), 
                            created_at
                        )
                    ) - julianday(created_at)
                    ELSE NULL 
                END) as avg_collection_days
            FROM bills 
            WHERE is_credit = 1""").fetchone()
        
        # Top credit customers by risk
        risky_customers = conn.execute("""SELECT 
                c.name as customer_name,
                c.phone,
                COUNT(b.id) as overdue_bills_count,
                SUM(b.credit_balance) as total_overdue_amount,
                AVG(julianday('now') - julianday(b.credit_due_date)) as avg_days_overdue
            FROM bills b
            JOIN customers c ON b.customer_id = c.id
            WHERE b.is_credit = 1 
            AND b.credit_balance > 0 
            AND b.credit_due_date < DATE('now')
            GROUP BY b.customer_id, c.name, c.phone
            ORDER BY total_overdue_amount DESC
            LIMIT 10""").fetchall()
        
        # Credit aging analysis
        aging_analysis = conn.execute("""SELECT 
                CASE 
                    WHEN julianday('now') - julianday(credit_due_date) <= 0 THEN 'Current'
                    WHEN julianday('now') - julianday(credit_due_date) <= 30 THEN '1-30 days'
                    WHEN julianday('now') - julianday(credit_due_date) <= 60 THEN '31-60 days'
                    WHEN julianday('now') - julianday(credit_due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket,
                COUNT(*) as bills_count,
                SUM(credit_balance) as total_amount
            FROM bills 
            WHERE is_credit = 1 AND credit_balance > 0
            GROUP BY aging_bucket
            ORDER BY 
                CASE aging_bucket
                    WHEN 'Current' THEN 1
                    WHEN '1-30 days' THEN 2
                    WHEN '31-60 days' THEN 3
                    WHEN '61-90 days' THEN 4
                    ELSE 5
                END""").fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "monthly_trends": [dict(row) for row in monthly_trends],
            "collection_stats": dict(collection_stats) if collection_stats else {},
            "risky_customers": [dict(row) for row in risky_customers],
            "aging_analysis": [dict(row) for row in aging_analysis],
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Credit analytics error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/credit/bill/<bill_id>/payments', methods=['GET'])
@require_auth
def get_bill_payment_history(bill_id):
    """Get payment history for a specific bill"""
    try:
        conn = get_db_connection()
        
        # Get bill details
        bill = conn.execute("""SELECT b.id, b.bill_number, b.total_amount, b.credit_balance, 
                   b.credit_paid_amount, b.payment_status, b.created_at,
                   COALESCE(c.name, b.customer_name, 'Walk-in Customer') as customer_name
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            WHERE b.id = ?""", (bill_id,)).fetchone()
        
        if not bill:
            conn.close()
            return jsonify({"success": False, "error": "Bill not found"}), 404
        
        # Get payment transactions for this bill
        payments = conn.execute("""SELECT id, amount, payment_method, reference_number, notes, created_at
            FROM credit_transactions
            WHERE bill_id = ? AND transaction_type = 'received'
            ORDER BY created_at DESC""", (bill_id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            "success": True,
            "bill": dict(bill),
            "payments": [dict(payment) for payment in payments],
            "total_payments": len(payments),
            "total_received": sum(float(p['amount']) for p in payments)
        })
        
    except Exception as e:
        print(f"❌ Bill payment history error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

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

@app.route('/api/upload/product-image', methods=['POST'])
def upload_product_image():
    """Upload product image"""
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    if file and allowed_file(file.filename):
        # Validate file size (5MB limit)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({"error": "File size must be less than 5MB"}), 400
        
        filename = secure_filename(file.filename)
        # Add timestamp and product prefix to filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"product_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Create upload folder if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(filepath)
        
        # Return public URL
        image_url = f"/static/uploads/{filename}"
        return jsonify({
            "message": "Product image uploaded successfully",
            "image_url": image_url,
            "filename": filename
        }), 200
    
    return jsonify({"error": "Invalid file type. Allowed: png, jpg, jpeg, gif, webp"}), 400

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
        conn.execute("""UPDATE cms_site_settings SET
                site_name = ?,
                logo_url = ?,
                favicon_url = ?,
                primary_color = ?,
                secondary_color = ?,
                contact_email = ?,
                contact_phone = ?,
                address = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (
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
        conn.execute("""INSERT INTO cms_site_settings (
                site_name, logo_url, favicon_url, primary_color, secondary_color,
                contact_email, contact_phone, address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""UPDATE cms_hero_section SET
                title = ?,
                subtitle = ?,
                button_text = ?,
                button_link = ?,
                background_image_url = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (
            data.get('title'),
            data.get('subtitle'),
            data.get('button_text'),
            data.get('button_link'),
            data.get('background_image_url'),
            existing['id']
        ))
    else:
        conn.execute("""INSERT INTO cms_hero_section (title, subtitle, button_text, button_link, background_image_url)
            VALUES (?, ?, ?, ?, ?)""", (
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
    
    conn.execute("""INSERT INTO cms_features (id, title, description, icon_image_url, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""UPDATE cms_features SET
                title = ?,
                description = ?,
                icon_image_url = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?""", (
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
    
    conn.execute("""INSERT INTO cms_pricing_plans (id, name, price_per_month, description, features, is_popular, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        
        conn.execute("""UPDATE cms_pricing_plans SET
                name = ?,
                price_per_month = ?,
                description = ?,
                features = ?,
                is_popular = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?""", (
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
    
    conn.execute("""INSERT INTO cms_testimonials (id, name, role, company, message, avatar_image_url, rating, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""UPDATE cms_testimonials SET
                name = ?,
                role = ?,
                company = ?,
                message = ?,
                avatar_image_url = ?,
                rating = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?""", (
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
    
    conn.execute("""INSERT INTO cms_faqs (id, question, answer, category, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""UPDATE cms_faqs SET
                question = ?,
                answer = ?,
                category = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?""", (
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
    
    conn.execute("""INSERT INTO cms_gallery (id, title, description, image_url, category, display_order, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""UPDATE cms_gallery SET
                title = ?,
                description = ?,
                image_url = ?,
                category = ?,
                display_order = ?,
                is_active = ?
            WHERE id = ?""", (
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
    features = conn.execute("""SELECT * FROM cms_features 
        WHERE is_active = 1 
        ORDER BY display_order, created_at""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in features])

@app.route('/api/cms/pricing', methods=['GET'])
def get_pricing_plans():
    """Get all pricing plans (public)"""
    conn = get_db_connection()
    plans = conn.execute("""SELECT * FROM cms_pricing_plans 
        WHERE is_active = 1 
        ORDER BY display_order, price_per_month""").fetchall()
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
    testimonials = conn.execute("""SELECT * FROM cms_testimonials 
        WHERE is_active = 1 
        ORDER BY display_order, created_at DESC""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in testimonials])

@app.route('/api/cms/faqs', methods=['GET'])
def get_faqs():
    """Get all FAQs (public)"""
    conn = get_db_connection()
    faqs = conn.execute("""SELECT * FROM cms_faqs 
        WHERE is_active = 1 
        ORDER BY display_order, created_at""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in faqs])

@app.route('/api/cms/gallery', methods=['GET'])
def get_gallery():
    """Get all gallery images (public)"""
    category = request.args.get('category', 'all')
    
    conn = get_db_connection()
    
    if category == 'all':
        images = conn.execute("""SELECT * FROM cms_gallery 
            WHERE is_active = 1 
            ORDER BY display_order, created_at DESC""").fetchall()
    else:
        images = conn.execute("""SELECT * FROM cms_gallery 
            WHERE is_active = 1 AND category = ?
            ORDER BY display_order, created_at DESC""", (category,)).fetchall()
    
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
    conn.execute("""UPDATE cms_website_content 
        SET is_active = 0 
        WHERE page_name = ?""", (page_name,))
    
    # Insert new version
    conn.execute("""INSERT INTO cms_website_content (page_name, content_html, edited_by, is_active)
        VALUES (?, ?, ?, 1)""", (page_name, content_html, edited_by))
    
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
    content = conn.execute("""SELECT content_html, edited_by, updated_at 
        FROM cms_website_content 
        WHERE page_name = ? AND is_active = 1
        ORDER BY updated_at DESC
        LIMIT 1""", (page_name,)).fetchone()
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
    admin = conn.execute("""SELECT * FROM cms_admin_users 
        WHERE username = ? AND password_hash = ? AND is_active = 1""", (username, password_hash)).fetchone()
    
    if admin:
        # Update last login
        conn.execute("""UPDATE cms_admin_users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE id = ?""", (admin['id'],))
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
@require_bizpulse_user
def client_management_page():
    """Client Management Interface - BizPulse Users Only"""
    return render_template('client_management.html')

# ============================================================================
# CLIENT MANAGEMENT API ROUTES - For BizPulse Admin
# ============================================================================

@app.route('/api/admin/clients', methods=['GET'])
@require_bizpulse_user
def get_all_clients():
    """Get all clients for admin management"""
    try:
        conn = get_db_connection()
        
        clients = conn.execute("""SELECT 
                id, company_name, contact_name, contact_email, contact_phone,
                business_type, is_active, created_at, updated_at
            FROM clients 
            ORDER BY created_at DESC""").fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'clients': [dict(client) for client in clients]
        })
        
    except Exception as e:
        logger.error(f"Error getting clients: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clients', methods=['POST'])
@require_bizpulse_user
def create_client():
    """Create new client account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['companyName', 'contactName', 'contactEmail', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Check if email already exists
        conn = get_db_connection()
        
        existing = conn.execute(
            'SELECT id FROM clients WHERE contact_email = ?',
            (data['contactEmail'],)
        ).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        
        # Generate client ID
        client_id = f"CLIENT-{uuid.uuid4().hex[:8].upper()}"
        
        # Hash password
        password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Insert client
        conn.execute("""INSERT INTO clients (
                id, company_name, contact_name, contact_email, contact_phone,
                business_type, password_hash, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
            client_id,
            data['companyName'],
            data['contactName'], 
            data['contactEmail'],
            data.get('contactPhone', ''),
            data.get('businessType', 'retail'),
            password_hash,
            1,  # Active by default
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ New client created: {data['companyName']} ({client_id})")
        
        return jsonify({
            'success': True,
            'message': 'Client created successfully',
            'client_id': client_id
        })
        
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/clients/<client_id>', methods=['DELETE'])
@require_bizpulse_user
def delete_client(client_id):
    """Delete client account"""
    try:
        conn = get_db_connection()
        
        # Check if client exists
        client = conn.execute(
            'SELECT company_name FROM clients WHERE id = ?',
            (client_id,)
        ).fetchone()
        
        if not client:
            conn.close()
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        # Delete client
        conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Client deleted: {client['company_name']} ({client_id})")
        
        return jsonify({
            'success': True,
            'message': 'Client deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/login-as-client', methods=['POST'])
@require_bizpulse_user
def login_as_client():
    """Admin login as client (for testing/support)"""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Client ID required'}), 400
        
        conn = get_db_connection()
        
        # Get client details
        client = conn.execute("""SELECT id, company_name, contact_name, contact_email, business_type
            FROM clients 
            WHERE id = ? AND is_active = 1""", (client_id,)).fetchone()
        
        conn.close()
        
        if not client:
            return jsonify({'success': False, 'error': 'Client not found or inactive'}), 404
        
        # Create new session for client
        session.clear()
        session['user_id'] = client['id']
        session['user_type'] = 'client'
        session['user_name'] = client['contact_name']
        session['email'] = client['contact_email']
        session['company_name'] = client['company_name']
        session['business_type'] = client['business_type']
        session['is_super_admin'] = False
        session['logged_in_by_admin'] = True  # Flag to track admin login
        session.permanent = True
        
        logger.info(f"🔑 Admin logged in as client: {client['company_name']} ({client_id})")
        
        return jsonify({
            'success': True,
            'message': f'Logged in as {client["company_name"]}',
            'redirect_url': '/retail/dashboard'
        })
        
    except Exception as e:
        logger.error(f"Error in admin login as client: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    admin = conn.execute("""SELECT * FROM cms_admin_users 
        WHERE id = ? AND password_hash = ?""", (session['cms_admin_id'], current_hash)).fetchone()
    
    if not admin:
        conn.close()
        return jsonify({"success": False, "message": "Current password is incorrect"}), 401
    
    # Update password
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn.execute("""UPDATE cms_admin_users 
        SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?""", (new_hash, session['cms_admin_id']))
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
    conn.execute("""INSERT INTO companies (
            id, business_name, phone_number, whatsapp_number, email, address,
            send_daily_report, report_time, timezone, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
    conn.execute("""UPDATE companies SET
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
        WHERE id = ?""", (
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
        clients = conn.execute("""SELECT id, company_name, contact_email, contact_name, phone_number, 
                   whatsapp_number, business_address, business_type, gst_number,
                   username, is_active, last_login, created_at, updated_at
            FROM clients 
            ORDER BY created_at DESC""").fetchall()
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
def create_client_super_admin():
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
        existing = conn.execute("""SELECT id FROM clients 
            WHERE contact_email = ? OR username = ?""", (data['contact_email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new client
        conn.execute("""INSERT INTO clients (
                id, company_name, contact_email, contact_name, phone_number,
                whatsapp_number, business_address, business_type, gst_number,
                username, password_hash, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        conn.execute("""INSERT INTO companies (
                id, business_name, phone_number, whatsapp_number, email, address,
                send_daily_report, report_time, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
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
        conn.execute("""UPDATE clients SET
                company_name = ?,
                contact_email = ?,
                contact_name = ?,
                phone_number = ?,
                whatsapp_number = ?,
                business_address = ?,
                business_type = ?,
                gst_number = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (
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
        result = conn.execute("""UPDATE clients SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (password_hash, client_id))
        
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
        result = conn.execute("""UPDATE clients SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (is_active, client_id))
        
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
        client = conn.execute("SELECT id, company_name FROM clients WHERE id = ?", (client_id,)).fetchone()
        
        if not client:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Update password
        conn.execute("""UPDATE clients SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (password_hash, client_id))
        
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
        clients = conn.execute("""SELECT id, company_name, contact_email, contact_name, phone_number, 
                   whatsapp_number, business_address, business_type, gst_number,
                   username, is_active, last_login, created_at, updated_at
            FROM clients 
            ORDER BY created_at DESC""").fetchall()
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
        staff = conn.execute("""SELECT id, name, email, phone, role, username, is_active, created_at, updated_at
            FROM staff 
            WHERE business_owner_id = ?
            ORDER BY created_at DESC""", (current_user_id,)).fetchall()
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
        existing = conn.execute("""SELECT id FROM staff 
            WHERE email = ? OR username = ?""", (data['email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new staff member
        conn.execute("""INSERT INTO staff (
                id, business_owner_id, name, email, phone, role, username, password_hash, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        result = conn.execute("""UPDATE staff SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND business_owner_id = ?""", (is_active, staff_id, current_user_id))
        
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
        staff = conn.execute("SELECT id, name FROM staff WHERE id = ? AND business_owner_id = ?", (staff_id, current_user_id)).fetchone()
        
        if not staff:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Staff member not found or access denied'
            }), 404
        
        # Update password
        conn.execute("""UPDATE staff SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (password_hash, staff_id))
        
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
        clients = conn.execute("""SELECT company_name, contact_email, contact_name, phone_number,
                   whatsapp_number, business_type, username, 
                   CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
                   created_at
            FROM clients 
            ORDER BY created_at DESC""").fetchall()
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
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
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
        client = conn.execute("""SELECT id, company_name, contact_email, contact_name, phone_number,
                   whatsapp_number, business_type, username, is_active,
                   created_at, last_login, updated_at
            FROM clients 
            WHERE id = ?""", (client_id,)).fetchone()
        
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
        users = conn.execute("SELECT * FROM client_users WHERE client_id = ?", (client_id,)).fetchall()
        
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
        users = conn.execute("""SELECT id, full_name, email, username, role, department, phone_number,
                   is_active, last_login, created_at, updated_at
            FROM client_users 
            WHERE client_id = ?
            ORDER BY created_at DESC""", (current_client_id,)).fetchall()
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
        existing = conn.execute("""SELECT id FROM client_users 
            WHERE email = ? OR username = ?""", (data['email'], data['username'])).fetchone()
        
        if existing:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Email or username already exists'
            }), 400
        
        # Insert new user
        conn.execute("""INSERT INTO client_users (
                id, client_id, full_name, email, username, password_hash, password_plain,
                role, department, phone_number, is_active, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
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
        result = conn.execute("""UPDATE client_users SET 
                password_hash = ?,
                password_plain = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?""", (password_hash, new_password, user_id, current_client_id))
        
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
        user = conn.execute("SELECT id, full_name, password_plain FROM client_users WHERE id = ? AND client_id = ?", (user_id, current_user_id)).fetchone()
        
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
        conn.execute("""UPDATE client_users SET 
                password_hash = ?,
                password_plain = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (password_hash, new_password, user_id))
        
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
        conn.execute("""UPDATE client_users SET 
                password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?""", (password_hash, user_id, current_user_id))
        
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
        result = conn.execute("""UPDATE client_users SET 
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND client_id = ?""", (is_active, user_id, current_client_id))
        
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
        user = conn.execute("SELECT id, permissions FROM client_users WHERE id = ? AND client_id = ?", (user_id, current_client_id)).fetchone()
        
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
        user = conn.execute("SELECT id FROM client_users WHERE id = ? AND client_id = ?", (user_id, current_client_id)).fetchone()
        
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
        conn.execute("""UPDATE client_users SET 
                permissions = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (permissions_json, user_id))
        
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
        user = conn.execute("SELECT id, permissions, is_active FROM client_users WHERE id = ?", (user_id,)).fetchone()
        
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

# Client Profile Management API
@app.route('/api/client/profile', methods=['GET'])
@require_auth
def get_client_profile():
    """Get current client's profile information"""
    try:
        # Get current client ID from session
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated or invalid session'
            }), 401
        
        conn = get_db_connection()
        
        # Get client profile data
        client = conn.execute("""SELECT id, company_name, contact_name, contact_email, phone_number, 
                   whatsapp_number, business_address, city, state, pincode, country,
                   business_type, gst_number, pan_number, website, created_at, updated_at
            FROM clients 
            WHERE id = ?""", (current_client_id,)).fetchone()
        
        conn.close()
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client profile not found'
            }), 404
        
        return jsonify({
            'success': True,
            'profile': dict(client)
        })
        
    except Exception as e:
        print(f"❌ [PROFILE API] Error getting profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get profile: {str(e)}'
        }), 500

@app.route('/api/client/profile', methods=['PUT'])
@require_auth
def update_client_profile():
    """Update current client's profile information"""
    try:
        # Get current client ID from session
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated or invalid session'
            }), 401
        
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        conn = get_db_connection()
        
        # Build update query dynamically based on provided fields
        update_fields = []
        update_values = []
        
        # Map frontend field names to database column names
        field_mapping = {
            'full_name': 'contact_name',
            'email': 'contact_email', 
            'phone': 'phone_number',
            'date_of_birth': 'date_of_birth',
            'address': 'business_address',
            'business_name': 'company_name',
            'business_type': 'business_type',
            'gst_number': 'gst_number',
            'pan_number': 'pan_number',
            'business_address': 'business_address',
            'language': 'language',
            'timezone': 'timezone',
            'currency': 'currency',
            'date_format': 'date_format',
            # Legacy field mappings for backward compatibility
            'fullName': 'contact_name',
            'whatsapp': 'whatsapp_number',
            'city': 'city',
            'state': 'state',
            'pincode': 'pincode',
            'country': 'country',
            'storeName': 'company_name',
            'storeType': 'business_type',
            'storeAddress': 'business_address',
            'website': 'website'
        }
        
        # Process each field in the data
        for frontend_field, db_field in field_mapping.items():
            if frontend_field in data:
                update_fields.append(f"{db_field} = ?")
                update_values.append(data[frontend_field])
        
        # Add updated timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if not update_fields:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Execute update
        update_query = f"""UPDATE clients 
            SET {', '.join(update_fields)}
            WHERE id = ?"""
        update_values.append(current_client_id)
        
        conn.execute(update_query, update_values)
        conn.commit()
        
        # Get updated profile data
        updated_client = conn.execute("""SELECT id, company_name, contact_name, contact_email, phone_number, 
                   whatsapp_number, business_address, city, state, pincode, country,
                   business_type, gst_number, pan_number, website, created_at, updated_at
            FROM clients 
            WHERE id = ?""", (current_client_id,)).fetchone()
        
        conn.close()
        
        print(f"✅ [PROFILE API] Profile updated for client {current_client_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': dict(updated_client) if updated_client else None
        })
        
    except Exception as e:
        print(f"❌ [PROFILE API] Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update profile: {str(e)}'
        }), 500

@app.route('/api/client/profile/picture', methods=['POST'])
@require_auth
def upload_profile_picture():
    """Upload profile picture for current client"""
    try:
        # Get current client ID from session
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated or invalid session'
            }), 401
        
        # Check if file was uploaded
        if 'profile_picture' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP files only.'
            }), 400
        
        # Create uploads directory if it doesn't exist
        import os
        upload_dir = os.path.join('static', 'uploads', 'profile_pictures')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{current_client_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        # Update database with file path
        conn = get_db_connection()
        conn.execute("""UPDATE clients 
            SET profile_picture = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (f'/static/uploads/profile_pictures/{filename}', current_client_id))
        conn.commit()
        conn.close()
        
        print(f"✅ [PROFILE API] Profile picture uploaded for client {current_client_id}: {filename}")
        
        return jsonify({
            'success': True,
            'message': 'Profile picture uploaded successfully',
            'profile_picture_url': f'/static/uploads/profile_pictures/{filename}'
        })
        
    except Exception as e:
        print(f"❌ [PROFILE API] Error uploading profile picture: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to upload profile picture: {str(e)}'
        }), 500

@app.route('/api/client/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change client password"""
    try:
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Current password and new password are required'
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'error': 'New password must be at least 6 characters long'
            }), 400
        
        conn = get_db_connection()
        
        # Get current client
        client = conn.execute("SELECT id, password_hash FROM clients WHERE id = ?", (current_client_id,)).fetchone()
        
        if not client:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Verify current password
        if not check_password_hash(client['password_hash'], current_password):
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 400
        
        # Update password
        new_password_hash = generate_password_hash(new_password)
        conn.execute("""UPDATE clients 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?""", (new_password_hash, current_client_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        print(f"Error changing password: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/client/sessions', methods=['GET'])
@require_auth
def get_user_sessions():
    """Get user login sessions"""
    try:
        current_client_id = get_current_client_id()
        if not current_client_id:
            return jsonify({
                'success': False,
                'error': 'Not authenticated'
            }), 401
        
        conn = get_db_connection()
        
        # Get client info with last login
        client = conn.execute("""SELECT contact_name, last_login, login_count, created_at
            FROM clients WHERE id = ?""", (current_client_id,)).fetchone()
        
        conn.close()
        
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        # Create session data
        sessions = [
            {
                'id': 1,
                'device': 'Current Browser',
                'location': 'India',
                'ip_address': request.remote_addr,
                'last_active': client['last_login'] or 'Just now',
                'status': 'Active'
            }
        ]
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total_logins': client['login_count'] or 0,
            'member_since': client['created_at']
        })
        
    except Exception as e:
        print(f"Error getting sessions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
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
        client = conn.execute("""SELECT id, company_name, contact_email, username, password_hash, is_active
            FROM clients 
            WHERE username = ? AND is_active = 1""", (username,)).fetchone()
        
        if client and hash_password(password) == client['password_hash']:
            # Update last login
            conn.execute("UPDATE clients SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (client['id'],))
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
2024-12-11,BILL-001,Rajesh Kumar,2500,Cash,Completed
2024-12-11,BILL-002,Priya Sharma,1800,UPI,Completed
2024-12-10,BILL-003,Amit Singh,3200,Card,Completed
2024-12-10,BILL-004,Sunita Devi,1500,Cash,Completed
2024-12-09,BILL-005,Vikram Patel,2800,UPI,Completed
2024-12-09,BILL-006,Ravi Kumar,2200,UPI,Completed
2024-12-08,BILL-007,Meera Sharma,1900,Cash,Completed`;
                                filename = `sales_report_${today}.csv`;
                            } else if (type === 'products') {
                                csvData = `Product Name,Category,Units Sold,Revenue,Cost,Profit,Performance
Rice (1kg),Groceries,25,2000,1500,500,Excellent
Wheat Flour (1kg),Groceries,18,810,630,180,Good
Cooking Oil (1L),Groceries,12,1800,1560,240,Excellent
Tea Powder (250g),Beverages,15,1800,1500,300,Good
Sugar (1kg),Groceries,20,1100,900,200,Good
Milk (1L),Dairy,30,1800,1650,150,Average
Bread,Bakery,25,625,500,125,Good`;
                                filename = `products_report_${today}.csv`;
                            } else if (type === 'customers') {
                                csvData = `Customer Name,Phone,Total Orders,Total Spent,Average Order,Last Purchase,Status
Rajesh Kumar,+91 9876543210,8,15200,1900,2024-12-11,Active
Priya Sharma,+91 9876543211,5,8500,1700,2024-12-10,Active
Amit Singh,+91 9876543212,3,4200,1400,2024-12-08,Recent
Sunita Devi,+91 9876543213,6,9800,1633,2024-12-09,Active
Vikram Patel,+91 9876543214,4,7200,1800,2024-12-07,Recent
Ravi Kumar,+91 9876543215,2,4400,2200,2024-12-06,Recent`;
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
                current_stats = conn.execute("""SELECT 
                        COUNT(DISTINCT b.id) as total_orders,
                        COALESCE(SUM(b.total_amount), 0) as total_revenue,
                        COALESCE(AVG(b.total_amount), 0) as avg_order_value,
                        COUNT(DISTINCT b.customer_id) as active_customers
                    FROM bills b
                    WHERE DATE(b.created_at) BETWEEN ? AND ?""", (from_date, to_date)).fetchone()
                
                # Products sold count
                products_sold = conn.execute("""SELECT COUNT(DISTINCT bi.product_id) as products_count
                    FROM bill_items bi
                    JOIN bills b ON bi.bill_id = b.id
                    WHERE DATE(b.created_at) BETWEEN ? AND ?""", (from_date, to_date)).fetchone()
                
                # Previous period for comparison
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
                period_days = (to_date_obj - from_date_obj).days + 1
                
                prev_from = (from_date_obj - timedelta(days=period_days)).strftime('%Y-%m-%d')
                prev_to = (from_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                
                prev_stats = conn.execute("""SELECT 
                        COUNT(DISTINCT b.id) as total_orders,
                        COALESCE(SUM(b.total_amount), 0) as total_revenue,
                        COALESCE(AVG(b.total_amount), 0) as avg_order_value,
                        COUNT(DISTINCT b.customer_id) as active_customers
                    FROM bills b
                    WHERE DATE(b.created_at) BETWEEN ? AND ?""", (prev_from, prev_to)).fetchone()
                
                # Calculate changes
                def calculate_change(current, previous):
                    if previous == 0:
                        return 100 if current > 0 else 0
                    return round(((current - previous) / previous) * 100, 1)
                
                revenue_change = calculate_change(current_stats['total_revenue'], prev_stats['total_revenue'])
                orders_change = calculate_change(current_stats['total_orders'], prev_stats['total_orders'])
                customers_change = calculate_change(current_stats['active_customers'], prev_stats['active_customers'])
                
                # Sales trend data
                sales_trend = conn.execute("""SELECT 
                        DATE(created_at) as date,
                        COALESCE(SUM(total_amount), 0) as sales
                    FROM bills
                    WHERE DATE(created_at) BETWEEN ? AND ?
                    GROUP BY DATE(created_at)
                    ORDER BY date""", (from_date, to_date)).fetchall()
                
                # Category breakdown
                category_breakdown = conn.execute("""SELECT 
                        p.category,
                        COALESCE(SUM(bi.total_price), 0) as sales
                    FROM bill_items bi
                    JOIN bills b ON bi.bill_id = b.id
                    JOIN products p ON bi.product_id = p.id
                    WHERE DATE(b.created_at) BETWEEN ? AND ?
                    GROUP BY p.category
                    ORDER BY sales DESC""", (from_date, to_date)).fetchall()
                
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
        products_data = conn.execute("""SELECT 
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
            ORDER BY revenue DESC""", (from_date, to_date)).fetchall()

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
        customers_data = conn.execute("""SELECT 
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
            ORDER BY total_spent DESC""", (from_date, to_date)).fetchall()

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
        sales_data = conn.execute("""SELECT 
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
            ORDER BY b.created_at DESC""", (from_date, to_date)).fetchall()
        
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
        products_data = conn.execute("""SELECT 
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
            ORDER BY "Revenue" DESC""", (from_date, to_date)).fetchall()
        
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
        customers_data = conn.execute("""SELECT 
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
            ORDER BY "Total Spent" DESC""", (from_date, to_date)).fetchall()
        
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
    bills = conn.execute("""SELECT b.*, c.name as customer_name 
        FROM bills b 
        LEFT JOIN customers c ON b.customer_id = c.id 
        ORDER BY b.created_at DESC""").fetchall()
    conn.close()
    return jsonify([dict(row) for row in bills])

@app.route('/api/bills/<bill_id>/items', methods=['GET'])
def get_bill_items(bill_id):
    """Get items for a specific bill - Mobile ERP Style"""
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,)).fetchall()
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
        
        conn = get_db_connection()
        
        # ============================================================================
        # STOCK VALIDATION - Prevent negative stock
        # ============================================================================
        out_of_stock_items = []
        for item in data['items']:
            product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (item['product_id'],)).fetchone()
            
            if not product:
                out_of_stock_items.append(f"❌ Product '{item['product_name']}' not found")
                continue
            
            # Check if stock is sufficient
            if product['stock'] < item['quantity']:
                out_of_stock_items.append(
                    f"❌ {product['name']}: Requested {item['quantity']}, Available {product['stock']}"
                )
            
            # Check if stock would go negative
            if product['stock'] - item['quantity'] < 0:
                out_of_stock_items.append(
                    f"❌ {product['name']}: Cannot reduce stock below 0"
                )
        
        # If any items are out of stock, return error
        if out_of_stock_items:
            conn.close()
            return jsonify({
                "error": "Insufficient stock for some items",
                "out_of_stock_items": out_of_stock_items
            }), 400
        
        # ============================================================================
        # Proceed with bill creation if all stock checks pass
        # ============================================================================
        
        bill_id = generate_id()
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"📝 Generated bill: {bill_number}")
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Create bill record with customer name
            customer_name = data.get('customer_name', 'Walk-in Customer')
            conn.execute("""INSERT INTO bills (id, bill_number, customer_id, customer_name, business_type, subtotal, tax_amount, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                bill_id, 
                bill_number, 
                data.get('customer_id'),
                customer_name,
                data.get('business_type', 'retail'),
                data.get('subtotal', 0), 
                data.get('tax_amount', 0), 
                data.get('total_amount', 0),
                'completed',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Keep the customer_name from data, don't overwrite it
            # If customer_id exists, we can get additional info but keep the name from form
            if data.get('customer_id') and not customer_name:
                customer = conn.execute("SELECT name FROM customers WHERE id = ?", (data.get('customer_id'),)).fetchone()
                if customer:
                    customer_name = customer['name']
            
            # Process each item
            for item in data['items']:
                item_id = generate_id()
                
                # Insert bill item
                conn.execute("""INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                    item_id, 
                    bill_id, 
                    item['product_id'], 
                    item['product_name'],
                    item['quantity'], 
                    item['unit_price'], 
                    item['total_price']
                ))
                
                # Update product stock (SAFE STOCK REDUCTION - Never go below 0)
                result = conn.execute("""UPDATE products SET stock = CASE 
                        WHEN stock - ? >= 0 THEN stock - ?
                        ELSE 0
                    END 
                    WHERE id = ?""", (item['quantity'], item['quantity'], item['product_id']))
                
                # Double check that stock didn't go negative
                updated_product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                
                if updated_product and updated_product['stock'] < 0:
                    # This should never happen due to our validation, but just in case
                    conn.execute("UPDATE products SET stock = 0 WHERE id = ?", (item['product_id'],))
                    print(f"⚠️ WARNING: Stock for {updated_product['name']} was negative, reset to 0")
                
                # Get product details for sales entry
                product = conn.execute("SELECT category FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                
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
                
                conn.execute("""INSERT INTO sales (
                        id, bill_id, bill_number, customer_id, customer_name,
                        product_id, product_name, category, quantity, unit_price,
                        total_price, tax_amount, discount_amount, payment_method,
                        sale_date, sale_time, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                    item['product_id'], item['product_name'], 
                    product['category'] if product else 'General',
                    item['quantity'], item['unit_price'], item['total_price'],
                    item_tax, item_discount, data.get('payment_method', 'cash'),
                    sale_date, sale_time, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            # Add payment record and handle credit bills
            payment_method = data.get('payment_method', 'cash')
            if payment_method:
                payment_id = generate_id()
                
                if payment_method == 'credit':
                    # For credit bills, set paid amount to 0 and create balance due
                    paid_amount = 0
                    balance_due = data.get('total_amount', 0)
                    
                    # Update bills table for credit tracking
                    conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'unpaid',
                               credit_paid_amount = ?, credit_balance = ?
                        WHERE id = ?""", (payment_method, paid_amount, balance_due, bill_id))
                    
                    # Update sales records for credit tracking
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                    
                    # Create payment record with 0 amount for credit
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    print(f"💳 Credit bill created: {bill_number} - Amount: ₹{data.get('total_amount', 0)}")
                    
                elif payment_method == 'partial':
                    # For partial payments, get the partial amount
                    partial_amount = float(data.get('partial_amount', 0))
                    total_amount = data.get('total_amount', 0)
                    balance_due = total_amount - partial_amount
                    
                    print(f"🔍 Partial payment debug:")
                    print(f"   partial_amount from data: {data.get('partial_amount')}")
                    print(f"   parsed partial_amount: {partial_amount}")
                    print(f"   total_amount: {total_amount}")
                    print(f"   calculated balance_due: {balance_due}")
                    
                    # Validate partial amount
                    if partial_amount <= 0:
                        print(f"❌ Invalid partial amount: {partial_amount}")
                        # Set to 0 for credit bill if no valid partial amount
                        partial_amount = 0
                        balance_due = total_amount
                    
                    # Update bills table for partial payment tracking
                    conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'partial',
                               credit_paid_amount = ?, credit_balance = ?
                        WHERE id = ?""", (payment_method, partial_amount, balance_due, bill_id))
                    
                    # Update sales records for partial payment tracking
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, partial_amount, bill_id))
                    
                    # Create payment record with partial amount
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, partial_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    print(f"💰 Partial payment bill created: {bill_number} - Total: ₹{total_amount}, Paid: ₹{partial_amount}, Due: ₹{balance_due}")
                    
                else:
                    # Regular payment - full amount paid
                    paid_amount = data.get('total_amount', 0)
                    balance_due = 0
                    
                    # Update bills table for regular payment
                    conn.execute("""UPDATE bills SET payment_method = ?, payment_status = 'paid'
                        WHERE id = ?""", (payment_method, bill_id))
                    
                    # Update sales records
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                    
                    # Create payment record
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
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
# INVOICES MODULE - PROFESSIONAL INVOICE MANAGEMENT
# ============================================================================

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices with comprehensive filtering and pagination"""
    try:
        # Get query parameters
        status = request.args.get('status', 'all')
        date_filter = request.args.get('date_filter', 'all')
        custom_date = request.args.get('custom_date')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        conn = get_db_connection()
        
        # Base query with payment status calculation
        base_query = '''
            SELECT b.*, 
                   COALESCE(c.name, b.customer_name, 'Walk-in Customer') as customer_name, 
                   c.phone as customer_phone,
                   c.email as customer_email,
                   DATE(b.created_at) as invoice_date,
                   TIME(b.created_at) as invoice_time,
                   COALESCE(b.credit_paid_amount, SUM(p.amount), 0) as paid_amount,
                   COALESCE(b.credit_balance, b.total_amount - COALESCE(SUM(p.amount), 0)) as balance_due,
                   CASE 
                       WHEN b.payment_method = 'partial' THEN 'partial'
                       WHEN COALESCE(b.credit_paid_amount, SUM(p.amount), 0) = 0 THEN 'unpaid'
                       WHEN COALESCE(b.credit_paid_amount, SUM(p.amount), 0) < b.total_amount THEN 'partial'
                       WHEN COALESCE(b.credit_paid_amount, SUM(p.amount), 0) >= b.total_amount THEN 'paid'
                       ELSE 'unpaid'
                   END as payment_status
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN payments p ON b.id = p.bill_id
        '''
        
        # Build WHERE conditions
        conditions = []
        params = []
        
        # Date filtering
        if date_filter == 'today':
            conditions.append("DATE(b.created_at) = DATE('now', 'localtime')")
        elif date_filter == 'yesterday':
            conditions.append("DATE(b.created_at) = DATE('now', 'localtime', '-1 day')")
        elif date_filter == 'week':
            conditions.append("DATE(b.created_at) >= DATE('now', 'localtime', '-7 days')")
        elif date_filter == 'month':
            conditions.append("DATE(b.created_at) >= DATE('now', 'localtime', '-30 days')")
        elif date_filter == 'custom' and custom_date:
            conditions.append("DATE(b.created_at) = ?")
            params.append(custom_date)
        
        # Status filtering (payment status)
        if status != 'all':
            # We'll filter after the GROUP BY since payment_status is calculated
            pass
        
        # Add WHERE clause if conditions exist
        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        
        # Group by bill to aggregate payments
        base_query += ' GROUP BY b.id'
        
        # Add payment status filter after GROUP BY
        if status != 'all':
            base_query += f" HAVING payment_status = '{status}' "
        
        # Order by creation date (newest first)
        base_query += ' ORDER BY b.created_at DESC'
        
        # Get total count for pagination
        count_query = f"SELECT COUNT(*) as total FROM ({base_query})"
        total_count = conn.execute(count_query, params).fetchone()['total']
        
        # Add pagination
        base_query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute main query
        invoices = conn.execute(base_query, params).fetchall()
        
        # Convert to list of dicts with proper formatting
        result = []
        for invoice in invoices:
            invoice_dict = dict(invoice)
            
            # Format dates properly
            if invoice_dict['invoice_date']:
                try:
                    date_obj = datetime.strptime(invoice_dict['invoice_date'], '%Y-%m-%d')
                    invoice_dict['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                    invoice_dict['display_date'] = date_obj.strftime('%d %b %Y')
                except:
                    invoice_dict['formatted_date'] = invoice_dict['invoice_date']
                    invoice_dict['display_date'] = invoice_dict['invoice_date']
            
            # Format time
            if invoice_dict['invoice_time']:
                try:
                    time_obj = datetime.strptime(invoice_dict['invoice_time'], '%H:%M:%S')
                    invoice_dict['formatted_time'] = time_obj.strftime('%I:%M %p')
                except:
                    invoice_dict['formatted_time'] = invoice_dict['invoice_time']
            
            # Ensure payment status is properly set
            if not invoice_dict.get('payment_status'):
                invoice_dict['payment_status'] = 'unpaid'
            
            # Calculate balance due (use the value from query if available)
            paid_amount = invoice_dict.get('paid_amount', 0) or 0
            total_amount = invoice_dict.get('total_amount', 0) or 0
            balance_due = invoice_dict.get('balance_due')
            if balance_due is None:
                invoice_dict['balance_due'] = max(0, total_amount - paid_amount)
            else:
                invoice_dict['balance_due'] = balance_due
            
            # Add status badge color
            status_colors = {
                'paid': 'success',
                'partial': 'warning', 
                'unpaid': 'danger'
            }
            invoice_dict['status_color'] = status_colors.get(invoice_dict['payment_status'], 'secondary')
            
            result.append(invoice_dict)
        
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            'invoices': result,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': total_count,
                'per_page': limit,
                'has_next': page < total_pages,
                'has_prev': page > 1
            },
            'filters': {
                'status': status,
                'date_filter': date_filter,
                'custom_date': custom_date
            }
        })
        
    except Exception as e:
        print(f"❌ Invoice fetch error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoices/<invoice_id>', methods=['GET'])
def get_invoice_details(invoice_id):
    """Get detailed invoice information with accurate payment status"""
    try:
        conn = get_db_connection()
        
        # Get invoice with customer details and payment calculation
        invoice = conn.execute("""SELECT b.*, 
                   COALESCE(c.name, 'Walk-in Customer') as customer_name, 
                   c.phone as customer_phone, 
                   c.address as customer_address,
                   c.email as customer_email,
                   DATE(b.created_at) as invoice_date,
                   TIME(b.created_at) as invoice_time,
                   COALESCE(SUM(p.amount), 0) as paid_amount,
                   CASE 
                       WHEN COALESCE(SUM(p.amount), 0) = 0 THEN 'unpaid'
                       WHEN COALESCE(SUM(p.amount), 0) < b.total_amount THEN 'partial'
                       WHEN COALESCE(SUM(p.amount), 0) >= b.total_amount THEN 'paid'
                       ELSE 'unpaid'
                   END as payment_status
            FROM bills b
            LEFT JOIN customers c ON b.customer_id = c.id
            LEFT JOIN payments p ON b.id = p.bill_id
            WHERE b.id = ?
            GROUP BY b.id""", (invoice_id,)).fetchone()
        
        if not invoice:
            conn.close()
            return jsonify({"error": "Invoice not found"}), 404
        
        # Get invoice items with product details
        items = conn.execute("""SELECT bi.*, 
                   COALESCE(p.name, bi.product_name) as product_name, 
                   p.unit as product_unit,
                   p.category as product_category
            FROM bill_items bi
            LEFT JOIN products p ON bi.product_id = p.id
            WHERE bi.bill_id = ?
            ORDER BY bi.id""", (invoice_id,)).fetchall()
        
        # Get payments with formatted dates
        query = ("SELECT *, DATE(processed_at) as payment_date, TIME(processed_at) as payment_time "
                "FROM payments WHERE bill_id = ? ORDER BY processed_at DESC")
        payments = conn.execute(query, (invoice_id,)).fetchall()
        
        conn.close()
        
        # Format invoice data
        invoice_dict = dict(invoice)
        
        # Format dates
        if invoice_dict['invoice_date']:
            try:
                date_obj = datetime.strptime(invoice_dict['invoice_date'], '%Y-%m-%d')
                invoice_dict['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                invoice_dict['display_date'] = date_obj.strftime('%d %b %Y')
            except:
                invoice_dict['formatted_date'] = invoice_dict['invoice_date']
                invoice_dict['display_date'] = invoice_dict['invoice_date']
        
        # Format time
        if invoice_dict['invoice_time']:
            try:
                time_obj = datetime.strptime(invoice_dict['invoice_time'], '%H:%M:%S')
                invoice_dict['formatted_time'] = time_obj.strftime('%I:%M %p')
            except:
                invoice_dict['formatted_time'] = invoice_dict['invoice_time']
        
        # Calculate balance
        paid_amount = invoice_dict.get('paid_amount', 0) or 0
        total_amount = invoice_dict.get('total_amount', 0) or 0
        invoice_dict['balance_due'] = max(0, total_amount - paid_amount)
        
        # Format items
        formatted_items = []
        for item in items:
            item_dict = dict(item)
            item_dict['line_total'] = item_dict['quantity'] * item_dict['unit_price']
            formatted_items.append(item_dict)
        
        # Format payments
        formatted_payments = []
        for payment in payments:
            payment_dict = dict(payment)
            
            # Format payment date
            if payment_dict['payment_date']:
                try:
                    date_obj = datetime.strptime(payment_dict['payment_date'], '%Y-%m-%d')
                    payment_dict['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                except:
                    payment_dict['formatted_date'] = payment_dict['payment_date']
            
            # Format payment time
            if payment_dict['payment_time']:
                try:
                    time_obj = datetime.strptime(payment_dict['payment_time'], '%H:%M:%S')
                    payment_dict['formatted_time'] = time_obj.strftime('%I:%M %p')
                except:
                    payment_dict['formatted_time'] = payment_dict['payment_time']
            
            formatted_payments.append(payment_dict)
        
        return jsonify({
            "invoice": invoice_dict,
            "items": formatted_items,
            "payments": formatted_payments,
            "summary": {
                "total_items": len(formatted_items),
                "total_payments": len(formatted_payments),
                "subtotal": invoice_dict.get('subtotal', 0),
                "tax_amount": invoice_dict.get('tax_amount', 0),
                "discount_amount": invoice_dict.get('discount_amount', 0),
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "balance_due": invoice_dict['balance_due'],
                "payment_status": invoice_dict['payment_status']
            }
        })
        
    except Exception as e:
        print(f"❌ Invoice details error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoices/export', methods=['GET'])
def export_invoices():
    """Export invoices in different formats (PDF, Excel, CSV, WhatsApp)"""
    try:
        # Get parameters
        format_type = request.args.get('format', 'pdf')
        status = request.args.get('status', 'all')
        date_filter = request.args.get('date_filter', 'all')
        custom_date = request.args.get('custom_date')
        limit = int(request.args.get('limit', 1000))
        
        conn = get_db_connection()
        
        # Build query (same as get_invoices but without pagination)
        base_query = ("SELECT b.*, "
                     "COALESCE(c.name, 'Walk-in Customer') as customer_name, "
                     "c.phone as customer_phone, "
                     "c.email as customer_email, "
                     "DATE(b.created_at) as invoice_date, "
                     "TIME(b.created_at) as invoice_time, "
                     "COALESCE(SUM(p.amount), 0) as paid_amount, "
                     "CASE "
                     "WHEN COALESCE(SUM(p.amount), 0) = 0 THEN 'unpaid' "
                     "WHEN COALESCE(SUM(p.amount), 0) < b.total_amount THEN 'partial' "
                     "WHEN COALESCE(SUM(p.amount), 0) >= b.total_amount THEN 'paid' "
                     "ELSE 'unpaid' "
                     "END as payment_status "
                     "FROM bills b "
                     "LEFT JOIN customers c ON b.customer_id = c.id "
                     "LEFT JOIN payments p ON b.id = p.bill_id")
        
        # Build WHERE conditions
        conditions = []
        params = []
        
        # Date filtering
        if date_filter == 'today':
            conditions.append("DATE(b.created_at) = DATE('now', 'localtime')")
        elif date_filter == 'yesterday':
            conditions.append("DATE(b.created_at) = DATE('now', 'localtime', '-1 day')")
        elif date_filter == 'week':
            conditions.append("DATE(b.created_at) >= DATE('now', 'localtime', '-7 days')")
        elif date_filter == 'month':
            conditions.append("DATE(b.created_at) >= DATE('now', 'localtime', '-30 days')")
        elif date_filter == 'custom' and custom_date:
            conditions.append("DATE(b.created_at) = ?")
            params.append(custom_date)
        
        # Add WHERE clause if conditions exist
        if conditions:
            base_query += ' WHERE ' + ' AND '.join(conditions)
        
        # Group by bill to aggregate payments
        base_query += ' GROUP BY b.id'
        
        # Add payment status filter after GROUP BY
        if status != 'all':
            base_query += f" HAVING payment_status = '{status}' "
        
        # Order by creation date (newest first)
        base_query += ' ORDER BY b.created_at DESC'
        
        # Add limit
        base_query += ' LIMIT ?'
        params.append(limit)
        
        # Execute query
        invoices = conn.execute(base_query, params).fetchall()
        conn.close()
        
        # Convert to list of dicts
        invoice_list = []
        for invoice in invoices:
            invoice_dict = dict(invoice)
            
            # Format dates
            if invoice_dict['invoice_date']:
                try:
                    date_obj = datetime.strptime(invoice_dict['invoice_date'], '%Y-%m-%d')
                    invoice_dict['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                    invoice_dict['display_date'] = date_obj.strftime('%d %b %Y')
                except:
                    invoice_dict['formatted_date'] = invoice_dict['invoice_date']
                    invoice_dict['display_date'] = invoice_dict['invoice_date']
            
            # Calculate balance due
            paid_amount = invoice_dict.get('paid_amount', 0) or 0
            total_amount = invoice_dict.get('total_amount', 0) or 0
            invoice_dict['balance_due'] = max(0, total_amount - paid_amount)
            
            invoice_list.append(invoice_dict)
        
        # Handle different export formats
        if format_type == 'csv':
            return export_invoices_csv(invoice_list)
        elif format_type == 'excel':
            return export_invoices_excel(invoice_list)
        elif format_type == 'pdf':
            return export_invoices_pdf(invoice_list)
        elif format_type == 'whatsapp':
            return export_invoices_whatsapp(invoice_list)
        else:
            return jsonify({"error": "Invalid format"}), 400
            
    except Exception as e:
        print(f"❌ Export error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def export_invoices_csv(invoices):
    """Export invoices to CSV format"""
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Invoice Number', 'Date', 'Customer', 'Total Amount', 
        'Paid Amount', 'Balance Due', 'Payment Status'
    ])
    
    # Write data
    for invoice in invoices:
        writer.writerow([
            invoice.get('bill_number', ''),
            invoice.get('formatted_date', ''),
            invoice.get('customer_name', 'Walk-in Customer'),
            f"{invoice.get('total_amount', 0):.2f}",
            f"{invoice.get('paid_amount', 0):.2f}",
            f"{invoice.get('balance_due', 0):.2f}",
            invoice.get('payment_status', '').upper()
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def export_invoices_excel(invoices):
    """Export invoices to Excel format"""
    try:
        import pandas as pd
        import io
        from flask import make_response
        
        # Prepare data
        data = []
        for invoice in invoices:
            data.append({
                'Invoice Number': invoice.get('bill_number', ''),
                'Date': invoice.get('formatted_date', ''),
                'Customer': invoice.get('customer_name', 'Walk-in Customer'),
                'Total Amount': invoice.get('total_amount', 0),
                'Paid Amount': invoice.get('paid_amount', 0),
                'Balance Due': invoice.get('balance_due', 0),
                'Payment Status': invoice.get('payment_status', '').upper()
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Invoices', index=False)
        
        output.seek(0)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except ImportError:
        # Fallback to CSV if pandas not available
        return export_invoices_csv(invoices)

def export_invoices_whatsapp(invoices):
    """Send invoice summary via WhatsApp"""
    try:
        # Calculate summary
        total_invoices = len(invoices)
        total_amount = sum(inv.get('total_amount', 0) for inv in invoices)
        paid_amount = sum(inv.get('paid_amount', 0) for inv in invoices)
        balance_due = sum(inv.get('balance_due', 0) for inv in invoices)
        
        paid_count = len([inv for inv in invoices if inv.get('payment_status') == 'paid'])
        unpaid_count = len([inv for inv in invoices if inv.get('payment_status') == 'unpaid'])
        partial_count = len([inv for inv in invoices if inv.get('payment_status') == 'partial'])
        
        # Create message
        message = (f"📄 *Invoice Report - BizPulse*\n\n"
                  f"📊 *Summary:*\n"
                  f"• Total Invoices: {total_invoices}\n"
                  f"• Total Amount: ₹{total_amount:,.2f}\n"
                  f"• Paid Amount: ₹{paid_amount:,.2f}\n"
                  f"• Balance Due: ₹{balance_due:,.2f}\n\n"
                  f"📈 *Status Breakdown:*\n"
                  f"• ✅ Paid: {paid_count}\n"
                  f"• ❌ Unpaid: {unpaid_count}\n"
                  f"• ⚠️ Partial: {partial_count}\n\n"
                  f"📅 *Generated:* {datetime.now().strftime('%d/%m/%Y %I:%M %p')}\n\n"
                  f"_Generated by BizPulse ERP System_")
        
        # For now, return the message (you can integrate with WhatsApp API later)
        return jsonify({
            "success": True,
            "message": "WhatsApp report generated successfully!",
            "whatsapp_message": message,
            "summary": {
                "total_invoices": total_invoices,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "balance_due": balance_due
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"WhatsApp export failed: {str(e)}"
        }), 500

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
            query = "SELECT s.*, p.name as product_name, c.name as customer_name FROM sales s LEFT JOIN products p ON s.product_id = p.id LEFT JOIN customers c ON s.customer_id = c.id WHERE s.sale_date = ? ORDER BY s.created_at DESC"
            sales = conn.execute(query, (today,)).fetchall()
        elif date_filter == 'yesterday':
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            query = "SELECT s.*, p.name as product_name, c.name as customer_name FROM sales s LEFT JOIN products p ON s.product_id = p.id LEFT JOIN customers c ON s.customer_id = c.id WHERE s.sale_date = ? ORDER BY s.created_at DESC"
            sales = conn.execute(query, (yesterday,)).fetchall()
        elif date_filter == 'week':
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            query = "SELECT s.*, p.name as product_name, c.name as customer_name FROM sales s LEFT JOIN products p ON s.product_id = p.id LEFT JOIN customers c ON s.customer_id = c.id WHERE s.sale_date >= ? ORDER BY s.created_at DESC"
            sales = conn.execute(query, (week_ago,)).fetchall()
        else:
            # All sales
            query = "SELECT s.*, p.name as product_name, c.name as customer_name FROM sales s LEFT JOIN products p ON s.product_id = p.id LEFT JOIN customers c ON s.customer_id = c.id ORDER BY s.created_at DESC LIMIT 100"
            sales = conn.execute(query).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in sales])
        
    except Exception as e:
        print("Sales fetch error:", str(e))
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

def print_startup_info():
    """Print startup information"""
    import socket 
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("📱 [MOBILE ACCESS]:")
    print(f"   Mobile App: http://{local_ip}:5000/mobile-simple")
    print(f"   Login: bizpulse.erp@gmail.com / admin123")
    print()
    print("🖥️  [DESKTOP ACCESS]:")
    print(f"   Main Site: http://localhost:5000")
    print(f"   Network: http://{local_ip}:5000")
    print()

if __name__ == '__main__':
    init_db()
    print_startup_info()
    app.run(host='0.0.0.0', port=5000, debug=True)