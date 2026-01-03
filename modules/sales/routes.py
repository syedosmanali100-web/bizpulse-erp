"""
Sales routes - Handle all sales API endpoints
"""

from flask import Blueprint, request, jsonify
from .service import SalesService
from datetime import datetime, timedelta

sales_bp = Blueprint('sales', __name__)
sales_service = SalesService()

@sales_bp.route('/api/sales', methods=['GET'])
def get_sales():
    """Get all sales with optional date filtering"""
    try:
        date_filter = request.args.get('date_filter')  # today, yesterday, week, month, or specific date
        
        sales = sales_service.get_all_sales(date_filter)
        summary = sales_service.get_sales_summary(date_filter)
        
        return jsonify({
            "success": True,
            "sales": sales,
            "summary": summary,
            "total_count": len(sales),
            "total_records": len(sales),
            "date_filter": date_filter
        })
        
    except Exception as e:
        print(f"❌ [SALES API] Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to get sales: {str(e)}",
            "sales": [],
            "summary": {}
        }), 500

@sales_bp.route('/api/sales/all', methods=['GET'])
def get_all_sales():
    """Get all sales with date range filtering - for frontend compatibility"""
    try:
        from_date = request.args.get('from') or request.args.get('startDate')
        to_date = request.args.get('to') or request.args.get('endDate')
        date_filter = request.args.get('filter')  # today, yesterday, week, month
        payment_method = request.args.get('payment_method')
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 500, type=int)
        
        # Use date_filter if provided, otherwise use date range
        if date_filter and date_filter in ['today', 'yesterday', 'week', 'month']:
            sales = sales_service.get_all_sales(date_filter)
            summary = sales_service.get_sales_summary(date_filter)
        elif from_date or to_date:
            sales = sales_service.get_sales_by_date_range(from_date, to_date, limit)
            summary = sales_service.get_sales_summary()
        else:
            # Default to today's sales
            sales = sales_service.get_all_sales('today')
            summary = sales_service.get_sales_summary('today')
        
        # Filter by payment method if specified
        if payment_method and payment_method != 'all':
            sales = [s for s in sales if s.get('payment_method') == payment_method]
        
        # Calculate pagination
        total_records = len(sales)
        total_pages = max(1, (total_records + limit - 1) // limit)
        
        # Return both 'bills' and 'sales' for frontend compatibility
        return jsonify({
            "success": True,
            "sales": sales,
            "bills": sales,  # Frontend expects 'bills'
            "summary": {
                "total_sales": summary.get('total_revenue', 0),  # Frontend expects this for revenue
                "total_bills": summary.get('total_sales', 0),    # Frontend expects this for count
                "total_revenue": summary.get('total_revenue', 0),
                "total_items": summary.get('total_items', 0),
                "avg_sale_value": summary.get('avg_sale_value', 0),
                "net_profit": summary.get('total_revenue', 0) * 0.2,  # Estimated 20% profit
                "receivable": 0,
                "receivable_profit": 0
            },
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records,
                "per_page": limit
            },
            "filters": {
                "date_filter": date_filter,
                "from_date": from_date,
                "to_date": to_date,
                "payment_method": payment_method
            },
            "total_count": total_records,
            "total_records": total_records
        })
        
    except Exception as e:
        print(f"❌ [SALES API] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to get sales: {str(e)}",
            "sales": [],
            "bills": [],
            "summary": {},
            "pagination": {"current_page": 1, "total_pages": 1, "total_records": 0}
        }), 500

@sales_bp.route('/api/sales/refresh', methods=['POST'])
def refresh_sales():
    """Refresh sales data - for frontend compatibility"""
    try:
        data = request.json or {}
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        sales = sales_service.get_sales_by_date_range(from_date, to_date, 500)
        summary = sales_service.get_sales_summary()
        
        return jsonify({
            "success": True,
            "sales": sales,
            "summary": summary,
            "total_count": len(sales)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to refresh sales: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/export', methods=['GET'])
def export_sales():
    """Export sales data - for frontend compatibility"""
    try:
        date_range = request.args.get('date_range', 'today')
        payment_method = request.args.get('payment_method', 'all')
        format_type = request.args.get('format', 'json')
        
        # Map date_range to date_filter
        date_filter = date_range if date_range in ['today', 'yesterday', 'week', 'month'] else None
        
        sales = sales_service.get_all_sales(date_filter)
        
        # Filter by payment method if specified
        if payment_method and payment_method != 'all':
            sales = [s for s in sales if s.get('payment_method') == payment_method]
        
        return jsonify({
            "success": True,
            "sales": sales,
            "total_count": len(sales),
            "export_format": format_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to export sales: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/summary', methods=['GET'])
def get_sales_summary():
    """Get sales summary with totals"""
    try:
        date_filter = request.args.get('date_filter')  # today, yesterday, week, month
        
        summary = sales_service.get_sales_summary(date_filter)
        
        return jsonify({
            "success": True,
            "summary": summary,
            "date_filter": date_filter
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get sales summary: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/top-products', methods=['GET'])
def get_top_products():
    """Get top selling products"""
    try:
        limit = int(request.args.get('limit', 10))
        date_filter = request.args.get('date_filter')
        
        products = sales_service.get_top_products(limit, date_filter)
        
        return jsonify({
            "success": True,
            "top_products": products,
            "limit": limit,
            "date_filter": date_filter
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get top products: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/chart', methods=['GET'])
def get_sales_chart():
    """Get daily sales data for chart"""
    try:
        days = int(request.args.get('days', 7))
        
        chart_data = sales_service.get_daily_sales_chart(days)
        
        return jsonify({
            "success": True,
            "chart_data": chart_data,
            "days": days
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get chart data: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/health', methods=['GET'])
def check_sales_health():
    """Check if sales data is being stored properly"""
    try:
        health = sales_service.check_database_health()
        
        return jsonify({
            "success": True,
            "health": health,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to check health: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/today', methods=['GET'])
def get_today_sales():
    """Get today's sales - Quick endpoint"""
    try:
        sales = sales_service.get_all_sales('today')
        summary = sales_service.get_sales_summary('today')
        
        return jsonify({
            "success": True,
            "today_sales": sales,
            "today_summary": summary,
            "date": datetime.now().strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get today's sales: {str(e)}"
        }), 500

@sales_bp.route('/api/sales/yesterday', methods=['GET'])
def get_yesterday_sales():
    """Get yesterday's sales - Quick endpoint"""
    try:
        sales = sales_service.get_all_sales('yesterday')
        summary = sales_service.get_sales_summary('yesterday')
        
        return jsonify({
            "success": True,
            "yesterday_sales": sales,
            "yesterday_summary": summary,
            "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get yesterday's sales: {str(e)}"
        }), 500