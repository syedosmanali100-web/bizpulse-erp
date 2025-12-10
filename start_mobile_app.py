#!/usr/bin/env python3
"""
BizPulse Mobile App Starter - PWA Solution
Direct mobile access without APK issues
"""

import subprocess
import socket
import webbrowser
import time
import qrcode
from pathlib import Path
import sys

class MobileAppStarter:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 5000
        
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def create_qr_code(self, url):
        """Create QR code for mobile access"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)
            
            print("\n" + "="*50)
            print("📱 SCAN QR CODE WITH YOUR PHONE:")
            print("="*50)
            qr.print_ascii()
            print("="*50)
            
        except ImportError:
            print(f"\n📱 Open this URL on your phone: {url}")
    
    def start_app(self):
        """Start the mobile app"""
        print("🛒 BizPulse Mobile App Starter")
        print("="*50)
        
        # Get IP address
        ip = self.get_local_ip()
        url = f"http://{ip}:{self.port}"
        
        print(f"🌐 Starting server on: {url}")
        print("📱 Mobile URL: " + url)
        
        # Create QR code
        self.create_qr_code(url)
        
        print("\n📋 Instructions:")
        print("1. Connect your phone to same WiFi")
        print("2. Scan QR code OR open URL in mobile browser")
        print("3. Tap 'Add to Home Screen' when prompted")
        print("4. Use as native app!")
        
        print(f"\n🔑 Login Details:")
        print("Email: admin@demo.com")
        print("Password: demo123")
        
        print("\n🚀 Starting Flask server...")
        
        # Start Flask app
        try:
            subprocess.run([sys.executable, "app.py"], check=True)
        except KeyboardInterrupt:
            print("\n⚠️ Server stopped")
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    starter = MobileAppStarter()
    starter.start_app()

if __name__ == "__main__":
    main()