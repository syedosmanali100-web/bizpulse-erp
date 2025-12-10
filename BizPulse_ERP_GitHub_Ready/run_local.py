#!/usr/bin/env python3
"""
Local development server for BizPulse ERP
Run this file to start the development server
"""

import os
import sys

def main():
    print("🚀 Starting BizPulse ERP Development Server...")
    print("=" * 50)
    
    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  Consider using a virtual environment")
    
    # Import and run the Flask app
    try:
        from app import app
        print("✅ Flask app imported successfully")
        print("🌐 Starting server...")
        print("📱 Access points:")
        print("   - Main Website: http://localhost:5000")
        print("   - Mobile App: http://localhost:5000/mobile-simple")
        print("   - Client Management: http://localhost:5000/client-management")
        print("   - WhatsApp Reports: http://localhost:5000/whatsapp-sender")
        print("🔑 Login: bizpulse.erp@gmail.com / demo123")
        print("=" * 50)
        
        # Run the app
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Error importing app: {e}")
        print("💡 Make sure to install requirements: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()