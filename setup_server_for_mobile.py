#!/usr/bin/env python3
"""
BizPulse Server Setup for Mobile APK
Configures the Flask server for optimal mobile app connectivity
"""

import socket
import subprocess
import sys
import os
import platform

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_port_available(port):
    """Check if a port is available"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', port))
        s.close()
        return True
    except OSError:
        return False

def get_network_interfaces():
    """Get all network interfaces"""
    interfaces = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4 Address' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip != '127.0.0.1':
                        interfaces.append(ip)
        else:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            ips = result.stdout.strip().split()
            interfaces = [ip for ip in ips if ip != '127.0.0.1']
    except Exception:
        pass
    
    return interfaces

def create_mobile_optimized_app():
    """Create a mobile-optimized version of app.py"""
    print("📱 Creating mobile-optimized server configuration...")
    
    mobile_app_content = '''#!/usr/bin/env python3
"""
BizPulse Mobile-Optimized Server
Configured for optimal mobile APK connectivity
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import json
from datetime import datetime
import uuid
import hashlib
from functools import wraps
import socket

app = Flask(__name__)

# Enhanced CORS configuration for mobile apps
CORS(app, 
     origins="*",  # Allow all origins for mobile app
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
     supports_credentials=False,
     max_age=86400)  # Cache preflight for 24 hours

app.config['SECRET_KEY'] = 'bizpulse-mobile-secret-key'

# Mobile-specific configuration
app.config['MOBILE_OPTIMIZED'] = True
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

# Add mobile-specific headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,HEAD')
    response.headers.add('Access-Control-Max-Age', '86400')
    
    # Mobile optimization headers
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    
    return response

# Handle preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,X-Requested-With,Accept,Origin")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS,HEAD")
        return response

# Import the rest of the app.py content here
# (Database functions, routes, etc. - same as original app.py)

''' + open('app.py', 'r').read().split('if __name__ == \'__main__\':')[0] + '''

# Mobile-specific routes
@app.route('/mobile/status')
def mobile_status():
    """Mobile app status endpoint"""
    return jsonify({
        'status': 'online',
        'server_ip': get_local_ip(),
        'timestamp': datetime.now().isoformat(),
        'mobile_optimized': True
    })

@app.route('/mobile/config')
def mobile_config():
    """Mobile app configuration"""
    return jsonify({
        'server_url': f"http://{get_local_ip()}:5000",
        'api_base': '/api',
        'features': {
            'offline_mode': True,
            'auto_sync': True,
            'push_notifications': False
        }
    })

if __name__ == '__main__':
    init_db()
    
    local_ip = get_local_ip()
    
    print("🛒 BizPulse Mobile-Optimized Server Starting...")
    print("=" * 60)
    print(f"📱 Mobile Server URL: http://{local_ip}:5000")
    print(f"🌐 Local Access: http://localhost:5000")
    print(f"📊 Dashboard: http://{local_ip}:5000")
    print(f"📱 Mobile App: http://{local_ip}:5000/mobile-fixed")
    print("=" * 60)
    print("📋 Mobile APK Configuration:")
    print(f"   Server IP: {local_ip}")
    print("   Port: 5000")
    print("   Protocol: HTTP")
    print("=" * 60)
    print("🔧 Network Requirements:")
    print("   - Device and server on same WiFi network")
    print("   - Firewall allows port 5000")
    print("   - No proxy or VPN blocking connections")
    print("=" * 60)
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',  # Listen on all interfaces
            port=5000,
            threaded=True,   # Handle multiple requests
            use_reloader=False  # Prevent double startup in debug mode
        )
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        print("💡 Try running as administrator or check if port 5000 is available")
'''
    
    with open('app_mobile_optimized.py', 'w', encoding='utf-8') as f:
        f.write(mobile_app_content)
    
    print("✅ Created app_mobile_optimized.py")

def main():
    """Main setup function"""
    print("🛒 BizPulse Mobile Server Setup")
    print("=" * 50)
    
    # Get network information
    local_ip = get_local_ip()
    interfaces = get_network_interfaces()
    
    print(f"🌐 Network Configuration:")
    print(f"   Primary IP: {local_ip}")
    
    if interfaces:
        print("   Available IPs:")
        for ip in interfaces:
            print(f"     - {ip}")
    
    # Check port availability
    port_available = check_port_available(5000)
    print(f"🔌 Port 5000: {'✅ Available' if port_available else '❌ In Use'}")
    
    if not port_available:
        print("⚠️  Port 5000 is in use. You may need to:")
        print("   - Stop other Flask applications")
        print("   - Use a different port")
        print("   - Kill processes using port 5000")
    
    print("\n📱 Mobile APK Server URLs:")
    print(f"   Primary: http://{local_ip}:5000")
    for ip in interfaces:
        if ip != local_ip:
            print(f"   Alternative: http://{ip}:5000")
    
    # Create mobile-optimized server
    create_mobile_optimized_app()
    
    print("\n🚀 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Run the mobile-optimized server:")
    print("   python app_mobile_optimized.py")
    print("\n2. Build the APK:")
    print("   python ultimate_apk_builder.py")
    print("\n3. Install APK on Android device")
    print("\n4. Ensure device is on same WiFi network")
    
    print(f"\n🔧 Server will be accessible at: http://{local_ip}:5000")
    print("💡 The APK will automatically detect and connect to this server")

if __name__ == "__main__":
    main()