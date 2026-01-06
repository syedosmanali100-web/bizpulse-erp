"""
Customers API routes
"""

from flask import Blueprint, request, jsonify, session
from .service import CustomersService
from modules.shared.auth_decorators import require_auth

customers_bp = Blueprint('customers', __name__)
customers_service = CustomersService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

@customers_bp.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers - Mobile ERP compatible - Filtered by user"""
    try:
        user_id = get_user_id_from_session()
        result = customers_service.get_all_customers(user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@customers_bp.route('/api/customers', methods=['POST'])
def add_customer():
    """Add new customer - Mobile ERP compatible - With user_id"""
    try:
        data = request.json
        print(f"[CUSTOMER ADD API] Received data: {data}")
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # 🔥 Add user_id for multi-tenant support
        user_id = get_user_id_from_session()
        if user_id:
            data['user_id'] = user_id
            print(f"[CUSTOMER ADD API] Adding customer for user: {user_id}")
        
        result = customers_service.add_customer(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except ValueError as e:
        print(f"[CUSTOMER ADD API] ValueError: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        print(f"[CUSTOMER ADD API] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@customers_bp.route('/api/customers/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update an existing customer - Mobile ERP compatible"""
    try:
        data = request.json
        print(f"[CUSTOMER UPDATE API] Updating customer {customer_id} with data: {data}")
        
        result = customers_service.update_customer(customer_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 404 if 'not found' in result.get('error', '') else 400
            return jsonify(result), status_code
        
    except ValueError as e:
        print(f"[CUSTOMER UPDATE API] ValueError: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"[CUSTOMER UPDATE API] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to update customer: {str(e)}"
        }), 500

@customers_bp.route('/api/customers/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete customer - Mobile ERP compatible"""
    try:
        print(f"[CUSTOMER DELETE API] Deleting customer: {customer_id}")
        
        result = customers_service.delete_customer(customer_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        print(f"[CUSTOMER DELETE API] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to delete customer: {str(e)}"
        }), 500

@customers_bp.route('/api/customers/search', methods=['GET'])
def search_customers():
    """Search customers by name or phone - Filtered by user"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Search query is required"
            }), 400
        
        user_id = get_user_id_from_session()
        result = customers_service.search_customers(query, user_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500