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

@mobile_bp.route('/mobile-debug-template')
def mobile_debug_template():
    """Debug endpoint to verify template serving"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mobile Debug - Template Test</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial; padding: 20px; background: #f0f0f0;">
        <h1>🔍 Mobile Template Debug</h1>
        <p><strong>Template:</strong> mobile_simple_working.html</p>
        <p><strong>Version:</strong> 2.0.2 - NO EMAIL VALIDATION</p>
        <p><strong>Date:</strong> 2026-01-09</p>
        
        <h2>Login Form Test:</h2>
        <form>
            <div style="margin: 10px 0;">
                <label>Email or Username:</label><br>
                <input type="text" id="testLogin" placeholder="abc_electronic" style="padding: 10px; width: 200px;">
                <span id="inputType" style="color: green; font-weight: bold;"></span>
            </div>
            <div style="margin: 10px 0;">
                <label>Password:</label><br>
                <input type="password" placeholder="admin123" style="padding: 10px; width: 200px;">
            </div>
            <button type="button" onclick="testInput()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px;">Test Input</button>
        </form>
        
        <div id="result" style="margin-top: 20px; padding: 10px; background: white; border-radius: 5px;"></div>
        
        <script>
            function testInput() {
                const input = document.getElementById('testLogin');
                const result = document.getElementById('result');
                
                result.innerHTML = `
                    <h3>✅ Input Test Results:</h3>
                    <p><strong>Input Type:</strong> ${input.type}</p>
                    <p><strong>Value:</strong> "${input.value}"</p>
                    <p><strong>Required @ symbol:</strong> ${input.type === 'email' ? 'YES ❌' : 'NO ✅'}</p>
                    <p><strong>Browser validation:</strong> ${input.checkValidity() ? 'PASSED ✅' : 'FAILED ❌'}</p>
                `;
                
                document.getElementById('inputType').textContent = `(Type: ${input.type})`;
            }
            
            // Auto-test on load
            setTimeout(() => {
                document.getElementById('testLogin').value = 'abc_electronic';
                testInput();
            }, 500);
        </script>
        
        <hr style="margin: 30px 0;">
        <p><a href="/mobile" style="color: #007bff;">← Back to Mobile App</a></p>
    </body>
    </html>
    '''

@mobile_bp.route('/mobile')
def mobile_app():
    response = make_response(render_template('mobile_simple_working.html'))
    # Add cache-busting headers to ensure fresh template
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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

@mobile_bp.route('/api/modules')
def get_erp_modules():
    """Get all available ERP modules for the mobile menu"""
    return jsonify({
        "success": True,
        "core_modules": [
            {"name": "Dashboard", "route": "dashboard", "icon": "📊"},
            {"name": "Billing", "route": "billing", "icon": "🧾"},
            {"name": "Sales", "route": "sales", "icon": "💰"}
        ],
        "inventory_modules": [
            {"name": "Products", "route": "products", "icon": "📦"},
            {"name": "Inventory", "route": "inventory", "icon": "📋"}
        ],
        "customer_modules": [
            {"name": "Customers", "route": "customers", "icon": "👥"},
            {"name": "Credit", "route": "credit", "icon": "💳"}
        ]
    })