"""
Mobile and PWA routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template, send_from_directory, redirect, jsonify, make_response
from datetime import datetime

mobile_bp = Blueprint('mobile', __name__)

@mobile_bp.route('/mobile-login-test')
def mobile_login_test():
    return render_template('mobile_login_test.html')

@mobile_bp.route('/mobile-simple-old')
def mobile_simple_old():
    return render_template('mobile_simple_test.html')

@mobile_bp.route('/mobile-instant')
def mobile_instant():
    return render_template('mobile_instant.html')

@mobile_bp.route('/mobile-debug')
def mobile_debug():
    return render_template('mobile_debug.html')

@mobile_bp.route('/test-hamburger')
def test_hamburger():
    return render_template('test_hamburger.html')

@mobile_bp.route('/diagnostic-full')
def diagnostic_full():
    return render_template('mobile_diagnostic_full.html')

@mobile_bp.route('/mobile-simple')
def mobile_simple_new():
    return render_template('mobile_simple_working.html')

@mobile_bp.route('/mobile-diagnostic')
def mobile_diagnostic():
    return render_template('mobile_diagnostic_simple.html')

@mobile_bp.route('/mobile-test')
def mobile_test_connection():
    return render_template('mobile_test_connection.html')

@mobile_bp.route('/mobile-fresh')
def mobile_fresh_version():
    return render_template('mobile_fresh.html')

@mobile_bp.route('/mobile-test-page')
def mobile_test_page():
    return render_template('mobile_test_simple.html')

@mobile_bp.route('/camera-test')
def camera_test():
    return render_template('camera_test.html')

# PWA Support Routes
@mobile_bp.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@mobile_bp.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@mobile_bp.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@mobile_bp.route('/offline.html')
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

@mobile_bp.route('/mobile')
def mobile_app():
    return render_template('mobile_simple_working.html')

@mobile_bp.route('/mobile-dashboard')
def mobile_dashboard():
    """Mobile ERP Dashboard - Original interface"""
    return render_template('mobile_simple_working.html')

@mobile_bp.route('/mobile-simple')
def mobile_simple():
    """Direct redirect to mobile dashboard"""
    return redirect('/mobile-dashboard')

@mobile_bp.route('/mobile-v1')
def mobile_app_v1():
    return render_template('mobile_erp_working.html')

@mobile_bp.route('/mobile-old')
def mobile_app_old():
    return render_template('mobile_erp_working.html')

@mobile_bp.route('/mobile-working')
def mobile_working():
    return render_template('mobile_erp_working.html')

@mobile_bp.route('/mobile-fixed')
def mobile_app_fixed():
    return render_template('mobile_erp_working.html')

@mobile_bp.route('/mobile-pwa')
def mobile_pwa():
    response = make_response(render_template('mobile_erp_working.html'))
    # Add cache-busting headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@mobile_bp.route('/api/version')
def api_version():
    """API endpoint for version checking - enables auto-updates"""
    return jsonify({
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat(),
        "features": ["products", "customers", "reports"]
    })