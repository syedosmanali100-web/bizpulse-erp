"""
BizPulse ERP - Modular Monolith Entry Point
REFACTORED FROM SINGLE FILE TO MODULAR ARCHITECTURE
WITH REAL-TIME SYNC SUPPORT
"""

from flask import Flask, request, g, make_response
from flask_cors import CORS
# from flask_socketio import SocketIO  # Temporarily commented for testing
from werkzeug.utils import secure_filename
import os
import json
from datetime import timedelta
import logging
import threading
import time
import atexit

# Import shared utilities
from modules.shared.database import init_db

# Import all module blueprints
from modules.auth.routes import auth_bp
from modules.products.routes import products_bp
from modules.mobile.routes import mobile_bp
from modules.main.routes import main_bp
from modules.retail.routes import retail_bp
from modules.hotel.routes import hotel_bp
from modules.billing.routes import billing_bp
from modules.sales.routes import sales_bp
from modules.invoices.routes import invoices_bp
from modules.dashboard.routes import dashboard_bp
from modules.customers.routes import customers_bp
from modules.credit.routes import credit_bp
from modules.settings.routes import settings_bp
from modules.reports.routes import reports_bp
from modules.earnings.routes import earnings_bp
from modules.notifications.routes import notifications_bp
# from modules.rbac.routes import rbac_bp  # RBAC System - temporarily disabled

# Import sync module (temporarily disabled)
# from modules.sync.routes import init_socketio_events
from modules.sync.service import sync_service
from modules.sync.api_routes import sync_api_bp

# Create Flask app
app = Flask(__name__, template_folder='frontend/screens/templates', static_folder='frontend/assets/static')
logger = logging.getLogger(__name__)

# Enable CORS for all domains and methods (for mobile app)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# Initialize SocketIO for real-time sync (temporarily disabled)
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# App configuration
app.config['SECRET_KEY'] = 'cms-secret-key-change-in-production-2024'  # Change this in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Session expires after 30 days
app.config['SESSION_PERMANENT'] = True  # Make sessions permanent
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem for session storage
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates for development

