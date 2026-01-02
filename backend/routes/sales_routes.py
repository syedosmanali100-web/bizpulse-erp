"""
Production-Grade Sales API Routes
Clean sales reporting and analytics endpoints
"""

from flask import Blueprint, request, jsonify
from services.sales_service import SalesService
from functools import wraps

# Create blueprint
sales_bp = Blueprint('sales', __name__)

# Initialize service
sales_service = SalesService()

def require_auth(f):
    """Authentication decorator - implement based on your auth system"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, we'll skip auth for testing
        return f(*args, **kwargs)
    return decorated_function

@sales_bp.route('/api/sales', methods=['GET'])
@require_auth
def get_sales():
    """
    Get sales data with filtering options
    
    Query parameters:
    - filter: today, yesterday, week, month, custom, all
    - from_date: YYYY-MM-DD (for custom filter)
    - to_date: YYYY-MM-DD (for custom filter)
    - limit: number of records
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('filter'):
            filters['filter'] = request.args.get('filter')
        
        if request.args.get('from_date'):
            filters['from_date'] = request.args.get('from_date')
        
        if request.args.get('to_date'):
            filters['to_date'] = request.args.get('to_date')
        
        if request.args.get('limit'):
            try:
                filters['limit'] = int(request.args.get('limit'))
            except ValueError:
                filters['limit'] = 100
        
        # Get sales using service
        success, result = sales_service.get_sales(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@sales_bp.route('/api/sales/summary', methods=['GET'])
@require_auth
def get_sales_summary():
    """Get sales summary for different time periods"""
    try:
        success, result = sales_service.get_sales_summary()
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@sales_bp.route('/api/sales/by-product', methods=['GET'])
@require_auth
def get_sales_by_product():
    """
    Get sales grouped by product
    
    Query parameters:
    - from: YYYY-MM-DD
    - to: YYYY-MM-DD
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('from'):
            filters['from'] = request.args.get('from')
        
        if request.args.get('to'):
            filters['to'] = request.args.get('to')
        
        # Get sales by product using service
        success, result = sales_service.get_sales_by_product(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@sales_bp.route('/api/sales/by-category', methods=['GET'])
@require_auth
def get_sales_by_category():
    """
    Get sales grouped by category
    
    Query parameters:
    - from: YYYY-MM-DD
    - to: YYYY-MM-DD
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('from'):
            filters['from'] = request.args.get('from')
        
        if request.args.get('to'):
            filters['to'] = request.args.get('to')
        
        # Get sales by category using service
        success, result = sales_service.get_sales_by_category(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500