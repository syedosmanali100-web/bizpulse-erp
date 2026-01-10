from flask import jsonify, request, session
from . import credit_bp
from modules.shared.database import get_db_connection
from datetime import datetime, timedelta
import traceback

def get_user_id_from_session():
    """Get user_id from session for filtering data"""
    user_type = session.get('user_type')
    if user_type == 'employee':
        return session.get('client_id')
    else:
        return session.get('user_id')

@credit_bp.route('/api/credit/test', methods=['GET'])
def test_credit():
    """Simple test endpoint"""
    return jsonify({
        'success': True,
        'message': 'Credit API is working!',
        'timestamp': datetime.now().isoformat()
    })

@credit_bp.route('/api/credit/bills/debug', methods=['GET'])
def get_credit_bills_debug():
    """Get all credit bills - optimized for speed - Filtered by user"""
    print("=" * 80)
    print("🔥 CREDIT API CALLED")
    print("=" * 80)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get filter parameters
        status = request.args.get('status', 'all')
        customer = request.args.get('customer', 'all')
        date_range = request.args.get('date_range', 'all')
        user_id = get_user_id_from_session()
        
        print(f"📋 Filters: status={status}, customer={customer}, date_range={date_range}, user_id={user_id}")
        
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
        
        # Add user_id filter
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


@credit_bp.route('/api/credit/transactions/<bill_id>', methods=['GET'])
def get_credit_transactions(bill_id):
    """Get all transactions for a specific credit bill"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get bill details
        cursor.execute("""
            SELECT bill_number, customer_name, total_amount, credit_paid_amount, credit_balance
            FROM bills
            WHERE id = ?
        """, (bill_id,))
        
        bill = cursor.fetchone()
        if not bill:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Bill not found'
            }), 404
        
        # Get all transactions for this bill
        cursor.execute("""
            SELECT 
                id, transaction_type, amount, payment_method, 
                reference_number, notes, created_at
            FROM credit_transactions
            WHERE bill_id = ?
            ORDER BY created_at DESC
        """, (bill_id,))
        
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            transactions.append({
                'id': row[0],
                'transaction_type': row[1],
                'amount': float(row[2]),
                'payment_method': row[3],
                'reference_number': row[4],
                'notes': row[5] or '',
                'created_at': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'bill': {
                'bill_number': bill[0],
                'customer_name': bill[1],
                'total_amount': float(bill[2]),
                'paid_amount': float(bill[3] or 0),
                'balance': float(bill[4] or 0)
            },
            'transactions': transactions,
            'total_transactions': len(transactions)
        })
        
    except Exception as e:
        print(f"❌ [CREDIT TRANSACTIONS] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@credit_bp.route('/api/credit/customer/<customer_id>/transactions', methods=['GET'])
def get_customer_credit_transactions(customer_id):
    """Get all credit transactions for a specific customer"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get customer details
        cursor.execute("""
            SELECT name, phone, email
            FROM customers
            WHERE id = ?
        """, (customer_id,))
        
        customer = cursor.fetchone()
        if not customer:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        # Get all credit bills for this customer
        cursor.execute("""
            SELECT 
                b.id, b.bill_number, b.total_amount, 
                b.credit_paid_amount, b.credit_balance, 
                b.payment_status, b.created_at
            FROM bills b
            WHERE b.customer_id = ? AND b.is_credit = 1
            ORDER BY b.created_at DESC
        """, (customer_id,))
        
        bills = cursor.fetchall()
        
        # Get all transactions for this customer
        cursor.execute("""
            SELECT 
                ct.id, ct.bill_id, ct.transaction_type, ct.amount, 
                ct.payment_method, ct.reference_number, ct.notes, ct.created_at,
                b.bill_number
            FROM credit_transactions ct
            JOIN bills b ON ct.bill_id = b.id
            WHERE ct.customer_id = ?
            ORDER BY ct.created_at DESC
        """, (customer_id,))
        
        rows = cursor.fetchall()
        
        transactions = []
        for row in rows:
            transactions.append({
                'id': row[0],
                'bill_id': row[1],
                'bill_number': row[8],
                'transaction_type': row[2],
                'amount': float(row[3]),
                'payment_method': row[4],
                'reference_number': row[5],
                'notes': row[6] or '',
                'created_at': row[7]
            })
        
        bills_list = []
        for bill in bills:
            bills_list.append({
                'id': bill[0],
                'bill_number': bill[1],
                'total_amount': float(bill[2]),
                'paid_amount': float(bill[3] or 0),
                'balance': float(bill[4] or 0),
                'payment_status': bill[5],
                'created_at': bill[6]
            })
        
        # Calculate totals
        total_credit = sum(b['balance'] for b in bills_list)
        total_paid = sum(b['paid_amount'] for b in bills_list)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'customer': {
                'name': customer[0],
                'phone': customer[1] or '',
                'email': customer[2] or ''
            },
            'bills': bills_list,
            'transactions': transactions,
            'summary': {
                'total_bills': len(bills_list),
                'total_credit': round(total_credit, 2),
                'total_paid': round(total_paid, 2),
                'total_transactions': len(transactions)
            }
        })
        
    except Exception as e:
        print(f"❌ [CUSTOMER CREDIT TRANSACTIONS] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@credit_bp.route('/api/credit/today-summary', methods=['GET'])
def get_today_summary():
    """Get today's payment summary"""
    try:
        conn = get_db_connection()
        user_id = get_user_id_from_session()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get today's payments from credit_transactions
        query = """
            SELECT 
                COUNT(*) as payment_count,
                SUM(amount) as total_amount
            FROM credit_transactions
            WHERE DATE(created_at) = ?
            AND transaction_type = 'payment'
        """
        
        params = [today]
        
        # Add user filter if needed
        if user_id:
            query += " AND (bill_id IN (SELECT id FROM bills WHERE business_owner_id = ? OR business_owner_id IS NULL))"
            params.append(user_id)
        
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        
        payment_count = row['payment_count'] if row else 0
        total_amount = row['total_amount'] if row and row['total_amount'] else 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'payment_count': payment_count,
            'total_amount': float(total_amount)
        })
        
    except Exception as e:
        print(f"❌ [TODAY SUMMARY] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'payment_count': 0,
            'total_amount': 0
        }), 500


