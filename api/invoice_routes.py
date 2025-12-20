"""
Production-Grade Invoice API Routes
Clean invoice management endpoints
"""

from flask import Blueprint, request, jsonify
from services.invoice_service import InvoiceService
from functools import wraps

# Create blueprint
invoice_bp = Blueprint('invoices', __name__)

# Initialize service
invoice_service = InvoiceService()

def require_auth(f):
    """Authentication decorator - implement based on your auth system"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, we'll skip auth for testing
        return f(*args, **kwargs)
    return decorated_function

@invoice_bp.route('/api/invoices', methods=['POST'])
@require_auth
def create_invoice():
    """
    Create a new invoice (source of truth for all transactions)
    
    Expected JSON:
    {
        "items": [
            {
                "product_id": "prod-1",
                "product_name": "Rice 1kg",
                "quantity": 2,
                "unit_price": 80.0
            }
        ],
        "total_amount": 160.0,
        "customer_id": "cust-1",
        "payment_method": "cash",
        "tax_amount": 0,
        "discount_amount": 0
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        # Create invoice using service
        success, result = invoice_service.create_invoice(data)
        
        if success:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@invoice_bp.route('/api/invoices', methods=['GET'])
@require_auth
def get_invoices():
    """
    Get invoices with optional filtering
    
    Query parameters:
    - status: completed, pending, cancelled
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    - limit: number of records
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        if request.args.get('limit'):
            try:
                filters['limit'] = int(request.args.get('limit'))
            except ValueError:
                filters['limit'] = 50
        
        # Get invoices using service
        success, result = invoice_service.get_invoices(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@invoice_bp.route('/api/invoices/<invoice_id>', methods=['GET'])
@require_auth
def get_invoice_by_id(invoice_id):
    """Get invoice details by ID"""
    try:
        success, result = invoice_service.get_invoice_by_id(invoice_id)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@invoice_bp.route('/api/invoices/<invoice_id>', methods=['DELETE'])
@require_auth
def delete_invoice(invoice_id):
    """Delete invoice and revert all changes"""
    try:
        success, result = invoice_service.delete_invoice(invoice_id)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@invoice_bp.route('/api/invoices/summary', methods=['GET'])
@require_auth
def get_invoice_summary():
    """
    Get invoice summary statistics
    
    Query parameters:
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        # Get summary using service
        success, result = invoice_service.get_invoice_summary(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500