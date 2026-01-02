"""
Mobile service
COPIED AS-IS from app.py
"""

from datetime import datetime

class MobileService:
    
    def get_version_info(self):
        """Get mobile app version information"""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "features": ["products", "customers", "reports"]
        }