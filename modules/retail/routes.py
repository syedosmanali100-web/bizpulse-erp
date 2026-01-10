"""
Retail management routes
COPIED AS-IS from app.py
"""

from flask import Blueprint, render_template, jsonify, session
from modules.shared.auth_decorators import require_auth
from .service import RetailService
from datetime import datetime

retail_bp = Blueprint('retail', __name__)
retail_service = RetailService()

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

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
def retail_dashboard():
    return render_template('retail_dashboard.html')

@retail_bp.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics with real-time data - Filtered by user"""
    try:
        user_id = get_user_id_from_session()
        result = retail_service.get_dashboard_stats(user_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retail_bp.route('/api/dashboard/activity', methods=['GET'])
def get_dashboard_activity():
    """Get recent activity for dashboard - Filtered by user"""
    try:
        user_id = get_user_id_from_session()
        result = retail_service.get_recent_activity(user_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting dashboard activity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@retail_bp.route('/retail/profile')
def retail_profile():
    return render_template('retail_profile_professional.html')

@retail_bp.route('/test-reports')
def test_reports():
    return "<h1>🎉 Reports Module Working!</h1><p>Route is active!</p><a href='/retail/dashboard'>Back to Dashboard</a>"

@retail_bp.route('/retail/sales')
def retail_sales():
    # Add cache busting headers
    from flask import make_response
    response = make_response(render_template('retail_sales_professional.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
        return render_template('simple_receipt.html', invoice_id=invoice_id)
    except Exception as e:
        return f"<h1>❌ Invoice Detail Template Error</h1><p>Error: {str(e)}</p><p>Template: simple_receipt.html</p><p>Invoice ID: {invoice_id}</p><a href='/retail/invoices'>Back to Invoices</a>"

@retail_bp.route('/invoice-demo')
def invoice_demo():
    return render_template('invoice_demo.html')

@retail_bp.route('/invoice-test')
def invoice_test():
    """Invoice System Test Page"""
    return render_template('invoice_test_page.html')


# ============================================================================
# CREDIT MANAGEMENT ROUTES - Added directly to retail blueprint
# ============================================================================

@retail_bp.route('/api/credit/test', methods=['GET'])
def credit_test():
    """Test credit API"""
    return jsonify({
        'success': True,
        'message': 'Credit API working via retail blueprint!',
        'timestamp': datetime.now().isoformat()
    })

@retail_bp.route('/api/credit/bills/debug', methods=['GET'])
def get_credit_bills():
    """Get all credit bills - Filtered by user"""
    from flask import request
    from modules.shared.database import get_db_connection
    import traceback
    
    print("=" * 80)
    print("🔥 CREDIT API CALLED VIA RETAIL BLUEPRINT")
    print("=" * 80)
    
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        print(f"🔍 [CREDIT] Filtering by user_id: {user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get filter parameters
        status = request.args.get('status', 'all')
        customer = request.args.get('customer', 'all')
        date_range = request.args.get('date_range', 'all')
        
        print(f"📋 Filters: status={status}, customer={customer}, date_range={date_range}")
        
        # Base query with user filtering
        query = """
            SELECT 
                b.id,
                b.bill_number,
                b.customer_name,
                b.customer_id,
                b.total_amount,
                b.credit_paid_amount,
                b.credit_balance,
                b.payment_method,
                b.payment_status,
                b.created_at,
                b.is_credit
            FROM bills b
            WHERE b.is_credit = 1 
            AND b.credit_balance > 0
        """
        
        params = []
        
        # 🔥 Add user filtering
        if user_id:
            query += " AND (b.business_owner_id = ? OR b.business_owner_id IS NULL)"
            params.append(user_id)
        
        # Add date filter
        if date_range != 'all':
            if date_range == 'today':
                query += " AND DATE(b.created_at) = DATE('now', 'localtime')"
            elif date_range == 'yesterday':
                query += " AND DATE(b.created_at) = DATE('now', 'localtime', '-1 day')"
            elif date_range == 'week':
                query += " AND DATE(b.created_at) >= DATE('now', 'localtime', '-7 days')"
            elif date_range == 'month':
                query += " AND DATE(b.created_at) >= DATE('now', 'localtime', '-30 days')"
        
        # Add customer filter
        if customer != 'all':
            query += " AND b.customer_name = ?"
            params.append(customer)
        
        # Add status filter
        if status != 'all':
            if status.lower() == 'unpaid':
                query += " AND b.payment_status = 'unpaid'"
            elif status.lower() == 'partial':
                query += " AND b.payment_status = 'partial'"
        
        query += " ORDER BY b.created_at DESC"
        
        print(f"🔍 Executing query...")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"✅ Found {len(rows)} credit bills")
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'bill_number': row[1],
                'customer_name': row[2] or 'Walk-in Customer',
                'customer_id': row[3],
                'total_amount': float(row[4] or 0),
                'paid_amount': float(row[5] or 0),
                'balance_due': float(row[6] or 0),
                'remaining_amount': float(row[6] or 0),
                'payment_method': row[7] or 'cash',
                'payment_status': row[8] or 'unpaid',
                'created_at': row[9],
                'is_credit': row[10],
                'customer_phone': ''
            })
        
        # Calculate summary
        total_credit = sum(bill['balance_due'] for bill in bills)
        total_paid = sum(bill['paid_amount'] for bill in bills)
        total_amount = sum(bill['total_amount'] for bill in bills)
        total_bills = len(bills)
        
        # Get unique customers
        customers = list(set(bill['customer_name'] for bill in bills))
        
        print(f"💰 Total Credit: ₹{total_credit:.2f}")
        print(f"📊 Total Bills: {total_bills}")
        
        conn.close()
        
        response_data = {
            'success': True,
            'bills': bills,
            'customers': customers,
            'summary': {
                'total_credit': round(total_credit, 2),
                'total_bills': total_bills,
                'total_customers': len(customers)
            },
            'stats': {
                'total_bills': total_bills,
                'pending_amount': round(total_credit, 2),
                'total_amount': round(total_amount, 2),
                'received_amount': round(total_paid, 2)
            }
        }
        
        print(f"✅ Returning {len(bills)} bills")
        print("=" * 80)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'bills': [],
            'customers': [],
            'summary': {'total_credit': 0, 'total_bills': 0, 'total_customers': 0},
            'stats': {'total_bills': 0, 'pending_amount': 0, 'total_amount': 0, 'received_amount': 0}
        }), 500

@retail_bp.route('/api/credit/export', methods=['GET'])
def export_credit():
    """Export credit bills - Filtered by user"""
    from modules.shared.database import get_db_connection
    
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        print(f"🔍 [CREDIT EXPORT] Filtering by user_id: {user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query with user filtering
        query = """
            SELECT 
                b.bill_number,
                b.customer_name,
                b.total_amount,
                b.credit_paid_amount,
                b.credit_balance,
                b.payment_status,
                b.created_at
            FROM bills b
            WHERE b.is_credit = 1 AND b.credit_balance > 0
        """
        
        params = []
        
        # 🔥 Add user filtering
        if user_id:
            query += " AND (b.business_owner_id = ? OR b.business_owner_id IS NULL)"
            params.append(user_id)
        
        query += " ORDER BY b.created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        bills = []
        for row in rows:
            bills.append({
                'bill_number': row[0],
                'customer_name': row[1] or 'Walk-in Customer',
                'customer_phone': '',
                'total_amount': float(row[2] or 0),
                'paid_amount': float(row[3] or 0),
                'remaining_amount': float(row[4] or 0),
                'payment_status': row[5] or 'unpaid',
                'date': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': bills
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retail_bp.route('/api/credit/payment', methods=['POST'])
def record_credit_payment():
    """Record a payment for a credit bill"""
    from flask import request
    from modules.shared.database import get_db_connection
    import traceback
    import uuid
    from datetime import datetime
    
    print("=" * 80)
    print("💰 RECORDING CREDIT PAYMENT")
    print("=" * 80)
    
    try:
        data = request.json
        bill_id = data.get('bill_id')
        payment_amount = float(data.get('payment_amount', 0))
        payment_method = data.get('payment_method', 'CASH')
        
        print(f"📋 Bill ID: {bill_id}")
        print(f"💵 Payment Amount: ₹{payment_amount}")
        print(f"💳 Payment Method: {payment_method}")
        
        if not bill_id or payment_amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid bill ID or payment amount'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current bill details
        cursor.execute("""
            SELECT total_amount, credit_paid_amount, credit_balance, payment_status, bill_number, created_at
            FROM bills
            WHERE id = ?
        """, (bill_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Bill not found'
            }), 404
        
        total_amount = float(row[0])
        current_paid = float(row[1] or 0)
        current_balance = float(row[2] or 0)
        bill_number = row[4]
        bill_created_at = row[5]
        
        print(f"📊 Current Status:")
        print(f"   Total: ₹{total_amount}")
        print(f"   Paid: ₹{current_paid}")
        print(f"   Balance: ₹{current_balance}")
        print(f"   Bill Date: {bill_created_at}")
        
        new_paid = current_paid + payment_amount
        new_balance = total_amount - new_paid
        
        # Determine new status
        if new_balance <= 0:
            new_status = 'paid'
            new_balance = 0
            new_paid = total_amount
            is_credit = 0  # No longer a credit bill
        elif new_paid > 0:
            new_status = 'partial'
            is_credit = 1  # Still a credit bill
        else:
            new_status = 'unpaid'
            is_credit = 1
        
        print(f"📊 New Status:")
        print(f"   Paid: ₹{new_paid}")
        print(f"   Balance: ₹{new_balance}")
        print(f"   Status: {new_status}")
        
        # Insert payment record in payments table
        payment_id = str(uuid.uuid4())
        payment_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("""
            INSERT INTO payments (id, bill_id, method, amount, reference, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payment_id, bill_id, payment_method, payment_amount, f"Credit payment for {bill_number}", payment_timestamp))
        
        print(f"💾 Payment record created: {payment_id}")
        
        # Update bill
        cursor.execute("""
            UPDATE bills
            SET credit_paid_amount = ?,
                credit_balance = ?,
                payment_status = ?,
                payment_method = ?,
                is_credit = ?
            WHERE id = ?
        """, (new_paid, new_balance, new_status, payment_method, is_credit, bill_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Payment recorded successfully for {bill_number}")
        print(f"📅 Revenue will be counted for bill date: {bill_created_at}")
        print("=" * 80)
        
        return jsonify({
            'success': True,
            'message': 'Payment recorded successfully',
            'bill_number': bill_number,
            'new_paid_amount': round(new_paid, 2),
            'new_balance': round(new_balance, 2),
            'new_status': new_status,
            'payment_amount': round(payment_amount, 2),
            'payment_id': payment_id
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@retail_bp.route('/api/credit/history', methods=['GET'])
def get_credit_history():
    """Get credit payment history - paid and partially paid bills - Filtered by user"""
    from flask import request
    from modules.shared.database import get_db_connection
    import traceback
    
    print("=" * 80)
    print("📜 LOADING CREDIT PAYMENT HISTORY")
    print("=" * 80)
    
    try:
        # 🔥 Get user_id for filtering
        user_id = get_user_id_from_session()
        print(f"🔍 [CREDIT HISTORY] Filtering by user_id: {user_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get filter parameters
        date_range = request.args.get('date_range', 'all')
        customer = request.args.get('customer', 'all')
        
        # Query for bills that had credit and have payments - with latest payment date
        query = """
            SELECT 
                b.id,
                b.bill_number,
                b.customer_name,
                b.customer_id,
                b.total_amount,
                b.credit_paid_amount,
                b.credit_balance,
                b.payment_method,
                b.payment_status,
                b.created_at,
                b.is_credit,
                (SELECT MAX(p.processed_at) FROM payments p WHERE p.bill_id = b.id) as last_payment_date
            FROM bills b
            WHERE (b.is_credit = 1 OR b.credit_paid_amount > 0)
            AND b.credit_paid_amount > 0
        """
        
        params = []
        
        # 🔥 Add user filtering
        if user_id:
            query += " AND (b.business_owner_id = ? OR b.business_owner_id IS NULL)"
            params.append(user_id)
        
        # Add date filter
        if date_range != 'all':
            if date_range == 'today':
                query += " AND DATE(b.created_at) = DATE('now', 'localtime')"
            elif date_range == 'yesterday':
                query += " AND DATE(b.created_at) = DATE('now', 'localtime', '-1 day')"
            elif date_range == 'week':
                query += " AND DATE(b.created_at) >= DATE('now', 'localtime', '-7 days')"
            elif date_range == 'month':
                query += " AND DATE(b.created_at) >= DATE('now', 'localtime', '-30 days')"
        
        # Add customer filter
        if customer != 'all':
            query += " AND b.customer_name = ?"
            params.append(customer)
        
        query += " ORDER BY b.created_at DESC"
        
        print(f"🔍 Executing history query...")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        print(f"✅ Found {len(rows)} payment history records")
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'bill_number': row[1],
                'customer_name': row[2] or 'Walk-in Customer',
                'customer_id': row[3],
                'total_amount': float(row[4] or 0),
                'paid_amount': float(row[5] or 0),
                'balance_due': float(row[6] or 0),
                'remaining_amount': float(row[6] or 0),
                'payment_method': row[7] or 'cash',
                'payment_status': row[8] or 'unpaid',
                'created_at': row[9],
                'is_credit': row[10],
                'last_payment_date': row[11],  # Latest payment date
                'customer_phone': ''
            })
        
        # Calculate summary
        total_paid = sum(bill['paid_amount'] for bill in bills)
        total_amount = sum(bill['total_amount'] for bill in bills)
        total_remaining = sum(bill['balance_due'] for bill in bills)
        total_bills = len(bills)
        
        # Get unique customers
        customers = list(set(bill['customer_name'] for bill in bills))
        
        print(f"💰 Total Paid: ₹{total_paid:.2f}")
        print(f"📊 Total Bills: {total_bills}")
        
        conn.close()
        
        response_data = {
            'success': True,
            'bills': bills,
            'customers': customers,
            'summary': {
                'total_paid': round(total_paid, 2),
                'total_bills': total_bills,
                'total_customers': len(customers),
                'total_remaining': round(total_remaining, 2)
            },
            'stats': {
                'total_bills': total_bills,
                'pending_amount': round(total_remaining, 2),
                'total_amount': round(total_amount, 2),
                'received_amount': round(total_paid, 2)
            }
        }
        
        print(f"✅ Returning {len(bills)} history records")
        print("=" * 80)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'bills': [],
            'customers': [],
            'summary': {'total_paid': 0, 'total_bills': 0, 'total_customers': 0},
            'stats': {'total_bills': 0, 'pending_amount': 0, 'total_amount': 0, 'received_amount': 0}
        }), 500


@retail_bp.route('/api/credit/bill/<bill_id>/payments', methods=['GET'])
def get_bill_payment_history(bill_id):
    """Get payment history for a specific credit bill"""
    from modules.shared.database import get_db_connection
    import traceback
    
    print("=" * 80)
    print(f"📜 LOADING PAYMENT HISTORY FOR BILL: {bill_id}")
    print("=" * 80)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get bill details
        cursor.execute("""
            SELECT bill_number, customer_name, total_amount, credit_paid_amount, credit_balance
            FROM bills
            WHERE id = ?
        """, (bill_id,))
        
        bill_row = cursor.fetchone()
        if not bill_row:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Bill not found'
            }), 404
        
        bill_info = {
            'bill_number': bill_row[0],
            'customer_name': bill_row[1] or 'Walk-in Customer',
            'total_amount': float(bill_row[2] or 0),
            'paid_amount': float(bill_row[3] or 0),
            'balance': float(bill_row[4] or 0)
        }
        
        # Get payment history from payments table (oldest first)
        cursor.execute("""
            SELECT id, method, amount, reference, processed_at
            FROM payments
            WHERE bill_id = ?
            ORDER BY processed_at ASC
        """, (bill_id,))
        
        payment_rows = cursor.fetchall()
        
        payments = []
        for row in payment_rows:
            payments.append({
                'id': row[0],
                'method': row[1],
                'amount': float(row[2]),
                'reference': row[3],
                'processed_at': row[4]
            })
        
        print(f"✅ Found {len(payments)} payment records")
        
        conn.close()
        
        return jsonify({
            'success': True,
            'bill': bill_info,
            'payments': payments,
            'total_payments': len(payments)
        })
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

