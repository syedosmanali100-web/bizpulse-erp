"""
Authentication service
COPIED AS-IS from app.py
"""

import sqlite3
from modules.shared.database import get_db_connection, generate_id, hash_password
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    def authenticate_user(self, login_id, password):
        """Authenticate user against all user tables"""
        conn = get_db_connection()
        
        try:
            # First check users table (includes BizPulse admin users)
            user = conn.execute("SELECT id, first_name, last_name, email, business_name, business_type, password_hash, is_active FROM users WHERE email = ? AND is_active = 1", (login_id,)).fetchone()
            
            if user and hash_password(password) == user['password_hash']:
                # Determine if this is a BizPulse admin user
                bizpulse_emails = [
                    'bizpulse.erp@gmail.com',
                    'admin@bizpulse.com', 
                    'support@bizpulse.com',
                    'developer@bizpulse.com',
                    'osman@bizpulse.com'
                ]
                
                is_bizpulse_admin = (
                    user['email'].lower() in bizpulse_emails or 
                    '@bizpulse.com' in user['email'].lower()
                )
                
                session_data = {
                    'user_id': user['id'],
                    'user_type': 'admin' if is_bizpulse_admin else 'client',
                    'user_name': f"{user['first_name']} {user['last_name']}",
                    'email': user['email'],
                    'username': user['email'],  # Use email as username for BizPulse check
                    'business_name': user['business_name'],
                    'business_type': user['business_type'],
                    'is_super_admin': is_bizpulse_admin
                }
                
                conn.close()
                
                return {
                    'success': True,
                    'token': 'user-jwt-token',
                    'session_data': session_data,
                    'user': {
                        "id": user['id'],
                        "name": f"{user['first_name']} {user['last_name']}",
                        "email": user['email'],
                        "username": user['email'],
                        "type": 'admin' if is_bizpulse_admin else 'client',
                        "business_name": user['business_name'],
                        "business_type": user['business_type'],
                        "is_super_admin": is_bizpulse_admin
                    }
                }
            
            # Then check client database (business owners)
            client = conn.execute("SELECT id, company_name, contact_name, contact_email, username, password_hash, is_active FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (login_id, login_id)).fetchone()
            
            if client and hash_password(password) == client['password_hash']:
                session_data = {
                    'user_id': client['id'],
                    'user_type': "client",
                    'user_name': client['contact_name'] or client['company_name'],
                    'email': client['contact_email'],
                    'username': client['username'],
                    'company_name': client['company_name'],
                    'is_super_admin': False
                }
                
                conn.close()
                return {
                    'success': True,
                    'token': 'client-jwt-token',
                    'session_data': session_data,
                    'user': {
                        "id": client['id'],
                        "name": client['contact_name'] or client['company_name'],
                        "email": client['contact_email'],
                        "username": client['username'],
                        "type": "client",
                        "company_name": client['company_name'],
                        "business_type": "retail",
                        "is_super_admin": False
                    }
                }
            
            # Finally check staff and employee tables
            staff = conn.execute("SELECT s.id, s.name, s.email, s.username, s.password_hash, s.role, s.is_active, s.business_owner_id, c.company_name as business_name FROM staff s JOIN clients c ON s.business_owner_id = c.id WHERE (s.email = ? OR s.username = ?) AND s.is_active = 1", (login_id, login_id)).fetchone()
            
            if staff and hash_password(password) == staff['password_hash']:
                session_data = {
                    'user_id': staff['id'],
                    'user_type': "staff",
                    'user_name': staff['name'],
                    'email': staff['email'],
                    'username': staff['username'],
                    'business_owner_id': staff['business_owner_id'],
                    'staff_role': staff['role'],
                    'is_super_admin': False
                }
                
                conn.close()
                return {
                    'success': True,
                    'token': 'staff-jwt-token',
                    'session_data': session_data,
                    'user': {
                        "id": staff['id'],
                        "name": staff['name'],
                        "email": staff['email'],
                        "username": staff['username'],
                        "type": "staff",
                        "role": staff['role'],
                        "business_name": staff['business_name'],
                        "business_type": "retail",
                        "is_super_admin": False
                    }
                }
            
            # Check client users (employees)
            client_user = conn.execute("SELECT cu.id, cu.full_name, cu.email, cu.username, cu.password_hash, cu.is_active, cu.role, cu.client_id, c.company_name FROM client_users cu JOIN clients c ON cu.client_id = c.id WHERE (cu.email = ? OR cu.username = ?) AND cu.is_active = 1", (login_id, login_id)).fetchone()
            
            if client_user and hash_password(password) == client_user['password_hash']:
                session_data = {
                    'user_id': client_user['id'],
                    'user_type': "employee",
                    'user_name': client_user['full_name'],
                    'email': client_user['email'],
                    'username': client_user['username'],
                    'client_id': client_user['client_id'],
                    'is_super_admin': False
                }
                
                # Update last login
                conn.execute("UPDATE client_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (client_user['id'],))
                conn.commit()
                
                conn.close()
                return {
                    'success': True,
                    'token': 'employee-jwt-token',
                    'session_data': session_data,
                    'user': {
                        "id": client_user['id'],
                        "name": client_user['full_name'],
                        "email": client_user['email'],
                        "username": client_user['username'],
                        "type": "employee",
                        "role": client_user['role'],
                        "company": client_user['company_name'],
                        "business_type": "retail",
                        "is_super_admin": False
                    }
                }
            
            conn.close()
            return {'success': False, 'message': 'Invalid credentials'}
            
        except Exception as e:
            conn.close()
            raise e
    
    def get_user_info(self, session):
        """Get current user information including role and profile data"""
        user_id = session.get('user_id')
        user_type = session.get('user_type')
        user_name = session.get('user_name')
        
        # If it's a client, get the actual contact name from database
        if user_type == 'client' and user_id:
            conn = get_db_connection()
            try:
                client = conn.execute("SELECT contact_name, company_name, contact_email, profile_picture FROM clients WHERE id = ?", (user_id,)).fetchone()
                
                if client:
                    # Use contact_name if available, otherwise use company_name
                    actual_name = client['contact_name'] or client['company_name'] or user_name
                    profile_picture = client['profile_picture']
                    email = client['contact_email']
                else:
                    actual_name = user_name
                    profile_picture = None
                    email = None
                    
            except Exception as e:
                print(f"Error getting client profile: {e}")
                actual_name = user_name
                profile_picture = None
                email = None
            finally:
                conn.close()
        else:
            actual_name = user_name
            profile_picture = None
            email = None
        
        return {
            "user_id": user_id,
            "user_type": user_type,
            "user_name": actual_name,
            "email": email or session.get('email'),  # Include session email as fallback
            "username": session.get('username'),     # Include username for BizPulse check
            "profile_picture": profile_picture,
            "is_super_admin": session.get('is_super_admin', False),
            "staff_role": session.get('staff_role')  # For staff members
        }
    
    def register_user(self, data):
        """Register a new user"""
        user_id = generate_id()
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (id, email, password_hash, business_name, business_type) VALUES (?, ?, ?, ?, ?)", (
                user_id, data['email'], hash_password(data['password']),
                data.get('business_name', ''), data.get('business_type', 'retail')
            ))
            conn.commit()
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'message': 'Email already exists'}
        finally:
            conn.close()
    
    def forgot_password(self, email_or_username):
        """Handle forgot password functionality"""
        conn = get_db_connection()
        
        try:
            # Create password_reset_tokens table if it doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    username TEXT,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            user_found = None
            user_type = None
            user_id = None
            username = None
            
            # Check in users table first
            user = conn.execute("SELECT id, email, first_name, last_name FROM users WHERE (email = ? OR email = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
            
            if user:
                user_found = user
                user_type = 'user'
                user_id = user['id']
                username = user['email']
            else:
                # Check in clients table
                client = conn.execute("SELECT id, contact_email, company_name, username FROM clients WHERE (contact_email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
                
                if client:
                    user_found = client
                    user_type = 'client'
                    user_id = client['id']
                    username = client['username']
                else:
                    # Check in client_users table (employees)
                    client_user = conn.execute("SELECT id, email, full_name, username FROM client_users WHERE (email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
                    
                    if client_user:
                        user_found = client_user
                        user_type = 'client_user'
                        user_id = client_user['id']
                        username = client_user['username']
                    else:
                        # Check in staff table
                        staff = conn.execute("SELECT id, email, name, username FROM staff WHERE (email = ? OR username = ?) AND is_active = 1", (email_or_username, email_or_username)).fetchone()
                        
                        if staff:
                            user_found = staff
                            user_type = 'staff'
                            user_id = staff['id']
                            username = staff['username']
            
            if not user_found:
                conn.close()
                return {'success': False, 'message': 'User not found'}
            
            # Generate reset token
            import secrets
            from datetime import datetime, timedelta
            
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)  # Token expires in 24 hours
            
            # Store reset token
            conn.execute('''
                INSERT INTO password_reset_tokens (id, user_id, user_type, token, email, username, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (generate_id(), user_id, user_type, reset_token, 
                  user_found.get('email') or user_found.get('contact_email'), 
                  username, expires_at.isoformat()))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Password reset token generated successfully',
                'reset_token': reset_token,
                'user_type': user_type,
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            conn.close()
            raise e