# File Upload Configuration
UPLOAD_FOLDER = 'frontend/assets/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    # Refresh session on every request to keep it alive
    if 'user_id' in session:
        session.modified = True
    
    # language preference comes from cookie `app_lang` (set by frontend)
    lang = request.cookies.get('app_lang')
    if not lang:
        # try Accept-Language header fallback (very small parsing)
        al = request.headers.get('Accept-Language', '')
        if al:
            lang = al.split(',')[0].split('-')[0]
    g.lang = lang or 'en'

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(mobile_bp)
app.register_blueprint(main_bp)
app.register_blueprint(retail_bp)
app.register_blueprint(hotel_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(invoices_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(credit_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(earnings_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(sync_api_bp)
# app.register_blueprint(rbac_bp)  # RBAC System - temporarily disabled

# Initialize WebSocket events for real-time sync (temporarily disabled)
# init_socketio_events(socketio)

# Background task for cleanup
def cleanup_task():
    """Background task to cleanup inactive sessions"""
    while True:
        try:
            sync_service.cleanup_inactive_sessions()
            time.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"❌ Cleanup task error: {e}")
            time.sleep(60)

# Start cleanup task in background
cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
cleanup_thread.start()

# Start stock monitoring service
def start_background_services():
    """Start all background services"""
    try:
        from modules.notifications.stock_monitor import start_stock_monitor
        start_stock_monitor()
        print("✅ Stock monitoring service started")
    except Exception as e:
        print(f"❌ Failed to start stock monitoring service: {e}")

# Start background services in a separate thread to avoid blocking startup
services_thread = threading.Thread(target=start_background_services, daemon=True)
services_thread.start()

# Cleanup on app shutdown
def cleanup_on_exit():
    """Cleanup function called on app shutdown"""
    try:
        from modules.notifications.stock_monitor import stop_stock_monitor
        stop_stock_monitor()
        print("✅ Background services stopped")
    except Exception as e:
        print(f"❌ Error stopping background services: {e}")

atexit.register(cleanup_on_exit)

# Make socketio available globally for broadcasting (temporarily disabled)
# app.socketio = socketio

# Initialize database
def initialize_database():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized successfully")

# Import auth decorators for CMS
from modules.shared.auth_decorators import require_cms_auth
from flask import render_template, redirect, url_for, session, flash

# CMS Routes
@app.route('/cms-access')
def cms_access_page():
    """CMS Access Information Page - Redirects to login"""
    return render_template('cms_access.html')

@app.route('/cms/login', methods=['GET', 'POST'])
def cms_login():
    """CMS Login Page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper password hashing)
        if username == 'admin' and password == 'admin123':
            session['cms_admin_id'] = 'admin'  # Fixed: use cms_admin_id instead of cms_authenticated
            session['cms_user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('cms_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('cms_login.html')

@app.route('/cms/logout')
def cms_logout():
    """CMS Logout"""
    session.pop('cms_admin_id', None)  # Fixed: use cms_admin_id
    session.pop('cms_user', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('cms_login'))

@app.route('/cms')
@require_cms_auth
def cms_dashboard():
    """CMS Dashboard - Overview of all content"""
    return render_template('cms_dashboard.html')

@app.route('/cms/brand-logo')
@require_cms_auth
def cms_brand_logo():
    """Brand Logo Management Page"""
    return render_template('cms_brand_logo.html')

@app.route('/cms/settings')
@require_cms_auth
def cms_settings():
    """CMS Settings Page"""
    return render_template('cms_settings.html')

@app.route('/cms/hero')
@require_cms_auth
def cms_hero():
    """CMS Hero Section Management"""
    return render_template('cms_hero.html')

@app.route('/cms/features')
@require_cms_auth
def cms_features():
    """CMS Features Management"""
    return render_template('cms_features.html')

@app.route('/cms/pricing')
@require_cms_auth
def cms_pricing():
    """CMS Pricing Management"""
    return render_template('cms_pricing.html')

@app.route('/cms/testimonials')
@require_cms_auth
def cms_testimonials():
    """CMS Testimonials Management"""
    return render_template('cms_testimonials.html')

@app.route('/cms/faqs')
@require_cms_auth
def cms_faqs():
    """CMS FAQs Management"""
    return render_template('cms_faqs.html')

@app.route('/cms/gallery')
@require_cms_auth
def cms_gallery():
    """CMS Gallery Management"""
    return render_template('cms_gallery.html')

@app.route('/cms/profile')
@require_cms_auth
def cms_profile():
    """CMS Profile & Password Management"""
    return render_template('cms_profile.html')

@app.route('/notification-settings')
def notification_settings():
    """Notification Settings Page"""
    return render_template('notification_settings.html')

@app.route('/stock-alert-demo')
def stock_alert_demo():
    """Stock Alert Demo Page"""
    return render_template('stock_alert_demo.html')

def print_startup_info():
    """Print startup information"""
    print()
    print("🚀 BizPulse ERP - Modular Monolith")
    print("=" * 50)
    print("📊 ERP System: ACTIVE")
    print("🏪 Retail Management: ACTIVE") 
    print("🏨 Hotel Management: ACTIVE")
    print("📱 Mobile App: ACTIVE")
    print("🌐 Website: ACTIVE")
    print("⚙️  CMS: ACTIVE")
    print("=" * 50)
    print("🔗 Main URL: http://localhost:5000")
    print("📱 Mobile: http://localhost:5000/mobile")
    print("🏪 Retail: http://localhost:5000/retail/dashboard")
    print("🏨 Hotel: http://localhost:5000/hotel/dashboard")
    print("=" * 50)
    print("✅ All modules loaded successfully!")
    print()

if __name__ == '__main__':
    initialize_database()
    print_startup_info()
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 