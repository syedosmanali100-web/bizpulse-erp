"""
RBAC API Routes
Super Admin, Tenant, and Permission endpoints
"""

from flask import Blueprint, request, jsonify, render_template, session
from .super_admin_service import SuperAdminService
from .security import require_super_admin, require_auth
import logging

logger = logging.getLogger(__name__)

rbac_bp = Blueprint('rbac', __name__)
super_admin_service = SuperAdminService()

# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@rbac_bp.route('/rbac/super-admin/login')
def super_admin_login_page():
    """Super Admin Login Page"""
    return render_template('rbac_super_admin_login.html')

@rbac_bp.route('/rbac/super-admin/dashboard')
def super_admin_dashboard():
    """Super Admin Dashboard"""
    return render_template('rbac_super_admin_dashboard.html')

@rbac_bp.route('/client-management')
def client_management_page():
    """Client Management Page (redirects to RBAC dashboard)"""
    # Check if user is already logged in as BizPulse admin
    if session.get('email') == 'bizpulse.erp@gmail.com':
        # Already logged in with existing system
        return render_template('rbac_super_admin_dashboard.html')
    elif session.get('rbac_user_type') == 'super_admin':
        # Logged in with RBAC system
        return render_template('rbac_super_admin_dashboard.html')
    else:
        # Not logged in, redirect to existing login
        from flask import redirect, url_for
        return redirect('/login')

# ============================================================================
# SUPER ADMIN API ROUTES
# ============================================================================

@rbac_bp.route('/api/rbac/super-admin/login', methods=['POST'])
def api_super_admin_login():
    """Super Admin Login API"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'}), 400
        
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        result = super_admin_service.login(username, password, ip_address, user_agent)
        
        if result['success']:
            # Store in session for web access
            session['rbac_user_id'] = result['user']['id']
            session['rbac_user_type'] = 'super_admin'
            session['rbac_username'] = result['user']['username']
            session.permanent = True
            
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    
    except Exception as e:
        logger.error(f"Super admin login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/logout', methods=['POST'])
def api_super_admin_logout():
    """Super Admin Logout"""
    session.pop('rbac_user_id', None)
    session.pop('rbac_user_type', None)
    session.pop('rbac_username', None)
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@rbac_bp.route('/api/rbac/super-admin/clients', methods=['GET'])
def api_get_clients():
    """Get all clients"""
    try:
        # Debug logging
        print(f"[DEBUG GET] Session: {dict(session)}")
        
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        print(f"[DEBUG GET] RBAC admin: {is_rbac_admin}, Existing admin: {is_existing_admin}")
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized - Please login'}), 401
        
        # Get filters from query params
        filters = {
            'status': request.args.get('status'),
            'plan_type': request.args.get('plan_type'),
            'search': request.args.get('search')
        }
        
        result = super_admin_service.get_all_clients(filters)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Get clients error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients', methods=['POST'])
def api_create_client():
    """Create new client"""
    try:
        # Debug logging
        print(f"[DEBUG POST] Session: {dict(session)}")
        
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        print(f"[DEBUG POST] RBAC admin: {is_rbac_admin}, Existing admin: {is_existing_admin}")
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized - Please login first'}), 401
        
        data = request.get_json()
        created_by = session.get('rbac_user_id') or session.get('user_id')
        
        result = super_admin_service.create_client(data, created_by)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Create client error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>', methods=['GET'])
def api_get_client_details(client_id):
    """Get client details"""
    try:
        # Debug logging
        print(f"[DEBUG DETAILS] Session: {dict(session)}")
        print(f"[DEBUG DETAILS] Client ID: {client_id}")
        
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        print(f"[DEBUG DETAILS] RBAC admin: {is_rbac_admin}, Existing admin: {is_existing_admin}")
        
        if not (is_rbac_admin or is_existing_admin):
            print(f"[DEBUG DETAILS] Authorization failed!")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        print(f"[DEBUG DETAILS] Calling service...")
        result = super_admin_service.get_client_details(client_id)
        print(f"[DEBUG DETAILS] Service result: {result.get('success')}")
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Get client details error: {e}")
        print(f"[DEBUG DETAILS] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>', methods=['PUT'])
def api_update_client(client_id):
    """Update client"""
    try:
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        updated_by = session.get('rbac_user_id') or session.get('user_id')
        
        result = super_admin_service.update_client(client_id, data, updated_by)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Update client error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>/reset-password', methods=['POST'])
def api_reset_client_password(client_id):
    """Reset client password"""
    try:
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        reset_by = session.get('rbac_user_id') or session.get('user_id')
        result = super_admin_service.reset_client_password(client_id, reset_by)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>/toggle-status', methods=['POST'])
def api_toggle_client_status(client_id):
    """Toggle client status (activate/suspend/expire)"""
    try:
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        action = data.get('action')  # activate, suspend, expire
        reason = data.get('reason', '')
        changed_by = session.get('rbac_user_id') or session.get('user_id')
        
        result = super_admin_service.toggle_client_status(client_id, action, reason, changed_by)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Toggle status error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>/force-logout', methods=['POST'])
def api_force_logout_client(client_id):
    """Force logout all client sessions"""
    try:
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        logged_out_by = session.get('rbac_user_id') or session.get('user_id')
        result = super_admin_service.force_logout_client(client_id, logged_out_by)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Force logout error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@rbac_bp.route('/api/rbac/super-admin/clients/<client_id>/subscription', methods=['POST'])
def api_update_subscription(client_id):
    """Update client subscription"""
    try:
        # Check session (allow both RBAC and existing admin)
        is_rbac_admin = session.get('rbac_user_type') == 'super_admin'
        is_existing_admin = session.get('email') == 'bizpulse.erp@gmail.com'
        
        if not (is_rbac_admin or is_existing_admin):
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        plan_type = data.get('plan_type')
        duration_days = data.get('duration_days')
        amount = data.get('amount', 0)
        changed_by = session.get('rbac_user_id') or session.get('user_id')
        
        result = super_admin_service.update_subscription(
            client_id, plan_type, duration_days, amount, changed_by
        )
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Update subscription error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@rbac_bp.route('/api/rbac/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'RBAC system is running',
        'version': '1.0.0'
    })
