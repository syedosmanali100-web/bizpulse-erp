"""
Reports routes - Handle all report generation
"""

from flask import Blueprint, request, jsonify, session, send_file
from modules.shared.database import get_db_connection
from datetime import datetime, timedelta
import io
import csv

reports_bp = Blueprint('reports', __name__)

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

# ========== SALES REPORTS ==========

@reports_bp.route('/api/reports/sales_summary', methods=['GET'])
def sales_summary_report():
    """Sales Summary Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_bills,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_bill_value,
                SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END) as cash_sales,
                SUM(CASE WHEN payment_method = 'upi' THEN total_amount ELSE 0 END) as upi_sales,
                SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END) as card_sales,
                SUM(CASE WHEN is_credit = 1 THEN total_amount ELSE 0 END) as credit_sales
            FROM bills
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        
        # Calculate summary
        total_revenue = sum(row['total_revenue'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_revenue}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/sales_by_product', methods=['GET'])
def sales_by_product_report():
    """Product-wise Sales Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                product_name,
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue,
                COUNT(*) as total_transactions,
                AVG(unit_price) as avg_price
            FROM sales
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY product_name ORDER BY total_revenue DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_revenue = sum(row['total_revenue'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_revenue}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/sales_by_customer', methods=['GET'])
def sales_by_customer_report():
    """Customer-wise Sales Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                customer_name,
                COUNT(*) as total_bills,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_bill_value,
                MAX(created_at) as last_purchase
            FROM bills
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY customer_name ORDER BY total_revenue DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_revenue = sum(row['total_revenue'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_revenue}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/sales_by_payment', methods=['GET'])
def sales_by_payment_report():
    """Payment Method Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                payment_method,
                COUNT(*) as total_transactions,
                SUM(total_amount) as total_amount,
                AVG(total_amount) as avg_transaction
            FROM bills
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY payment_method ORDER BY total_amount DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_amount = sum(row['total_amount'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_amount}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/daily_sales', methods=['GET'])
def daily_sales_report():
    """Daily Sales Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as bills,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_value
            FROM bills
            WHERE DATE(created_at) >= DATE('now', '-30 days')
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY DATE(created_at) ORDER BY date DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_revenue = sum(row['revenue'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_revenue}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== INVENTORY REPORTS ==========

@reports_bp.route('/api/reports/stock_summary', methods=['GET'])
def stock_summary_report():
    """Stock Summary Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name as product_name,
                code as product_code,
                category,
                stock as current_stock,
                unit,
                price as selling_price,
                cost as cost_price,
                (stock * price) as stock_value
            FROM products
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY stock_value DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_value = sum(row['stock_value'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_value}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/low_stock', methods=['GET'])
def low_stock_report():
    """Low Stock Alert Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name as product_name,
                code as product_code,
                stock as current_stock,
                min_stock as minimum_stock,
                (min_stock - stock) as shortage,
                unit
            FROM products
            WHERE stock <= min_stock AND stock > 0
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY shortage DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': len(report_data)}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/out_of_stock', methods=['GET'])
def out_of_stock_report():
    """Out of Stock Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name as product_name,
                code as product_code,
                category,
                unit,
                price as selling_price
            FROM products
            WHERE stock = 0
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY name"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': len(report_data)}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/expiry_report', methods=['GET'])
def expiry_report():
    """Product Expiry Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name as product_name,
                code as product_code,
                stock as current_stock,
                expiry_date,
                CAST((JULIANDAY(expiry_date) - JULIANDAY('now')) AS INTEGER) as days_to_expiry
            FROM products
            WHERE expiry_date IS NOT NULL AND expiry_date != ''
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY days_to_expiry ASC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': len(report_data)}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/stock_valuation', methods=['GET'])
def stock_valuation_report():
    """Stock Valuation Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name as product_name,
                stock as quantity,
                cost as cost_price,
                price as selling_price,
                (stock * cost) as cost_value,
                (stock * price) as selling_value,
                ((stock * price) - (stock * cost)) as potential_profit
            FROM products
            WHERE stock > 0
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY selling_value DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_value = sum(row['selling_value'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_value}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== FINANCIAL REPORTS ==========

@reports_bp.route('/api/reports/profit_loss', methods=['GET'])
def profit_loss_report():
    """Profit & Loss Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        # Get sales data with cost
        query = """
            SELECT 
                DATE(s.sale_date) as date,
                SUM(s.total_price) as revenue,
                SUM(s.quantity * p.cost) as cost,
                SUM(s.total_price - (s.quantity * p.cost)) as profit
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (s.business_owner_id = ? OR s.business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY DATE(s.sale_date) ORDER BY date DESC LIMIT 30"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_profit = sum(row['profit'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_profit}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/revenue_report', methods=['GET'])
def revenue_report():
    """Revenue Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as transactions,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_revenue
            FROM bills
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_revenue = sum(row['revenue'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_revenue}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== CUSTOMER REPORTS ==========

@reports_bp.route('/api/reports/customer_list', methods=['GET'])
def customer_list_report():
    """Customer List Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                name,
                phone,
                email,
                address,
                created_at as registration_date
            FROM customers
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY name"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': len(report_data)}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/top_customers', methods=['GET'])
def top_customers_report():
    """Top Customers Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                customer_name,
                COUNT(*) as total_purchases,
                SUM(total_amount) as total_spent,
                AVG(total_amount) as avg_purchase,
                MAX(created_at) as last_purchase
            FROM bills
            WHERE 1=1
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " GROUP BY customer_name ORDER BY total_spent DESC LIMIT 50"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_spent = sum(row['total_spent'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_spent}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== CREDIT REPORTS ==========

@reports_bp.route('/api/reports/outstanding_credit', methods=['GET'])
def outstanding_credit_report():
    """Outstanding Credit Report"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                bill_number,
                customer_name,
                total_amount,
                credit_paid_amount as paid_amount,
                credit_balance as outstanding,
                created_at as bill_date
            FROM bills
            WHERE is_credit = 1 AND credit_balance > 0
        """
        
        params = []
        if user_id:
            query += " AND (business_owner_id = ? OR business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY credit_balance DESC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        report_data = [dict(row) for row in rows]
        total_outstanding = sum(row['outstanding'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {'total': total_outstanding}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/api/reports/credit_payment_history', methods=['GET'])
def credit_payment_history_report():
    """Credit Payment History Report - Complete transaction history with all payment details"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        query = """
            SELECT 
                b.bill_number,
                b.customer_name,
                b.total_amount as bill_amount,
                b.credit_paid_amount as total_paid,
                b.credit_balance as remaining_balance,
                b.created_at as bill_date,
                ct.amount as payment_amount,
                ct.payment_method,
                ct.created_at as payment_date,
                ct.notes as payment_notes,
                ct.reference_number
            FROM bills b
            LEFT JOIN credit_transactions ct ON b.id = ct.bill_id AND ct.transaction_type = 'payment'
            WHERE b.is_credit = 1
        """
        
        params = []
        if user_id:
            query += " AND (b.business_owner_id = ? OR b.business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY b.bill_number, ct.created_at ASC"
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        # Group payments by bill
        bills_dict = {}
        for row in rows:
            bill_number = row['bill_number']
            
            if bill_number not in bills_dict:
                bills_dict[bill_number] = {
                    'bill_number': bill_number,
                    'customer_name': row['customer_name'] or 'Walk-in Customer',
                    'bill_amount': float(row['bill_amount'] or 0),
                    'total_paid': float(row['total_paid'] or 0),
                    'remaining_balance': float(row['remaining_balance'] or 0),
                    'bill_date': row['bill_date'],
                    'payments': []
                }
            
            # Add payment if exists (only actual payments, not credit_issued)
            if row['payment_amount'] and row['payment_amount'] > 0:
                bills_dict[bill_number]['payments'].append({
                    'amount': float(row['payment_amount']),
                    'method': row['payment_method'] or 'CASH',
                    'date': row['payment_date'],
                    'notes': row['payment_notes'] or '',
                    'reference': row['reference_number'] or ''
                })
        
        # Flatten the data for table display
        report_data = []
        for bill_number, bill_info in bills_dict.items():
            if bill_info['payments']:
                # Add row for each payment
                for idx, payment in enumerate(bill_info['payments'], 1):
                    report_data.append({
                        'bill_number': bill_number,
                        'customer_name': bill_info['customer_name'],
                        'bill_amount': bill_info['bill_amount'],
                        'bill_date': bill_info['bill_date'],
                        'payment_no': f"Payment {idx}",
                        'payment_amount': payment['amount'],
                        'payment_method': payment['method'],
                        'payment_date': payment['date'],
                        'payment_notes': payment['notes'],
                        'total_paid': bill_info['total_paid'],
                        'remaining_balance': bill_info['remaining_balance']
                    })
            else:
                # Bill with no payments yet
                report_data.append({
                    'bill_number': bill_number,
                    'customer_name': bill_info['customer_name'],
                    'bill_amount': bill_info['bill_amount'],
                    'bill_date': bill_info['bill_date'],
                    'payment_no': 'No Payment',
                    'payment_amount': 0,
                    'payment_method': '-',
                    'payment_date': '-',
                    'payment_notes': '-',
                    'total_paid': bill_info['total_paid'],
                    'remaining_balance': bill_info['remaining_balance']
                })
        
        total_bill_amount = sum(row['bill_amount'] for row in report_data)
        total_paid_amount = sum(row['payment_amount'] for row in report_data)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'summary': {
                'total': total_paid_amount,
                'total_bills': total_bill_amount
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Add more report endpoints as needed...

# Export functionality
@reports_bp.route('/api/reports/<report_type>/export', methods=['GET'])
def export_report(report_type):
    """Export report to CSV/Excel"""
    try:
        format_type = request.args.get('format', 'csv')
        
        # For now, return a simple message
        # In production, generate actual file
        return jsonify({
            'success': True,
            'message': f'Export {report_type} as {format_type} - Feature coming soon!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
