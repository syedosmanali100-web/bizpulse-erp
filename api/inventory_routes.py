"""
Production-Grade Inventory API Routes
Clean inventory management endpoints
"""

from flask import Blueprint, request, jsonify
from services.inventory_service import InventoryService
from functools import wraps

# Create blueprint
inventory_bp = Blueprint('inventory', __name__)

# Initialize service
inventory_service = InventoryService()

def require_auth(f):
    """Authentication decorator - implement based on your auth system"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, we'll skip auth for testing
        return f(*args, **kwargs)
    return decorated_function

@inventory_bp.route('/api/inventory', methods=['GET'])
@require_auth
def get_inventory_status():
    """Get complete inventory status with stock levels and alerts"""
    try:
        success, result = inventory_service.get_inventory_status()
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@inventory_bp.route('/api/inventory/low-stock', methods=['GET'])
@require_auth
def get_low_stock_items():
    """Get items with low stock that need attention"""
    try:
        success, result = inventory_service.get_low_stock_items()
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@inventory_bp.route('/api/inventory/sync', methods=['POST'])
@require_auth
def sync_inventory():
    """Sync inventory with sales data for consistency checks"""
    try:
        success, result = inventory_service.sync_inventory()
        
        if success:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500