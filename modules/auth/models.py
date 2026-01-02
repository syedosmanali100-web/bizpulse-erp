"""
Authentication models
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection

class AuthModels:
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email from users table"""
        conn = get_db_connection()
        try:
            user = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
            return dict(user) if user else None
        finally:
            conn.close()
    
    @staticmethod
    def get_client_by_login(login_id):
        """Get client by email or username"""
        conn = get_db_connection()
        try:
            client = conn.execute("SELECT * FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (login_id, login_id)).fetchone()
            return dict(client) if client else None
        finally:
            conn.close()
    
    @staticmethod
    def get_staff_by_login(login_id):
        """Get staff by email or username"""
        conn = get_db_connection()
        try:
            staff = conn.execute("SELECT s.*, c.company_name as business_name FROM staff s JOIN clients c ON s.business_owner_id = c.id WHERE (s.email = ? OR s.username = ?) AND s.is_active = 1", (login_id, login_id)).fetchone()
            return dict(staff) if staff else None
        finally:
            conn.close()
    
    @staticmethod
    def get_client_user_by_login(login_id):
        """Get client user (employee) by email or username"""
        conn = get_db_connection()
        try:
            client_user = conn.execute("SELECT cu.*, c.company_name FROM client_users cu JOIN clients c ON cu.client_id = c.id WHERE (cu.email = ? OR cu.username = ?) AND cu.is_active = 1", (login_id, login_id)).fetchone()
            return dict(client_user) if client_user else None
        finally:
            conn.close()
    
    @staticmethod
    def update_client_user_last_login(user_id):
        """Update last login timestamp for client user"""
        conn = get_db_connection()
        try:
            conn.execute("UPDATE client_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()
    
    @staticmethod
    def get_client_profile(user_id):
        """Get client profile information"""
        conn = get_db_connection()
        try:
            client = conn.execute("SELECT contact_name, company_name, contact_email, profile_picture FROM clients WHERE id = ?", (user_id,)).fetchone()
            return dict(client) if client else None
        finally:
            conn.close()