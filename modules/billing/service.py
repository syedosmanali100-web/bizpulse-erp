"""
Billing service
COPIED AS-IS from app_original_backup.py
"""

from modules.shared.database import get_db_connection, generate_id
from datetime import datetime
from modules.dashboard.models import ActivityTracker, log_sale_activity, log_order_activity

class BillingService:
    
    def get_all_bills(self, user_id=None):
        """Get all bills with customer information - Mobile ERP Style - Filtered by user"""
        conn = get_db_connection()
        
        if user_id:
            bills = conn.execute("""SELECT b.*, c.name as customer_name 
                FROM bills b 
                LEFT JOIN customers c ON b.customer_id = c.id 
                WHERE b.business_owner_id = ? OR b.business_owner_id IS NULL
                ORDER BY b.created_at DESC""", (user_id,)).fetchall()
        else:
            bills = conn.execute("""SELECT b.*, c.name as customer_name 
                FROM bills b 
                LEFT JOIN customers c ON b.customer_id = c.id 
                ORDER BY b.created_at DESC""").fetchall()
        
        conn.close()
        return [dict(row) for row in bills]
    
    def get_bill_items(self, bill_id):
        """Get items for a specific bill - Mobile ERP Style"""
        conn = get_db_connection()
        items = conn.execute("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,)).fetchall()
        conn.close()
        return [dict(row) for row in items]
    
    def create_bill(self, data):
        """Create bill - Mobile ERP Perfect Implementation - With business_owner_id"""
        print("📥 [BILLING SERVICE] Received bill data:", data)
        
        # Extract business_owner_id
        business_owner_id = data.get('business_owner_id')
        print(f"📥 [BILLING SERVICE] business_owner_id: {business_owner_id}")
        
        # Validate required fields
        if not data or not data.get('items') or len(data['items']) == 0:
            return {"error": "Items are required", "success": False}
        
        conn = get_db_connection()
        
        # ============================================================================
        # STOCK VALIDATION - Prevent negative stock
        # ============================================================================
        out_of_stock_items = []
        for item in data['items']:
            product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (item['product_id'],)).fetchone()
            
            if not product:
                out_of_stock_items.append(f"❌ Product '{item['product_name']}' not found")
                continue
            
            # Check if stock is sufficient
            if product['stock'] < item['quantity']:
                out_of_stock_items.append(
                    f"❌ {product['name']}: Requested {item['quantity']}, Available {product['stock']}"
                )
            
            # Check if stock would go negative
            if product['stock'] - item['quantity'] < 0:
                out_of_stock_items.append(
                    f"❌ {product['name']}: Cannot reduce stock below 0"
                )
        
        # If any items are out of stock, return error
        if out_of_stock_items:
            conn.close()
            return {
                "error": "Insufficient stock for some items",
                "out_of_stock_items": out_of_stock_items,
                "success": False
            }
        
        # ============================================================================
        # Proceed with bill creation if all stock checks pass
        # ============================================================================
        
        bill_id = generate_id()
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"📝 [BILLING SERVICE] Generated bill: {bill_number}")
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Create bill record with customer name and business_owner_id
            customer_name = data.get('customer_name', 'Walk-in Customer')
            conn.execute("""INSERT INTO bills (id, bill_number, customer_id, customer_name, business_type, business_owner_id, subtotal, tax_amount, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                bill_id, 
                bill_number, 
                data.get('customer_id'),
                customer_name,
                data.get('business_type', 'retail'),
                business_owner_id,  # 🔥 Store business_owner_id for multi-tenant support
                data.get('subtotal', 0), 
                data.get('tax_amount', 0), 
                data.get('total_amount', 0),
                'completed',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            # Keep the customer_name from data, don't overwrite it
            # If customer_id exists, we can get additional info but keep the name from form
            if data.get('customer_id') and not customer_name:
                customer = conn.execute("SELECT name FROM customers WHERE id = ?", (data.get('customer_id'),)).fetchone()
                if customer:
                    customer_name = customer['name']
            
            # Process each item
            for item in data['items']:
                item_id = generate_id()
                
                # Insert bill item
                conn.execute("""INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                    item_id, 
                    bill_id, 
                    item['product_id'], 
                    item['product_name'],
                    item['quantity'], 
                    item['unit_price'], 
                    item['total_price']
                ))
                
                # Update product stock (SAFE STOCK REDUCTION - Never go below 0)
                result = conn.execute("""UPDATE products SET stock = CASE 
                        WHEN stock - ? >= 0 THEN stock - ?
                        ELSE 0
                    END 
                    WHERE id = ?""", (item['quantity'], item['quantity'], item['product_id']))
                
                # Double check that stock didn't go negative
                updated_product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                
                if updated_product and updated_product['stock'] < 0:
                    # This should never happen due to our validation, but just in case
                    conn.execute("UPDATE products SET stock = 0 WHERE id = ?", (item['product_id'],))
                    print(f"⚠️ [BILLING SERVICE] WARNING: Stock for {updated_product['name']} was negative, reset to 0")
                
                # Get product details for sales entry
                product = conn.execute("SELECT category FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                
                # Create sales entry for each item (AUTOMATIC SALES ENTRY)
                sale_id = generate_id()
                sale_date = datetime.now().strftime('%Y-%m-%d')
                sale_time = datetime.now().strftime('%H:%M:%S')
                
                # Calculate proportional tax and discount
                subtotal = data.get('subtotal', 0)
                tax_amount = data.get('tax_amount', 0)
                discount_amount = data.get('discount_amount', 0)
                
                item_tax = (item['total_price'] / subtotal) * tax_amount if subtotal > 0 else 0
                item_discount = (item['total_price'] / subtotal) * discount_amount if subtotal > 0 else 0
                
                conn.execute("""INSERT INTO sales (
                        id, bill_id, bill_number, customer_id, customer_name,
                        product_id, product_name, category, quantity, unit_price,
                        total_price, tax_amount, discount_amount, payment_method,
                        business_owner_id, sale_date, sale_time, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                    item['product_id'], item['product_name'], 
                    product['category'] if product else 'General',
                    item['quantity'], item['unit_price'], item['total_price'],
                    item_tax, item_discount, data.get('payment_method', 'cash'),
                    business_owner_id,  # 🔥 Store business_owner_id for multi-tenant support
                    sale_date, sale_time, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                
                # Broadcast sale creation to all connected devices
                try:
                    from modules.sync.utils import broadcast_data_change
                    sale_data = {
                        'id': sale_id,
                        'bill_id': bill_id,
                        'bill_number': bill_number,
                        'customer_name': customer_name,
                        'product_name': item['product_name'],
                        'quantity': item['quantity'],
                        'total_price': item['total_price'],
                        'payment_method': data.get('payment_method', 'cash'),
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    broadcast_data_change('create', 'sales', sale_data, data.get('business_owner_id'))
                except Exception as sync_error:
                    print(f"⚠️ [SYNC] Failed to broadcast sale creation: {sync_error}")
                    # Don't fail the main operation if sync fails
            
            # Add payment record and handle credit bills
            payment_method = data.get('payment_method', 'cash')
            if payment_method:
                payment_id = generate_id()
                
                if payment_method == 'credit':
                    # For credit bills, set paid amount to 0 and create balance due
                    paid_amount = 0
                    balance_due = data.get('total_amount', 0)
                    
                    print(f"💳 [BILLING] Creating CREDIT bill:")
                    print(f"   Bill ID: {bill_id}")
                    print(f"   Bill Number: {bill_number}")
                    print(f"   Total Amount: ₹{balance_due}")
                    print(f"   Setting is_credit = 1")
                    print(f"   Setting credit_balance = {balance_due}")
                    
                    # Update bills table for credit tracking
                    conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'unpaid',
                               credit_paid_amount = ?, credit_balance = ?
                        WHERE id = ?""", (payment_method, paid_amount, balance_due, bill_id))
                    
                    # Update sales records for credit tracking
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                    
                    # Create payment record with 0 amount for credit
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    # 🔥 NEW: Create initial credit transaction record
                    transaction_id = generate_id()
                    transaction_customer_id = data.get('customer_id') or 'walk-in-customer'
                    conn.execute("""INSERT INTO credit_transactions (
                            id, bill_id, customer_id, transaction_type, amount, 
                            payment_method, reference_number, notes, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        transaction_id,
                        bill_id,
                        transaction_customer_id,
                        'credit_issued',
                        balance_due,
                        payment_method,
                        bill_number,
                        f'Credit bill created for {customer_name}',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    print(f"💳 [BILLING SERVICE] Credit bill created: {bill_number} - Amount: ₹{data.get('total_amount', 0)}")
                    print(f"💳 [BILLING SERVICE] Credit transaction recorded: {transaction_id}")
                    
                elif payment_method == 'partial':
                    # For partial payments, get the partial amount
                    partial_amount = float(data.get('partial_amount', 0))
                    total_amount = data.get('total_amount', 0)
                    balance_due = total_amount - partial_amount
                    
                    print(f"🔍 [BILLING SERVICE] Partial payment debug:")
                    print(f"   partial_amount from data: {data.get('partial_amount')}")
                    print(f"   parsed partial_amount: {partial_amount}")
                    print(f"   total_amount: {total_amount}")
                    print(f"   calculated balance_due: {balance_due}")
                    
                    # Validate partial amount
                    if partial_amount <= 0:
                        print(f"❌ [BILLING SERVICE] Invalid partial amount: {partial_amount}")
                        # Set to 0 for credit bill if no valid partial amount
                        partial_amount = 0
                        balance_due = total_amount
                    
                    # Update bills table for partial payment tracking
                    conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'partial',
                               credit_paid_amount = ?, credit_balance = ?
                        WHERE id = ?""", (payment_method, partial_amount, balance_due, bill_id))
                    
                    # Update sales records for partial payment tracking
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, partial_amount, bill_id))
                    
                    # Create payment record with partial amount
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, partial_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    # 🔥 NEW: Create credit transaction records for partial payment
                    transaction_customer_id = data.get('customer_id') or 'walk-in-customer'
                    
                    # 1. Record the credit issued (full amount)
                    transaction_id_credit = generate_id()
                    conn.execute("""INSERT INTO credit_transactions (
                            id, bill_id, customer_id, transaction_type, amount, 
                            payment_method, reference_number, notes, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        transaction_id_credit,
                        bill_id,
                        transaction_customer_id,
                        'credit_issued',
                        total_amount,
                        payment_method,
                        bill_number,
                        f'Partial payment bill created for {customer_name}',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    # 2. Record the partial payment
                    if partial_amount > 0:
                        transaction_id_payment = generate_id()
                        partial_payment_method = data.get('partial_payment_method', 'cash')
                        conn.execute("""INSERT INTO credit_transactions (
                                id, bill_id, customer_id, transaction_type, amount, 
                                payment_method, reference_number, notes, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                            transaction_id_payment,
                            bill_id,
                            transaction_customer_id,
                            'payment',
                            partial_amount,
                            partial_payment_method,
                            bill_number,
                            f'Initial partial payment by {customer_name}',
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        ))
                    
                    print(f"💰 [BILLING SERVICE] Partial payment bill created: {bill_number} - Total: ₹{total_amount}, Paid: ₹{partial_amount}, Due: ₹{balance_due}")
                    print(f"💰 [BILLING SERVICE] Credit transactions recorded")
                    
                else:
                    # Regular payment - full amount paid
                    paid_amount = data.get('total_amount', 0)
                    balance_due = 0
                    
                    # Update bills table for regular payment
                    conn.execute("""UPDATE bills SET payment_method = ?, payment_status = 'paid'
                        WHERE id = ?""", (payment_method, bill_id))
                    
                    # Update sales records
                    conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                        WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                    
                    # Create payment record
                    conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                        VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Commit transaction
            conn.commit()
            conn.close()
            
            # Check if E-Way Bill is required for this invoice
            try:
                from modules.eway.service import eway_service
                invoice_value = data.get('total_amount', 0)
                
                if eway_service.check_eway_requirement(invoice_value, 'Maharashtra', 'Maharashtra'):
                    print(f"💡 [E-WAY BILL] Invoice {bill_number} (₹{invoice_value}) requires E-Way Bill generation")
                    # Note: E-Way Bill can be generated from the invoice management page
                    
            except Exception as eway_error:
                print(f"⚠️ [E-WAY BILL] Failed to check requirement: {eway_error}")
            
            # 🔥 LOG REAL-TIME ACTIVITY - Diverse sale activities based on transaction details
            try:
                total_amount = data.get('total_amount', 0)
                payment_method = data.get('payment_method', 'cash')
                
                # Determine activity type based on transaction characteristics
                if total_amount > 15000:
                    # Large transaction - log as bulk order
                    log_order_activity(
                        order_id=bill_id,
                        amount=total_amount,
                        order_type='processed',
                        customer_name=customer_name,
                        item_count=len(data['items'])
                    )
                    print(f"✅ [DASHBOARD] Bulk order activity logged: {customer_name} - ₹{total_amount}")
                    
                elif payment_method == 'credit':
                    # Credit transaction - different activity title
                    ActivityTracker.log_activity(
                        activity_type='sale',
                        title='Credit sale processed',
                        description=f'₹{total_amount:,.0f} - {customer_name} (Credit)',
                        amount=total_amount,
                        reference_id=bill_id,
                        reference_type='bill',
                        icon_type='success',
                        metadata={
                            'bill_number': bill_number,
                            'payment_method': payment_method,
                            'is_credit': True,
                            'has_dropdown': True,
                            'dropdown_type': 'sales'
                        }
                    )
                    print(f"✅ [DASHBOARD] Credit sale activity logged: {customer_name} - ₹{total_amount}")
                    
                elif payment_method == 'upi':
                    # UPI transaction
                    ActivityTracker.log_activity(
                        activity_type='sale',
                        title='UPI payment received',
                        description=f'₹{total_amount:,.0f} - {customer_name}',
                        amount=total_amount,
                        reference_id=bill_id,
                        reference_type='bill',
                        icon_type='success',
                        metadata={
                            'bill_number': bill_number,
                            'payment_method': payment_method,
                            'has_dropdown': True,
                            'dropdown_type': 'sales'
                        }
                    )
                    print(f"✅ [DASHBOARD] UPI payment activity logged: {customer_name} - ₹{total_amount}")
                    
                elif payment_method == 'card':
                    # Card transaction
                    ActivityTracker.log_activity(
                        activity_type='sale',
                        title='Card payment processed',
                        description=f'₹{total_amount:,.0f} - {customer_name}',
                        amount=total_amount,
                        reference_id=bill_id,
                        reference_type='bill',
                        icon_type='success',
                        metadata={
                            'bill_number': bill_number,
                            'payment_method': payment_method,
                            'has_dropdown': True,
                            'dropdown_type': 'sales'
                        }
                    )
                    print(f"✅ [DASHBOARD] Card payment activity logged: {customer_name} - ₹{total_amount}")
                    
                else:
                    # Regular cash sale
                    log_sale_activity(
                        bill_id=bill_id,
                        amount=total_amount,
                        customer_name=customer_name
                    )
                    print(f"✅ [DASHBOARD] Cash sale activity logged: {customer_name} - ₹{total_amount}")
                    
            except Exception as e:
                print(f"⚠️ [DASHBOARD] Failed to log activity: {e}")
            
            print(f"✅ [BILLING SERVICE] Bill created successfully: {bill_number}")
            print(f"✅ [BILLING SERVICE] Sales entries created: {len(data['items'])}")
            
            return {
                "message": "Bill created successfully",
                "bill_id": bill_id,
                "bill_number": bill_number,
                "success": True
            }
            
        except Exception as e:
            # Rollback transaction on error
            conn.rollback()
            conn.close()
            print(f"❌ [BILLING SERVICE] Transaction failed: {e}")
            raise e