"""
Billing routes
COPIED AS-IS from app_original_backup.py
"""

from flask import Blueprint, request, jsonify, session
from .service import BillingService
from modules.shared.auth_decorators import require_auth

billing_bp = Blueprint('billing', __name__)
billing_service = BillingService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

@billing_bp.route('/api/bills', methods=['GET'])
def get_bills():
    """Get all bills with customer information - Mobile ERP Style - Filtered by user"""
    try:
        user_id = get_user_id_from_session()
        result = billing_service.get_all_bills(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills/<bill_id>/items', methods=['GET'])
def get_bill_items(bill_id):
    """Get items for a specific bill - Mobile ERP Style"""
    try:
        result = billing_service.get_bill_items(bill_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@billing_bp.route('/api/bills', methods=['POST'])
def create_bill():
    """Create bill - Mobile ERP Perfect Implementation - With user_id"""
    try:
        data = request.json
        print("📥 [BILLING] Received bill data:", data)
        print(f"🔍 [BILLING] Payment Method: {data.get('payment_method')}")
        print(f"🔍 [BILLING] Partial Amount: {data.get('partial_amount')}")
        print(f"🔍 [BILLING] Partial Payment Method: {data.get('partial_payment_method')}")
        
        # 🔥 Add business_owner_id for multi-tenant support
        user_id = get_user_id_from_session()
        if user_id:
            data['business_owner_id'] = user_id
            print(f"🔍 [BILLING] business_owner_id: {user_id}")
        
        result = billing_service.create_bill(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        import traceback
        print(f"❌ [BILLING] Error creating bill: {e}")
        print(f"❌ [BILLING] Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e), "success": False}), 500