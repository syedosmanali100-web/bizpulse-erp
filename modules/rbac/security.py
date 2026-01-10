"""
Enterprise Security Utilities
JWT, Encryption, Rate Limiting, Password Hashing
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import os
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, g
from modules.shared.database import get_db_connection, generate_id

# ============================================================================
# CONFIGURATION
# ============================================================================

# JWT Secret (In production, use environment variable)
JWT_SECRET = os.environ.get('JWT_SECRET', 'bizpulse-erp-jwt-secret-key-change-in-production-2024')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRY = timedelta(hours=2)  # 2 hours
REFRESH_TOKEN_EXPIRY = timedelta(days=7)  # 7 days

# Encryption key for sensitive data (In production, use environment variable)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# Rate limiting
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
RATE_LIMIT_WINDOW = timedelta(minutes=5)
MAX_REQUESTS_PER_WINDOW = 20


# ============================================================================
# PASSWORD HASHING (bcrypt)
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def generate_temp_password(length: int = 12) -> str:
    """Generate secure temporary password"""
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# DATA ENCRYPTION (Fernet)
# ============================================================================

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    if not data:
        return None
    return cipher_suite.encrypt(data.encode('utf-8')).decode('utf-8')


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return None
    try:
        return cipher_suite.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
    except Exception:
        return None


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def generate_access_token(user_id: str, user_type: str, tenant_id: str = None, additional_claims: dict = None) -> str:
    """Generate JWT access token"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'tenant_id': tenant_id,
        'exp': datetime.utcnow() + ACCESS_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def generate_refresh_token(user_id: str, user_type: str, tenant_id: str = None) -> str:
    """Generate JWT refresh token"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'tenant_id': tenant_id,
        'exp': datetime.utcnow() + REFRESH_TOKEN_EXPIRY,
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {'valid': True, 'payload': payload}
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token expired'}
    except jwt.InvalidTokenError:
        return {'valid': False, 'error': 'Invalid token'}


def store_session_token(user_id: str, user_type: str, tenant_id: str, access_token: str, refresh_token: str, ip_address: str, user_agent: str):
    """Store session token in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    session_id = generate_id()
    access_expires = datetime.utcnow() + ACCESS_TOKEN_EXPIRY
    refresh_expires = datetime.utcnow() + REFRESH_TOKEN_EXPIRY
    
    cursor.execute('''
        INSERT INTO session_tokens (
            id, user_id, user_type, tenant_id, access_token, refresh_token,
            access_token_expires_at, refresh_token_expires_at, ip_address, user_agent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, user_id, user_type, tenant_id, access_token, refresh_token,
          access_expires, refresh_expires, ip_address, user_agent))
    
    conn.commit()
    conn.close()
    
    return session_id


def revoke_token(token: str):
    """Revoke a token"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE session_tokens 
        SET is_active = 0, revoked_at = CURRENT_TIMESTAMP
        WHERE access_token = ? OR refresh_token = ?
    ''', (token, token))
    
    conn.commit()
    conn.close()


def revoke_all_user_tokens(user_id: str):
    """Revoke all tokens for a user (force logout)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE session_tokens 
        SET is_active = 0, revoked_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND is_active = 1
    ''', (user_id,))
    
    conn.commit()
    conn.close()


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT is_active FROM session_tokens
        WHERE (access_token = ? OR refresh_token = ?) AND is_active = 1
    ''', (token, token))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is None


# ============================================================================
# RATE LIMITING & ACCOUNT LOCKOUT
# ============================================================================

def record_login_attempt(username: str, ip_address: str, user_agent: str, status: str, error_message: str = None):
    """Record login attempt for rate limiting"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO login_attempts (id, username, ip_address, user_agent, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (generate_id(), username, ip_address, user_agent, status, error_message))
    
    conn.commit()
    conn.close()


