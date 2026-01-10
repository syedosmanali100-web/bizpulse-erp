"""
E-Way Bill Routes
Handle E-Way Bill generation and management
"""

from flask import Blueprint, request, jsonify, render_template, session
from .service import eway_service
from modules.shared.auth_decorators import require_auth
import logging

logger = logging.getLogger(__name__)

eway_bp = Blueprint('eway', __name__, url_prefix='/api/eway')

@eway_bp.route('/check-requirement', methods=['POST'])
@require_auth
def check_eway_requirement():
    """Check if E-Way Bill is required for invoice"""
    try:
        data = request.json
        invoice_value = float(data.get('invoice_value', 0))
        from_state = data.get('from_state', '')
        to_state = data.get('to_state', '')
        
        is_required = eway_service.check_eway_requirement(invoice_value, from_state, to_state)
        
        return jsonify({
            'success': True,
            'is_required': is_required,
            'threshold': eway_service.eway_threshold,
            'message': f'E-Way Bill {"required" if is_required else "not required"} for this invoice'
        })
        
    except Exception as e:
        logger.error(f"❌ E-Way Bill requirement check error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/generate', methods=['POST'])
@require_auth
def generate_eway_bill():
    """Generate E-Way Bill for invoice"""
    try:
        data = request.json
        user_id = session.get('user_id')
        
        # Add user info to data
        data['generated_by'] = user_id
        data['business_owner_id'] = session.get('business_owner_id', user_id)
        
        success, result = eway_service.create_eway_bill(data)
        
        if success:
            return jsonify({
                'success': True,
                'data': result,
                'message': 'E-Way Bill generated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': result
            }), 400
            
    except Exception as e:
        logger.error(f"❌ E-Way Bill generation error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/list', methods=['GET'])
@require_auth
def get_eway_bills():
    """Get list of E-Way Bills"""
    try:
        user_id = session.get('user_id')
        business_owner_id = session.get('business_owner_id', user_id)
        
        # Get filters from query parameters
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('from_date'):
            filters['from_date'] = request.args.get('from_date')
        if request.args.get('to_date'):
            filters['to_date'] = request.args.get('to_date')
        
        eway_bills = eway_service.get_eway_bills(business_owner_id, filters)
        
        return jsonify({
            'success': True,
            'data': eway_bills,
            'total_count': len(eway_bills),
            'message': f'Retrieved {len(eway_bills)} E-Way Bills'
        })
        
    except Exception as e:
        logger.error(f"❌ Get E-Way Bills error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/<eway_bill_id>', methods=['GET'])
@require_auth
def get_eway_bill_details(eway_bill_id):
    """Get E-Way Bill details by ID"""
    try:
        eway_bill = eway_service.get_eway_bill_by_id(eway_bill_id)
        
        if eway_bill:
            return jsonify({
                'success': True,
                'data': eway_bill,
                'message': 'E-Way Bill details retrieved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'E-Way Bill not found'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Get E-Way Bill details error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/<eway_bill_id>/cancel', methods=['POST'])
@require_auth
def cancel_eway_bill(eway_bill_id):
    """Cancel E-Way Bill"""
    try:
        data = request.json
        reason = data.get('reason', 'Cancelled by user')
        user_id = session.get('user_id')
        
        success, message = eway_service.cancel_eway_bill(eway_bill_id, reason, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Cancel E-Way Bill error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/settings', methods=['GET'])
@require_auth
def get_eway_settings():
    """Get E-Way Bill settings"""
    try:
        user_id = session.get('user_id')
        business_owner_id = session.get('business_owner_id', user_id)
        
        settings = eway_service.get_eway_settings(business_owner_id)
        
        return jsonify({
            'success': True,
            'data': settings,
            'message': 'E-Way Bill settings retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Get E-Way Bill settings error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@eway_bp.route('/settings', methods=['POST'])
@require_auth
def update_eway_settings():
    """Update E-Way Bill settings"""
    try:
        data = request.json
        user_id = session.get('user_id')
        business_owner_id = session.get('business_owner_id', user_id)
        
        success, message = eway_service.update_eway_settings(business_owner_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Update E-Way Bill settings error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Frontend routes
@eway_bp.route('/manage', methods=['GET'])
@require_auth
def eway_management_page():
    """E-Way Bill management page"""
    return render_template('eway_management.html')

@eway_bp.route('/generate-form', methods=['GET'])
@require_auth
def eway_generate_form():
    """E-Way Bill generation form"""
    invoice_id = request.args.get('invoice_id')
    return render_template('eway_generate_form.html', invoice_id=invoice_id)

@eway_bp.route('/settings-page', methods=['GET'])
@require_auth
def eway_settings_page():
    """E-Way Bill settings page"""
    return render_template('eway_settings.html')