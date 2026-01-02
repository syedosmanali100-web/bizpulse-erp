"""
Products routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, request, jsonify
from .service import ProductsService
from modules.shared.auth_decorators import require_auth

products_bp = Blueprint('products', __name__)
products_service = ProductsService()

@products_bp.route('/api/products', methods=['GET'])
def get_products():
    conn = products_service.get_db_connection()
    products = conn.execute('SELECT * FROM products WHERE is_active = 1').fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

@products_bp.route('/api/products/debug', methods=['GET'])
def debug_products():
    """Debug endpoint to see all products with barcode data"""
    try:
        result = products_service.debug_products()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@products_bp.route('/api/test/barcode/<barcode>', methods=['GET'])
def test_barcode_route(barcode):
    """Simple test route to check if barcode routes work"""
    return jsonify({
        "success": True,
        "message": f"Barcode route working! Received: {barcode}",
        "timestamp": products_service.get_current_timestamp()
    })

@products_bp.route('/api/products/<product_id>/add-barcode', methods=['POST'])
def add_barcode_to_product(product_id):
    """Add barcode to existing product"""
    try:
        data = request.json
        barcode = data.get('barcode', '').strip()
        
        if not barcode:
            return jsonify({"success": False, "error": "Barcode is required"}), 400
        
        result = products_service.add_barcode_to_product(product_id, barcode)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@products_bp.route('/api/products/search/barcode/<barcode>', methods=['GET'])
def search_product_by_barcode(barcode):
    """⚡ FAST barcode search - Optimized for instant response"""
    try:
        result = products_service.search_product_by_barcode(barcode)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Search failed",
            "barcode": barcode
        }), 500

@products_bp.route('/api/products/barcode-to-cart/<barcode>', methods=['POST'])
def barcode_to_cart(barcode):
    """⚡ INSTANT barcode-to-cart - For billing system"""
    try:
        # ⚡ LIGHTNING-FAST barcode lookup
        result = products_service.search_product_by_barcode(barcode)
        
        if result['success']:
            product = result['product']
            
            # ⚡ INSTANT CART ITEM FORMAT - Ready for billing
            cart_item = {
                "product_id": product['id'],
                "product_name": product['name'],
                "unit_price": product['price'],
                "quantity": 1,  # Default quantity
                "total_price": product['price'],
                "stock_available": product['stock'],
                "unit": product['unit'],
                "barcode": product['barcode_data']
            }
            
            return jsonify({
                "success": True,
                "cart_item": cart_item,
                "message": f"Added {product['name']} to cart"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Product not found",
                "barcode": barcode
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Failed to add to cart",
            "barcode": barcode
        }), 500

@products_bp.route('/api/products', methods=['POST'])
@require_auth
def add_product():
    try:
        data = request.json
        result = products_service.add_product(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            status_code = 409 if 'already exists' in result.get('error', '') else 400
            return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to add product: {str(e)}"
        }), 500

@products_bp.route('/api/products/<product_id>', methods=['PUT'])
@require_auth
def update_product(product_id):
    """Update an existing product"""
    try:
        data = request.json
        result = products_service.update_product(product_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 409 if 'already exists' in result.get('error', '') else 404 if 'not found' in result.get('error', '') else 400
            return jsonify(result), status_code
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to update product: {str(e)}"
        }), 500

@products_bp.route('/api/products/<product_id>', methods=['DELETE'])
@require_auth
def delete_product(product_id):
    """Delete product completely from database"""
    try:
        result = products_service.delete_product(product_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete product: {str(e)}"
        }), 500

@products_bp.route('/api/products/recommend-images', methods=['POST'])
def recommend_product_images():
    """
    Recommend product images based on name and category
    Uses Unsplash API for high-quality, royalty-free images
    """
    try:
        data = request.json
        product_name = data.get('product_name', '').strip()
        category = data.get('category', '').strip()
        
        if not product_name:
            return jsonify({
                'success': False,
                'error': 'Product name is required'
            }), 400
        
        result = products_service.recommend_product_images(product_name, category)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch image recommendations. Please try again.'
        }), 500