@credit_bp.route('/api/credit/export', methods=['GET'])
def export_credit_bills():
    """Export credit bills data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                b.bill_number,
                b.customer_name,
                b.customer_id,
                b.total_amount,
                b.credit_paid_amount,
                b.credit_balance,
                b.payment_status,
                b.created_at
            FROM bills b
            WHERE b.is_credit = 1 AND b.credit_balance > 0
            ORDER BY b.created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        bills = []
        for row in rows:
            bills.append({
                'bill_number': row[0],
                'customer_name': row[1] or 'Walk-in Customer',
                'customer_phone': '',
                'total_amount': float(row[3] or 0),
                'paid_amount': float(row[4] or 0),
                'remaining_amount': float(row[5] or 0),
                'payment_status': row[6] or 'unpaid',
                'date': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': bills
        })
        
    except Exception as e:
        print(f"❌ [CREDIT EXPORT] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@credit_bp.route('/api/credit/payment', methods=['POST'])
def record_credit_payment():
    """Record a payment for a credit bill"""
    try:
        data = request.json
        bill_id = data.get('bill_id')
        payment_amount = float(data.get('payment_amount', 0))
        payment_method = data.get('payment_method', 'CASH')
        notes = data.get('notes', '')
        
        if not bill_id or payment_amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Invalid bill ID or payment amount'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current bill details including customer_id
        cursor.execute("""
            SELECT total_amount, credit_paid_amount, credit_balance, payment_status, customer_id, bill_number, customer_name
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
        customer_id = row[4]
        bill_number = row[5]
        customer_name = row[6] or 'Walk-in Customer'
        
        new_paid = current_paid + payment_amount
        new_balance = total_amount - new_paid
        
        # Determine new status
        if new_balance <= 0:
            new_status = 'paid'
            new_balance = 0
            new_paid = total_amount
        elif new_paid > 0:
            new_status = 'partial'
        else:
            new_status = 'unpaid'
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Update bill
            cursor.execute("""
                UPDATE bills
                SET credit_paid_amount = ?,
                    credit_balance = ?,
                    payment_status = ?,
                    payment_method = ?
                WHERE id = ?
            """, (new_paid, new_balance, new_status, payment_method, bill_id))
            
            # 🔥 CRITICAL FIX: Insert transaction record into credit_transactions table
            from modules.shared.database import generate_id
            transaction_id = generate_id()
            
            # Use customer_id or default to 'walk-in-customer' if NULL
            transaction_customer_id = customer_id or 'walk-in-customer'
            
            cursor.execute("""
                INSERT INTO credit_transactions (
                    id, bill_id, customer_id, transaction_type, amount, 
                    payment_method, reference_number, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                bill_id,
                transaction_customer_id,
                'payment',
                payment_amount,
                payment_method,
                bill_number,
                notes,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Also create a payment record in payments table
            payment_id = generate_id()
            cursor.execute("""
                INSERT INTO payments (id, bill_id, method, amount, processed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (payment_id, bill_id, payment_method, payment_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            
            print(f"✅ [CREDIT PAYMENT] Payment recorded successfully:")
            print(f"   Bill: {bill_number}")
            print(f"   Customer: {customer_name}")
            print(f"   Payment: ₹{payment_amount}")
            print(f"   New Balance: ₹{new_balance}")
            print(f"   Transaction ID: {transaction_id}")
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Payment recorded successfully',
                'new_paid_amount': new_paid,
                'new_status': new_status,
                'remaining_amount': new_balance,
                'transaction_id': transaction_id
            })
            
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
        
    except Exception as e:
        print(f"❌ [CREDIT PAYMENT] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
