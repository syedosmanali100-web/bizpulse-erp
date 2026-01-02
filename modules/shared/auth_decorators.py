"""
Authentication decorators
COPIED AS-IS from app.py
"""

from functools import wraps
from flask import session, redirect, url_for, render_template, request
from .database import get_current_client_id

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        
        # Set current user ID from session (don't override with dummy value)
        request.current_user_id = get_current_client_id()
        return f(*args, **kwargs)
    return decorated_function

# CMS Authentication decorator
def require_cms_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cms_admin_id' not in session:
            return redirect(url_for('cms_login'))
        return f(*args, **kwargs)
    return decorated_function

# Super Admin Authentication decorator
def require_super_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        if not session.get('is_super_admin', False):
            return render_template('error.html', 
                                 error_title="Access Denied", 
                                 error_message="This module is only available to super administrators (bizpulse.erp@gmail.com)."), 403
        return f(*args, **kwargs)
    return decorated_function

# BizPulse User Authentication decorator (for Client Management)
def require_bizpulse_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('main.login'))
        
        # Check if user is BizPulse official user
        user_email = session.get('email', '').lower()
        user_username = session.get('username', '').lower()
        
        bizpulse_users = [
            'bizpulse.erp@gmail.com',
            'admin@bizpulse.com',
            'support@bizpulse.com',
            'developer@bizpulse.com',
            'osman@bizpulse.com'
        ]
        
        is_bizpulse_user = (
            user_email in bizpulse_users or 
            user_username in bizpulse_users or 
            '@bizpulse.com' in user_email
        )
        
        if not is_bizpulse_user:
            return render_template('error.html', 
                                 error_title="Access Denied", 
                                 error_message="Client Management is only available to BizPulse official users. Please contact support@bizpulse.com for access."), 403
        
        return f(*args, **kwargs)
    return decorated_function