"""
Main website routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template, send_file, jsonify
from modules.shared.auth_decorators import require_auth, require_cms_auth
import os

main_bp = Blueprint('main', __name__)

# Routes
@main_bp.route('/')
def index():
    """Main website - loads saved content if available, or returns default template"""
    return render_template('index.html')

@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/register')
def register():
    return render_template('register.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/gallery')
def gallery_page():
    """Public Gallery Page"""
    return render_template('gallery.html')

@main_bp.route('/website-builder')
@require_cms_auth
def website_builder():
    """Professional Website Builder - Photoshop/Canva Style"""
    return render_template('website_builder_pro.html')

# ============================================================================
# DESKTOP APP DOWNLOAD ROUTES - BizPulse Desktop ERP
# ============================================================================

@main_bp.route('/desktop')
def desktop_download_page():
    """Desktop App Download Page"""
    return render_template('desktop_download.html')

@main_bp.route('/download/desktop')
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

@main_bp.route('/download/desktop/exe')
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

@main_bp.route('/api/desktop/info')
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

@main_bp.route('/debug-routes')
def debug_routes():
    """Debug route to show all available routes"""
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
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

@main_bp.route('/test-navigation')
def test_navigation():
    return render_template('test_navigation.html')

@main_bp.route('/test-permissions')
def test_permissions():
    return render_template('test_permissions.html')

@main_bp.route('/sales-management')
def sales_management():
    return render_template('sales_management_wine.html')

@main_bp.route('/debug-sales')
def debug_sales():
    return render_template('debug_sales_management.html')

@main_bp.route('/sales-management-old')
def sales_management_old():
    return render_template('sales_management_new.html')

@main_bp.route('/inventory/low-stock')
def low_stock_management():
    return render_template('low_stock_management.html')