"""
Settings routes - Notification settings
"""

from flask import Blueprint, request, jsonify, session
from modules.shared.database import get_db_connection, generate_id
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

def get_user_id_from_session():
    """Get user_id from session"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id', 'demo-user-123')

@settings_bp.route('/api/settings/notifications', methods=['GET'])
def get_notification_settings():
    """Get notification settings for current user"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        settings = conn.execute('''
            SELECT * FROM notification_settings 
            WHERE user_id = ? OR user_id IS NULL
            ORDER BY setting_type
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'settings': [dict(row) for row in settings]
        })
        
    except Exception as e:
        print(f"[SETTINGS API] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/notifications/<setting_id>', methods=['PUT'])
def update_notification_setting(setting_id):
    """Update a notification setting"""
    try:
        data = request.json
        conn = get_db_connection()
        
        # Check if setting exists
        setting = conn.execute('SELECT * FROM notification_settings WHERE id = ?', (setting_id,)).fetchone()
        
        if not setting:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Setting not found'
            }), 404
        
        # Update setting
        conn.execute('''
            UPDATE notification_settings 
            SET enabled = ?, threshold_days = ?, frequency_per_day = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('enabled', setting['enabled']),
            data.get('threshold_days', setting['threshold_days']),
            data.get('frequency_per_day', setting['frequency_per_day']),
            setting_id
        ))
        
        conn.commit()
        
        # Get updated setting
        updated_setting = conn.execute('SELECT * FROM notification_settings WHERE id = ?', (setting_id,)).fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Setting updated successfully',
            'setting': dict(updated_setting)
        })
        
    except Exception as e:
        print(f"[SETTINGS API] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/notifications', methods=['POST'])
def create_notification_setting():
    """Create a new notification setting"""
    try:
        data = request.json
        user_id = get_user_id_from_session()
        
        conn = get_db_connection()
        
        setting_id = generate_id()
        
        conn.execute('''
            INSERT INTO notification_settings 
            (id, user_id, setting_type, enabled, threshold_days, frequency_per_day)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            setting_id,
            user_id,
            data.get('setting_type'),
            data.get('enabled', 1),
            data.get('threshold_days', 7),
            data.get('frequency_per_day', 2)
        ))
        
        conn.commit()
        
        # Get created setting
        new_setting = conn.execute('SELECT * FROM notification_settings WHERE id = ?', (setting_id,)).fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Setting created successfully',
            'setting': dict(new_setting)
        }), 201
        
    except Exception as e:
        print(f"[SETTINGS API] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@settings_bp.route('/api/settings/business', methods=['GET'])
def get_business_settings():
    """Get business settings for receipts and invoices"""
    try:
        user_id = get_user_id_from_session()
        
        # Return default settings for now
        # In future, fetch from database based on user_id
        return jsonify({
            'success': True,
            'settings': {
                'business_name': 'BizPulse ERP',
                'address': 'Your Business Address',
                'phone': '040-12345678',
                'gstin': '36AAFCP6142N1Z2',
                'email': 'info@bizpulse.com'
            }
        })
        
    except Exception as e:
        print(f"[SETTINGS API] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
