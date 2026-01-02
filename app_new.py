"""
BizPulse ERP - Modular Monolith Entry Point
REFACTORED FROM SINGLE FILE TO MODULAR ARCHITECTURE
"""

from flask import Flask, request, g, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import timedelta
import logging

# Import shared utilities
from modules.shared.database import init_db

# Import all module blueprints
from modules.auth.routes import auth_bp
from modules.products.routes import products_bp
from modules.mobile.routes import mobile_bp
from modules.main.routes import main_bp
from modules.retail.routes import retail_bp
from modules.hotel.routes import hotel_bp

# Create Flask app
app = Flask(__name__, template_folder='frontend/screens/templates', static_folder='frontend/assets/static')
logger = logging.getLogger(__name__)

# Enable CORS for all domains and methods (for mobile app)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

# App configuration
app.config['SECRET_KEY'] = 'cms-secret-key-change-in-production-2024'  # Change this in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session expires after 24 hours
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

# Initialize database
def initialize_database():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized successfully")

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
    app.run(debug=True, host='0.0.0.0', port=5000)