"""
Main website routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template, send_from_directory, send_file, jsonify, request
from modules.shared.auth_decorators import require_auth, require_cms_auth
import os
import base64
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

# Routes
@main_bp.route('/test-mobile-access')
def test_mobile_access():
    """Test mobile access"""
    return send_from_directory('.', 'test_mobile_access.html')

@main_bp.route('/test-activity')
def test_activity():
    """Test activity frontend"""
    return send_from_directory('.', 'test_frontend_activity.html')

@main_bp.route('/test-buttons')
def test_buttons():
    """Test buttons fix"""
    return send_from_directory('.', 'test_buttons_fix.html')

@main_bp.route('/test-search')
def test_search():
    """Test universal search"""
    return send_from_directory('.', 'test_search.html')

@main_bp.route('/test-sales-pagination')
def test_sales_pagination():
    """Test sales pagination"""
    return send_from_directory('.', 'test_sales_pagination.html')

@main_bp.route('/test-logo')
def test_logo():
    """Test logo display"""
    return send_from_directory('.', 'test_logo_display.html')

@main_bp.route('/static/uploads/logos/<filename>')
def serve_logo(filename):
    """Serve logo files directly"""
    try:
        logo_dir = os.path.join('static', 'uploads', 'logos')
        return send_from_directory(logo_dir, filename)
    except Exception as e:
        return f"Error serving logo: {str(e)}", 404

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

@main_bp.route('/api/upload-company-logo', methods=['POST'])
def upload_company_logo():
    """Upload company logo"""
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No logo file provided'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Invalid file type. Please upload an image file.'}), 400
        
        # Validate file size (max 5MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({'error': 'File size must be less than 5MB'}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads', 'logos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        import time
        timestamp = str(int(time.time()))
        name, ext = os.path.splitext(filename)
        filename = f"company_logo_{timestamp}{ext}"
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Return success with file URL
        logo_url = f"/static/uploads/logos/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Logo uploaded successfully',
            'logo_url': logo_url,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@main_bp.route('/api/get-company-logo')
def get_company_logo():
    """Get current company logo"""
    try:
        # In a real application, you would get this from database
        # For now, return the most recent logo from uploads directory
        upload_dir = os.path.join('static', 'uploads', 'logos')
        
        print(f"🔍 [LOGO API] Checking directory: {upload_dir}")
        
        if not os.path.exists(upload_dir):
            print(f"❌ [LOGO API] Directory does not exist: {upload_dir}")
            return jsonify({'logo_url': None})
        
        # Get the most recent logo file
        logo_files = [f for f in os.listdir(upload_dir) if f.startswith('company_logo_')]
        print(f"📁 [LOGO API] Found {len(logo_files)} logo files: {logo_files}")
        
        if not logo_files:
            print("❌ [LOGO API] No logo files found")
            return jsonify({'logo_url': None})
        
        # Sort by timestamp (newest first)
        logo_files.sort(reverse=True)
        latest_logo = logo_files[0]
        
        logo_url = f"/static/uploads/logos/{latest_logo}"
        print(f"✅ [LOGO API] Returning logo URL: {logo_url}")
        return jsonify({'logo_url': logo_url})
        
    except Exception as e:
        print(f"❌ [LOGO API] Error: {str(e)}")
        return jsonify({'error': f'Failed to get logo: {str(e)}'}), 500

@main_bp.route('/cms/brand-logo')
@require_cms_auth
def cms_brand_logo():
    """Brand Logo Management Page"""
    return render_template('cms_brand_logo.html')

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
    from flask import make_response
    response = make_response(render_template('sales_management_wine.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@main_bp.route('/debug-sales')
def debug_sales():
    return render_template('debug_sales_management.html')

@main_bp.route('/sales-management-old')
def sales_management_old():
    return render_template('sales_management_new.html')

@main_bp.route('/inventory/low-stock')
def low_stock_management():
    return render_template('low_stock_management.html')

@main_bp.route('/premium-dashboard')
def premium_dashboard():
    """Premium Dashboard with 4 sections: Recent Sales, Last Product, Last Customer, Last Bulk Order"""
    return render_template('premium_dashboard.html')

@main_bp.route('/dashboard')
def dashboard_main():
    """Main Dashboard Page"""
    return render_template('dashboard_main.html')

@main_bp.route('/dashboard/demo')
def dashboard_demo():
    """Dashboard API Demo Page"""
    return render_template('dashboard_demo.html')

@main_bp.route('/client-management')
def client_management():
    """Client Management Page"""
    return render_template('client_management_clean.html')