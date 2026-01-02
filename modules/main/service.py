"""
Main website service
COPIED AS-IS from app.py
"""

import os

class MainService:
    
    def get_desktop_app_info(self):
        """Get desktop app information and download status"""
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
        
        return {
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
        }