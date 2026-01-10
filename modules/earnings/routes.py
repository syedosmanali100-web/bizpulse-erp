"""
Earnings routes - Handle all earnings and profit API endpoints
"""

from flask import Blueprint, request, jsonify, session
from .service import EarningsService
from datetime import datetime

earnings_bp = Blueprint('earnings', __name__)
earnings_service = EarningsService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

@earnings_bp.route('/api/earnings/summary', methods=['GET'])
def get_earnings_summary():
    """Get earnings summary with accurate profit calculations"""
    try:
        date_filter = request.args.get('date_filter', 'all')
        user_id = get_user_id_from_session()
        
        summary = earnings_service.get_earnings_summary(date_filter, user_id)
        
        return jsonify({
            "success": True,
            "summary": summary,
            "date_filter": date_filter
        })
        
    except Exception as e:
        print(f"❌ [EARNINGS API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to get earnings summary: {str(e)}",
            "summary": {
                "total_revenue": 0,
                "total_cost": 0,
                "total_profit": 0,
                "profit_margin": 0,
                "transaction_count": 0,
                "avg_profit_per_sale": 0
            }
        }), 500

@earnings_bp.route('/api/earnings/products', methods=['GET'])
def get_product_earnings():
    """Get product-wise earnings and profit data"""
    try:
        date_filter = request.args.get('date_filter', 'all')
        user_id = get_user_id_from_session()
        
        products = earnings_service.get_product_earnings(date_filter, user_id)
        
        return jsonify({
            "success": True,
            "products": products,
            "total_products": len(products),
            "date_filter": date_filter
        })
        
    except Exception as e:
        print(f"❌ [EARNINGS API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to get product earnings: {str(e)}",
            "products": []
        }), 500

@earnings_bp.route('/api/earnings/top-profitable', methods=['GET'])
def get_top_profitable_products():
    """Get most and least profitable products"""
    try:
        date_filter = request.args.get('date_filter', 'all')
        limit = int(request.args.get('limit', 5))
        user_id = get_user_id_from_session()
        
        top_products = earnings_service.get_top_profitable_products(date_filter, limit, user_id)
        
        return jsonify({
            "success": True,
            "most_profitable": top_products.get('most_profitable', []),
            "least_profitable": top_products.get('least_profitable', []),
            "date_filter": date_filter
        })
        
    except Exception as e:
        print(f"❌ [EARNINGS API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to get top profitable products: {str(e)}",
            "most_profitable": [],
            "least_profitable": []
        }), 500
