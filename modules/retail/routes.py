"""
Retail management routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template, jsonify
from modules.shared.auth_decorators import require_auth
from .service import RetailService
from datetime import datetime

retail_bp = Blueprint('retail', __name__)
retail_service = RetailService()

# Retail Management module routes
@retail_bp.route('/retail/products')
def retail_products_page():
    return render_template('retail_products.html')

@retail_bp.route('/retail/customers')
def retail_customers():
    return render_template('retail_customers.html')

@retail_bp.route('/retail/billing')
def retail_billing():
    return render_template('retail_billing.html')

@retail_bp.route('/retail/billing-test')
def retail_billing_test():
    return "<h1>✅ Billing Route Working!</h1><p>This is a test route to verify billing is accessible.</p>"

@retail_bp.route('/retail/dashboard')
@require_auth
def retail_dashboard():
    return render_template('retail_dashboard.html')

@retail_bp.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """Get comprehensive dashboard statistics with real-time data"""
    try:
        result = retail_service.get_dashboard_stats()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retail_bp.route('/retail/profile')
def retail_profile():
    return render_template('retail_profile_professional.html')

@retail_bp.route('/test-reports')
def test_reports():
    return "<h1>🎉 Reports Module Working!</h1><p>Route is active!</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@retail_bp.route('/retail/sales')
def retail_sales():
    return render_template('retail_sales_professional.html')

@retail_bp.route('/retail/credit')
def retail_credit():
    return render_template('retail_credit_professional.html')

@retail_bp.route('/retail/sales-old')
def retail_sales_old():
    return render_template('retail_sales_enhanced.html')

@retail_bp.route('/retail/inventory')
def retail_inventory():
    return render_template('inventory_professional.html')

@retail_bp.route('/retail/settings')
def retail_settings():
    return render_template('settings_professional.html')

@retail_bp.route('/retail/invoices')
def retail_invoices():
    try:
        return render_template('invoices_professional.html')
    except Exception as e:
        return f"<h1>❌ Invoice Template Error</h1><p>Error: {str(e)}</p><p>Template: invoices_professional.html</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@retail_bp.route('/retail/invoices-test')
def retail_invoices_test():
    return "<h1>✅ Invoice Route Working!</h1><p>This is a test route to verify invoices are accessible.</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@retail_bp.route('/retail/invoice/<invoice_id>')
def retail_invoice_detail(invoice_id):
    try:
        return render_template('retail_invoice_detail.html', invoice_id=invoice_id)
    except Exception as e:
        return f"<h1>❌ Invoice Detail Template Error</h1><p>Error: {str(e)}</p><p>Template: retail_invoice_detail.html</p><p>Invoice ID: {invoice_id}</p><a href='/retail/invoices'>Back to Invoices</a>"

@retail_bp.route('/invoice-demo')
def invoice_demo():
    return render_template('invoice_demo.html')

@retail_bp.route('/invoice-test')
def invoice_test():
    """Invoice System Test Page"""
    return render_template('invoice_test_page.html')