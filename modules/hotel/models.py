"""
Hotel models
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection

class HotelModels:
    
    @staticmethod
    def get_all_guests():
        """Get all hotel guests"""
        conn = get_db_connection()
        try:
            guests = conn.execute('SELECT * FROM hotel_guests ORDER BY created_at DESC').fetchall()
            return [dict(row) for row in guests]
        finally:
            conn.close()
    
    @staticmethod
    def get_all_services():
        """Get all hotel services"""
        conn = get_db_connection()
        try:
            services = conn.execute('SELECT * FROM hotel_services WHERE is_active = 1 ORDER BY name').fetchall()
            return [dict(row) for row in services]
        finally:
            conn.close()