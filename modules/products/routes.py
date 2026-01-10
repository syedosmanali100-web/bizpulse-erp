"""
Products routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, request, jsonify, session
from .service import ProductsService
from .variants_service import ProductVariantsService
from modules.shared.auth_decorators import require_auth
from modules.shared.database import get_current_client_id

products_bp = Blueprint('products', __name__)
products_service = ProductsService()
variants_service = ProductVariantsService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')  # For employees, use client_id
    else:
        return session.get('user_id')    # For clients/users, use user_id

@products_bp.route('/api/products', methods=['GET'])
def get_products():
    """Get products filtered by user_id for Desktop-Mobile sync"""
    conn = products_service.get_db_connection()
    
    # 🔥 Get user_id for filtering
    user_id = get_user_id_from_session()
    
    if user_id:
        # Filter by user_id for multi-tenant support
        products = conn.execute('SELECT * FROM products WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)', (user_id,)).fetchall()
    else:
        # Fallback: show all products if no user_id (backward compatibility)
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
def add_product():
    """Add new product - Mobile ERP compatible - With user_id for sync"""
    try:
        data = request.json
        print(f"[PRODUCT ADD API] Received data: {data}")
        
        # Validate JSON data
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        # 🔥 Add user_id to data for multi-tenant support
        user_id = get_user_id_from_session()
        if user_id:
            data['user_id'] = user_id
            print(f"[PRODUCT ADD API] Adding product for user: {user_id}")
        
        result = products_service.add_product(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            status_code = 409 if 'already exists' in result.get('error', '') else 400
            return jsonify(result), status_code
        
    except ValueError as e:
        print(f"[PRODUCT ADD API] ValueError: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
    except Exception as e:
        print(f"[PRODUCT ADD API] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@products_bp.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update an existing product - Mobile ERP compatible"""
    try:
        data = request.json
        print(f"[PRODUCT UPDATE API] Updating product {product_id} with data: {data}")
        
        result = products_service.update_product(product_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            status_code = 409 if 'already exists' in result.get('error', '') else 404 if 'not found' in result.get('error', '') else 400
            return jsonify(result), status_code
        
    except ValueError as e:
        print(f"[PRODUCT UPDATE API] ValueError: {e}")
        return jsonify({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }), 400
        
    except Exception as e:
        print(f"[PRODUCT UPDATE API] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to update product: {str(e)}"
        }), 500

@products_bp.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete product completely from database - Mobile ERP compatible"""
    try:
        print(f"[PRODUCT DELETE API] Deleting product: {product_id}")
        
        result = products_service.delete_product(product_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        print(f"[PRODUCT DELETE API] Exception: {e}")
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

        result = products_service.recommend_product_images(product_name, category)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/alerts', methods=['GET'])
def get_product_alerts():
    """
    Get product alerts for:
    - Low stock products
    - Out of stock products
    - Products expiring soon (within 7 days)
    - Expired products
    """
    try:
        from datetime import datetime, timedelta
        
        conn = products_service.get_db_connection()
        user_id = get_user_id_from_session()
        
        # Get current date
        today = datetime.now().date()
        expiry_threshold = (today + timedelta(days=7)).isoformat()
        
        alerts = {
            'low_stock': [],
            'out_of_stock': [],
            'expiring_soon': [],
            'expired': []
        }
        
        # Build query based on user_id
        if user_id:
            base_query = 'SELECT * FROM products WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)'
            products = conn.execute(base_query, (user_id,)).fetchall()
        else:
            products = conn.execute('SELECT * FROM products WHERE is_active = 1').fetchall()
        
        for product in products:
            product_dict = dict(product)
            
            # Check stock levels
            if product_dict['stock'] == 0:
                alerts['out_of_stock'].append({
                    'id': product_dict['id'],
                    'name': product_dict['name'],
                    'category': product_dict['category'],
                    'stock': product_dict['stock'],
                    'message': f"{product_dict['name']} is out of stock"
                })
            elif product_dict['stock'] <= product_dict.get('min_stock', 0):
                alerts['low_stock'].append({
                    'id': product_dict['id'],
                    'name': product_dict['name'],
                    'category': product_dict['category'],
                    'stock': product_dict['stock'],
                    'min_stock': product_dict.get('min_stock', 0),
                    'message': f"{product_dict['name']} is low on stock ({product_dict['stock']} remaining)"
                })
            
            # Check expiry dates
            if product_dict.get('expiry_date'):
                try:
                    expiry_date = datetime.fromisoformat(product_dict['expiry_date']).date()
                    
                    if expiry_date < today:
                        alerts['expired'].append({
                            'id': product_dict['id'],
                            'name': product_dict['name'],
                            'category': product_dict['category'],
                            'expiry_date': product_dict['expiry_date'],
                            'days_expired': (today - expiry_date).days,
                            'message': f"{product_dict['name']} expired {(today - expiry_date).days} days ago"
                        })
                    elif expiry_date <= (today + timedelta(days=7)):
                        days_until_expiry = (expiry_date - today).days
                        alerts['expiring_soon'].append({
                            'id': product_dict['id'],
                            'name': product_dict['name'],
                            'category': product_dict['category'],
                            'expiry_date': product_dict['expiry_date'],
                            'days_until_expiry': days_until_expiry,
                            'message': f"{product_dict['name']} expires in {days_until_expiry} days",
                            'priority': 'high' if days_until_expiry <= 3 else 'medium'
                        })
                except (ValueError, TypeError):
                    pass  # Skip invalid dates
        
        # Sort expiring_soon by days_until_expiry (most urgent first)
        alerts['expiring_soon'].sort(key=lambda x: x['days_until_expiry'])
        
        # Calculate totals
        total_alerts = (
            len(alerts['low_stock']) + 
            len(alerts['out_of_stock']) + 
            len(alerts['expiring_soon']) + 
            len(alerts['expired'])
        )
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_alerts': total_alerts,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ALERTS API] Exception: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========== PRODUCT VARIANTS ROUTES ==========

@products_bp.route('/api/products/<product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """Get all variants for a product"""
    try:
        variants = variants_service.get_product_variants(product_id)
        
        return jsonify({
            "success": True,
            "variants": variants,
            "total": len(variants)
        })
        
    except Exception as e:
        print(f"[VARIANTS GET] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@products_bp.route('/api/products/<product_id>/variants', methods=['POST'])
def add_product_variant(product_id):
    """Add a variant to a product"""
    try:
        data = request.json
        print(f"[VARIANT ADD] Adding variant to product {product_id}: {data}")
        
        result = variants_service.add_variant(product_id, data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        print(f"[VARIANT ADD] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@products_bp.route('/api/products/variants/<variant_id>', methods=['PUT'])
def update_product_variant(variant_id):
    """Update a variant"""
    try:
        data = request.json
        print(f"[VARIANT UPDATE] Updating variant {variant_id}: {data}")
        
        result = variants_service.update_variant(variant_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
        
    except Exception as e:
        print(f"[VARIANT UPDATE] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@products_bp.route('/api/products/variants/<variant_id>', methods=['DELETE'])
def delete_product_variant(variant_id):
    """Delete a variant"""
    try:
        print(f"[VARIANT DELETE] Deleting variant {variant_id}")
        
        result = variants_service.delete_variant(variant_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
        
    except Exception as e:
        print(f"[VARIANT DELETE] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
