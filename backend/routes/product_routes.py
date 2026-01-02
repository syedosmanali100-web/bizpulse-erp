"""
Production-Grade Product API Routes
Clean product management endpoints
"""

from flask import Blueprint, request, jsonify
from services.product_service import ProductService
from functools import wraps

# Create blueprint
product_bp = Blueprint('products', __name__)

# Initialize service
product_service = ProductService()

def require_auth(f):
    """Authentication decorator - implement based on your auth system"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, we'll skip auth for testing
        return f(*args, **kwargs)
    return decorated_function

@product_bp.route('/api/products', methods=['GET'])
@require_auth
def get_products():
    """
    Get products with optional filtering
    
    Query parameters:
    - category: filter by category
    - low_stock: true/false - show only low stock items
    - search: search in name or code
    - limit: number of records
    """
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        
        if request.args.get('low_stock') == 'true':
            filters['low_stock'] = True
        
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        if request.args.get('limit'):
            try:
                filters['limit'] = int(request.args.get('limit'))
            except ValueError:
                filters['limit'] = 100
        
        # Get products using service
        success, result = product_service.get_products(filters)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@product_bp.route('/api/products/<product_id>', methods=['GET'])
@require_auth
def get_product_by_id(product_id):
    """Get product by ID"""
    try:
        success, result = product_service.get_product_by_id(product_id)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@product_bp.route('/api/products/barcode/<barcode>', methods=['GET'])
@require_auth
def get_product_by_barcode(barcode):
    """Get product by barcode"""
    try:
        success, result = product_service.get_product_by_barcode(barcode)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@product_bp.route('/api/products', methods=['POST'])
@require_auth
def create_product():
    """
    Create new product
    
    Expected JSON:
    {
        "name": "Product Name",
        "category": "Category",
        "price": 100.0,
        "cost": 80.0,
        "stock": 50,
        "min_stock": 10,
        "unit": "piece",
        "barcode_data": "1234567890"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        # Create product using service
        success, result = product_service.create_product(data)
        
        if success:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@product_bp.route('/api/products/<product_id>', methods=['PUT'])
@require_auth
def update_product(product_id):
    """Update product (excluding stock - stock is managed by billing)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        # Update product using service
        success, result = product_service.update_product(product_id, data)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@product_bp.route('/api/products/<product_id>', methods=['DELETE'])
@require_auth
def delete_product(product_id):
    """Soft delete product"""
    try:
        success, result = product_service.delete_product(product_id)
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500