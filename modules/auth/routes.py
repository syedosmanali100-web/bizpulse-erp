"""
Authentication routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, make_response, g
from .service import AuthService
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/api/set_language', methods=['POST'])
def api_set_language():
    try:
        data = request.get_json(force=True)
        lang = data.get('lang') if isinstance(data, dict) else None
        if not lang:
            return jsonify({'status':'error','message':'missing lang'}), 400
        resp = make_response(jsonify({'status':'ok'}))
        # set cookie for 1 year
        resp.set_cookie('app_lang', lang, max_age=60*60*24*365, httponly=False)
        return resp
    except Exception as e:
        return jsonify({'status':'error','message': str(e)}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
@auth_bp.route('/api/auth/unified-login', methods=['POST'])
def api_login():
    """Unified login for all user types with proper database authentication"""
    data = request.get_json()
    
    # Handle both login_id and loginId (mobile uses loginId)
    login_id = data.get('loginId') or data.get('login_id') or data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not login_id or not password:
        return jsonify({'message': 'Login ID and password are required'}), 400
    
    try:
        result = auth_service.authenticate_user(login_id, password)
        if result['success']:
            # Set session data
            for key, value in result['session_data'].items():
                session[key] = value
            session.permanent = True
            
            logger.info(f"✅ User login successful: {result['user']['email']} (Type: {result['user']['type']})")
            
            return jsonify({
                "message": "Login successful",
                "token": result['token'],
                "user": result['user']
            })
        else:
            return jsonify({"message": result['message']}), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"message": "Login error", "error": str(e)}), 500

@auth_bp.route('/api/auth/user-info', methods=['GET'])
def get_user_info():
    """Get current user information including role and profile data"""
    try:
        result = auth_service.get_user_info(session)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_user_info: {e}")
        return jsonify({
            "user_id": session.get('user_id'),
            "user_type": session.get('user_type'),
            "user_name": session.get('user_name'),
            "email": session.get('email'),           # Include session email
            "username": session.get('username'),     # Include username
            "profile_picture": None,
            "is_super_admin": session.get('is_super_admin', False),
            "staff_role": session.get('staff_role')
        })

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.json
    
    try:
        result = auth_service.register_user(data)
        if result['success']:
            return jsonify({"message": "Registration successful", "user_id": result['user_id']})
        else:
            return jsonify({"message": result['message']}), 400
    except Exception as e:
        return jsonify({"message": "Registration error", "error": str(e)}), 500

@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Generate password reset token and allow user to set new password"""
    data = request.get_json()
    email_or_username = data.get('email', '').strip() or data.get('username', '').strip()
    
    if not email_or_username:
        return jsonify({'message': 'Email or username is required'}), 400
    
    try:
        result = auth_service.forgot_password(email_or_username)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({'message': result['message']}), 404
    except Exception as e:
        return jsonify({'message': 'Password reset error', 'error': str(e)}), 500