def check_rate_limit(username: str, ip_address: str) -> dict:
    """Check if user/IP is rate limited"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check failed attempts in last 5 minutes
    time_threshold = (datetime.utcnow() - RATE_LIMIT_WINDOW).isoformat()
    
    cursor.execute('''
        SELECT COUNT(*) FROM login_attempts
        WHERE (username = ? OR ip_address = ?) 
        AND status = 'failed'
        AND created_at > ?
    ''', (username, ip_address, time_threshold))
    
    failed_attempts = cursor.fetchone()[0]
    conn.close()
    
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        return {
            'allowed': False,
            'reason': f'Too many failed attempts. Try again after {LOCKOUT_DURATION.seconds // 60} minutes.',
            'attempts': failed_attempts
        }
    
    return {
        'allowed': True,
        'attempts': failed_attempts,
        'remaining': MAX_LOGIN_ATTEMPTS - failed_attempts
    }


def is_account_locked(user_id: str, user_type: str) -> dict:
    """Check if account is locked"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table = 'super_admins' if user_type == 'super_admin' else 'tenants' if user_type == 'tenant' else 'tenant_users'
    
    cursor.execute(f'''
        SELECT account_locked_until, failed_login_attempts
        FROM {table}
        WHERE id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {'locked': False}
    
    locked_until, failed_attempts = result
    
    if locked_until:
        locked_until_dt = datetime.fromisoformat(locked_until)
        if datetime.utcnow() < locked_until_dt:
            return {
                'locked': True,
                'until': locked_until,
                'reason': f'Account locked due to {failed_attempts} failed login attempts'
            }
    
    return {'locked': False}


def increment_failed_attempts(user_id: str, user_type: str):
    """Increment failed login attempts and lock if threshold reached"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table = 'super_admins' if user_type == 'super_admin' else 'tenants' if user_type == 'tenant' else 'tenant_users'
    
    cursor.execute(f'''
        UPDATE {table}
        SET failed_login_attempts = failed_login_attempts + 1
        WHERE id = ?
    ''', (user_id,))
    
    # Check if should lock account
    cursor.execute(f'''
        SELECT failed_login_attempts FROM {table} WHERE id = ?
    ''', (user_id,))
    
    failed_attempts = cursor.fetchone()[0]
    
    if failed_attempts >= MAX_LOGIN_ATTEMPTS:
        lockout_until = (datetime.utcnow() + LOCKOUT_DURATION).isoformat()
        cursor.execute(f'''
            UPDATE {table}
            SET account_locked_until = ?
            WHERE id = ?
        ''', (lockout_until, user_id))
    
    conn.commit()
    conn.close()


def reset_failed_attempts(user_id: str, user_type: str):
    """Reset failed login attempts on successful login"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    table = 'super_admins' if user_type == 'super_admin' else 'tenants' if user_type == 'tenant' else 'tenant_users'
    
    cursor.execute(f'''
        UPDATE {table}
        SET failed_login_attempts = 0, account_locked_until = NULL
        WHERE id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()


# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def require_auth(allowed_user_types: list = None):
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify token
            result = verify_token(token)
            if not result['valid']:
                return jsonify({'error': result['error']}), 401
            
            # Check if token is revoked
            if is_token_revoked(token):
                return jsonify({'error': 'Token has been revoked'}), 401
            
            payload = result['payload']
            
            # Check user type
            if allowed_user_types and payload['user_type'] not in allowed_user_types:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Store user info in g for access in route
            g.user_id = payload['user_id']
            g.user_type = payload['user_type']
            g.tenant_id = payload.get('tenant_id')
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_super_admin(f):
    """Decorator to require super admin authentication"""
    return require_auth(['super_admin'])(f)


def require_tenant(f):
    """Decorator to require tenant authentication"""
    return require_auth(['tenant'])(f)


def require_tenant_user(f):
    """Decorator to require tenant user authentication"""
    return require_auth(['tenant_user'])(f)


# ============================================================================
# AUDIT LOGGING
# ============================================================================

def log_audit(tenant_id: str, user_id: str, user_type: str, action: str, module: str = None, 
              resource_type: str = None, resource_id: str = None, old_value: str = None, 
              new_value: str = None, status: str = 'success', error_message: str = None):
    """Log audit trail"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None
    
    cursor.execute('''
        INSERT INTO audit_logs (
            id, tenant_id, user_id, user_type, action, module, resource_type, resource_id,
            old_value, new_value, ip_address, user_agent, status, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (generate_id(), tenant_id, user_id, user_type, action, module, resource_type, resource_id,
          old_value, new_value, ip_address, user_agent, status, error_message))
    
    conn.commit()
    conn.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_tenant_id() -> str:
    """Generate unique tenant ID"""
    return f"TNT-{secrets.token_hex(8).upper()}"


def generate_username(business_name: str) -> str:
    """Generate username from business name"""
    # Remove special characters and spaces
    clean_name = ''.join(c for c in business_name if c.isalnum() or c.isspace())
    # Take first 3 words, lowercase, join with underscore
    words = clean_name.lower().split()[:3]
    base_username = '_'.join(words)
    
    # Add random suffix to ensure uniqueness
    suffix = secrets.token_hex(3)
    return f"{base_username}_{suffix}"


def validate_password_strength(password: str) -> dict:
    """Validate password meets security requirements"""
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if not any(c.isupper() for c in password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not any(c.islower() for c in password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not any(c.isdigit() for c in password):
        errors.append('Password must contain at least one number')
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append('Password must contain at least one special character')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
