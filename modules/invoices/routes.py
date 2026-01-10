"""
Invoice routes - Handle all invoice API endpoints
Invoices are the source of truth for all transactions
"""

from flask import Blueprint, request, jsonify, session
from .service import InvoiceService
from datetime import datetime

invoices_bp = Blueprint('invoices', __name__)
invoice_service = InvoiceService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

@invoices_bp.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices with comprehensive filtering and pagination - Filtered by user"""
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        
        filters = {}
        
        # Status filter (payment status)
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        # Date filter (quick filters)
        if request.args.get('date_filter'):
            filters['date_filter'] = request.args.get('date_filter')
        
        # Custom date
        if request.args.get('custom_date'):
            filters['custom_date'] = request.args.get('custom_date')
        
        # Date range filters
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        # Pagination
        if request.args.get('page'):
            try:
                filters['page'] = int(request.args.get('page'))
            except ValueError:
                filters['page'] = 1
        
        if request.args.get('limit'):
            try:
                filters['limit'] = int(request.args.get('limit'))
            except ValueError:
                filters['limit'] = 50
        
        result = invoice_service.get_invoices(filters, user_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get invoices: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/all', methods=['GET'])
def get_all_invoices():
    """Get all invoices - for frontend compatibility - Filtered by user"""
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        
        from_date = request.args.get('from')
        to_date = request.args.get('to')
        limit = request.args.get('limit', 100, type=int)
        
        filters = {'limit': limit}
        if from_date:
            filters['date_from'] = from_date
        if to_date:
            filters['date_to'] = to_date
        
        result = invoice_service.get_invoices(filters, user_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get invoices: {str(e)}"
        }), 500


@invoices_bp.route('/api/invoices/<invoice_id>', methods=['GET'])
def get_invoice_by_id(invoice_id):
    """Get invoice details by ID - Filtered by user"""
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        
        result = invoice_service.get_invoice_by_id(invoice_id, user_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get invoice: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices', methods=['POST'])
def create_invoice():
    """Create a new invoice"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        result = invoice_service.create_invoice(data)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to create invoice: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/<invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    """Delete invoice and revert all changes"""
    try:
        result = invoice_service.delete_invoice(invoice_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete invoice: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/summary', methods=['GET'])
def get_invoice_summary():
    """Get invoice summary statistics"""
    try:
        filters = {}
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        result = invoice_service.get_invoice_summary(filters)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get invoice summary: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/refresh', methods=['POST'])
def refresh_invoices():
    """Refresh invoices data - for frontend compatibility"""
    try:
        data = request.json or {}
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        filters = {'limit': 500}
        if from_date:
            filters['date_from'] = from_date
        if to_date:
            filters['date_to'] = to_date
        
        result = invoice_service.get_invoices(filters)
        summary = invoice_service.get_invoice_summary(filters)
        
        return jsonify({
            "success": True,
            "invoices": result.get('invoices', []),
            "summary": summary.get('summary', {}),
            "total_count": result.get('pagination', {}).get('total_records', 0)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to refresh invoices: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/export', methods=['GET'])
def export_invoices():
    """Export invoices data"""
    try:
        date_range = request.args.get('date_range', 'today')
        payment_status = request.args.get('payment_status', 'all')
        format_type = request.args.get('format', 'json')
        
        filters = {}
        if date_range in ['today', 'yesterday', 'week', 'month']:
            filters['date_filter'] = date_range
        
        if payment_status and payment_status != 'all':
            filters['status'] = payment_status
        
        result = invoice_service.get_invoices(filters)
        
        return jsonify({
            "success": True,
            "invoices": result.get('invoices', []),
            "total_count": result.get('pagination', {}).get('total_records', 0),
            "export_format": format_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to export invoices: {str(e)}"
        }), 500

@invoices_bp.route('/api/invoices/health', methods=['GET'])
def check_invoices_health():
    """Check if invoice data is being stored properly"""
    try:
        health = invoice_service.check_database_health()
        
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
