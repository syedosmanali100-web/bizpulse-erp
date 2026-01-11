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

@auth_bp.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """Logout user and clear session"""
    try:
        # Clear all session data
        session.clear()
        
        logger.info('✅ User logged out successfully')
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'message': 'Logout error',
            'error': str(e)
        }), 500

@auth_bp.route('/api/auth/client-login', methods=['POST'])
def client_login():
    """Client login with username/password for mobile app"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        from modules.shared.database import get_db_connection
        import hashlib
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Try to find client by username or email
        cursor.execute('''
            SELECT id, company_name, username, contact_email, password_hash, is_active
            FROM clients
            WHERE username = ? OR contact_email = ?
        ''', (username, username))
        
        client = cursor.fetchone()
        conn.close()
        
        if not client:
            logger.warning(f"❌ Client not found: {username}")
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        
        client_id, company_name, client_username, email, password_hash, is_active = client
        
        # Check if client is active
        if not is_active:
            logger.warning(f"❌ Client account inactive: {username}")
            return jsonify({
                'success': False,
                'message': 'Account is inactive. Please contact support.'
            }), 401
        
        # Verify password
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if input_hash != password_hash:
            logger.warning(f"❌ Invalid password for client: {username}")
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        
        # Update last login
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE clients 
            SET last_login = CURRENT_TIMESTAMP,
                login_count = login_count + 1
            WHERE id = ?
        ''', (client_id,))
        conn.commit()
        conn.close()
        
        # Set session
        session['user_id'] = client_id
        session['user_type'] = 'client'
        session['user_name'] = company_name
        session['email'] = email
        session['username'] = client_username
        session.permanent = True
        
        logger.info(f"✅ Client login successful: {username} ({company_name})")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user_type': 'client',
            'client_id': client_id,
            'company_name': company_name,
            'username': client_username,
            'email': email
        })
        
    except Exception as e:
        logger.error(f"Client login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Login error',
            'error': str(e)
        }), 500


# ============================================================================
# CLIENT MANAGEMENT APIs
# ============================================================================

@auth_bp.route('/api/admin/clients', methods=['GET'])
def get_all_clients():
    """Get all clients for admin"""
    try:
        from modules.shared.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, company_name, contact_email, contact_name, phone_number, 
                   username, is_active, last_login, created_at, business_type,
                   city, state, country
            FROM clients
            ORDER BY created_at DESC
        ''')
        
        clients = []
        for row in cursor.fetchall():
            clients.append({
                'id': row[0],
                'company_name': row[1],
                'contact_email': row[2],
                'contact_name': row[3],
                'phone_number': row[4],
                'username': row[5],
                'is_active': row[6],
                'last_login': row[7],
                'created_at': row[8],
                'business_type': row[9],
                'city': row[10],
                'state': row[11],
                'country': row[12]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'clients': clients,
            'total': len(clients)
        })
        
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/admin/clients', methods=['POST'])
def create_client():
    """Create new client"""
    try:
        from modules.shared.database import get_db_connection, generate_id
        import hashlib
        
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'message': 'Username is required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute('SELECT id FROM clients WHERE username = ?', (username,))
        existing_client = cursor.fetchone()
        
        if existing_client:
            conn.close()
            return jsonify({
                'success': False,
                'message': f'Username "{username}" already exists. Please choose a different username.'
            }), 400
        
        # Check if email already exists
        email = data.get('contact_email', '').strip()
        if email:
            cursor.execute('SELECT id FROM clients WHERE contact_email = ?', (email,))
            existing_email = cursor.fetchone()
            
            if existing_email:
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Email "{email}" already exists. Please use a different email.'
                }), 400
        
        # Generate client ID
        client_id = generate_id()
        
        # Hash password
        password = data.get('password', 'admin123')
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO clients (
                id, company_name, contact_email, contact_name, phone_number,
                username, password_hash, is_active, business_type, country
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_id,
            data.get('company_name'),
            data.get('contact_email'),
            data.get('contact_name'),
            data.get('phone_number'),
            username,
            password_hash,
            1,
            data.get('business_type', 'retail'),
            data.get('country', 'India')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Client created successfully',
            'client_id': client_id
        })
        
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/admin/clients/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete client"""
    try:
        from modules.shared.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM clients WHERE id = ?', (client_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Client deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/api/admin/login-as-client', methods=['POST'])
def login_as_client():
    """Admin login as client"""
    try:
        data = request.get_json()
        client_id = data.get('clientId')
        
        from modules.shared.database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, company_name, contact_email, username
            FROM clients
            WHERE id = ?
        ''', (client_id,))
        
        client = cursor.fetchone()
        conn.close()
        
        if client:
            # Set session as this client
            session['user_id'] = client[0]
            session['user_type'] = 'client'
            session['user_name'] = client[1]
            session['email'] = client[2]
            session['username'] = client[3]
            session.permanent = True
            
            return jsonify({
                'success': True,
                'message': 'Logged in as client',
                'redirect': '/retail/dashboard'
            })
        else:
            return jsonify({'success': False, 'message': 'Client not found'}), 404
        
    except Exception as e:
        logger.error(f"Error logging in as client: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
