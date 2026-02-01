"""
Billing service
UPDATED to use new transaction-based stock system
"""

from modules.shared.database import get_db_connection, generate_id
from datetime import datetime
from modules.dashboard.models import ActivityTracker, log_sale_activity, log_order_activity

# Import new stock service
try:
    from modules.stock.service import StockService
    from modules.stock.database import get_current_stock
    stock_service = StockService()
except ImportError:
    # Fallback if stock module is not available
    stock_service = None
    def get_current_stock(product_id, business_owner_id=None):
        # Fallback to old products.stock field
        conn = get_db_connection()
        result = conn.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
        conn.close()
        return result[0] if result else 0

# Import notification helper
try:
    from modules.notifications.routes import create_notification_for_user
except ImportError:
    # Fallback if notifications module is not available
    def create_notification_for_user(user_id, notification_type, message, action_url=None):
        pass

class BillingService:
    
    def get_all_bills(self, user_id=None):
        """Get all bills with customer information - STRICT DATA ISOLATION"""
        conn = get_db_connection()
        
        if user_id:
            # STRICT FILTER: Only show bills belonging to this user
            bills = conn.execute("""SELECT b.*, c.name as customer_name 
                FROM bills b 
                LEFT JOIN customers c ON b.customer_id = c.id 
                WHERE b.business_owner_id = ?
                ORDER BY b.created_at DESC""", (user_id,)).fetchall()
        else:
            # No user_id: show nothing
            bills = []
        
        conn.close()
        return [dict(row) for row in bills]
    
    def get_bill_items(self, bill_id):
        """Get items for a specific bill - Mobile ERP Style"""
        conn = get_db_connection()
        items = conn.execute("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,)).fetchall()
        conn.close()
        return [dict(row) for row in items]
    
    def create_bill(self, data):
        """Create bill - OPTIMIZED for instant creation"""
        print("📥 [BILLING SERVICE] Received bill data:", data)
        
        # Extract business_owner_id
        business_owner_id = data.get('business_owner_id')
        print(f"📥 [BILLING SERVICE] business_owner_id: {business_owner_id}")
        
        # Validate required fields
        if not data or not data.get('items') or len(data['items']) == 0:
            return {"error": "Items are required", "success": False}
        
        # ============================================================================
        # OPTIMIZED: Batch stock validation with single query
        # ============================================================================
        conn = get_db_connection()
        product_ids = [item['product_id'] for item in data['items']]
        placeholders = ','.join('?' * len(product_ids))
        
        # Get all product details in one query
        products_data = conn.execute(f"""
            SELECT id, name, stock, category, min_stock 
            FROM products 
            WHERE id IN ({placeholders})
        """, product_ids).fetchall()
        
        products_map = {p['id']: dict(p) for p in products_data}
        
        # Quick stock validation
        out_of_stock_items = []
        for item in data['items']:
            product = products_map.get(item['product_id'])
            if not product:
                continue
            
            current_stock = product['stock']
            if current_stock < item['quantity']:
                out_of_stock_items.append(
                    f"❌ {product['name']}: Requested {item['quantity']}, Available {current_stock}"
                )
        
        if out_of_stock_items:
            conn.close()
            return {
                "error": "Insufficient stock for some items",
                "out_of_stock_items": out_of_stock_items,
                "success": False
            }
        
        # ============================================================================
        # Proceed with bill creation
        # ============================================================================
        
        bill_id = generate_id()
        bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
        print(f"📝 [BILLING SERVICE] Generated bill: {bill_number}")
        
        # Start transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Prepare data
            customer_name = data.get('customer_name', 'Walk-in Customer')
            gst_rate = data.get('gst_rate', 18)
            payment_method = data.get('payment_method', 'cash')
            total_amount = data.get('total_amount', 0)
            subtotal = data.get('subtotal', 0)
            tax_amount = data.get('tax_amount', 0)
            discount_amount = data.get('discount_amount', 0)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sale_date = datetime.now().strftime('%Y-%m-%d')
            sale_time = datetime.now().strftime('%H:%M:%S')
            
            # Create bill record
            conn.execute("""INSERT INTO bills (id, bill_number, customer_id, customer_name, business_type, business_owner_id, subtotal, tax_amount, discount_amount, gst_rate, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                bill_id, bill_number, data.get('customer_id'), customer_name,
                data.get('business_type', 'retail'), business_owner_id,
                subtotal, tax_amount, discount_amount, gst_rate, total_amount,
                'completed', current_time
            ))
            
            # ============================================================================
            # OPTIMIZED: Batch prepare all inserts
            # ============================================================================
            bill_items_data = []
            sales_data = []
            stock_updates = []
            stock_transactions = []
            low_stock_products = []
            
            for item in data['items']:
                item_id = generate_id()
                product = products_map.get(item['product_id'])
                
                # Prepare bill item
                bill_items_data.append((
                    item_id, bill_id, item['product_id'], item['product_name'],
                    item['quantity'], item['unit_price'], item['total_price']
                ))
                
                # Prepare stock update
                stock_updates.append((item['quantity'], item['product_id']))
                
                # Prepare stock transaction if service available
                if stock_service:
                    stock_transactions.append({
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'bill_id': bill_id,
                        'bill_number': bill_number
                    })
                
                # Check for low stock (for later notification)
                if product:
                    new_stock = product['stock'] - item['quantity']
                    min_stock = product.get('min_stock', 0) or 0
                    if new_stock <= min_stock and min_stock > 0:
                        low_stock_products.append({
                            'name': product['name'],
                            'stock': new_stock,
                            'min_stock': min_stock
                        })
                
                # Prepare sales entry
                sale_id = generate_id()
                item_tax = (item['total_price'] / subtotal) * tax_amount if subtotal > 0 else 0
                item_discount = (item['total_price'] / subtotal) * discount_amount if subtotal > 0 else 0
                category = product['category'] if product else 'General'
                
                sales_data.append((
                    sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                    item['product_id'], item['product_name'], category,
                    item['quantity'], item['unit_price'], item['total_price'],
                    item_tax, item_discount, payment_method, business_owner_id,
                    sale_date, sale_time, current_time
                ))
            
            # ============================================================================
            # OPTIMIZED: Execute all inserts in batch
            # ============================================================================
            
            # Batch insert bill items
            conn.executemany("""INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", bill_items_data)
            
            # Batch update stock
            conn.executemany("""UPDATE products SET stock = stock - ? WHERE id = ?""", stock_updates)
            
            # Batch insert sales entries
            conn.executemany("""INSERT INTO sales (
                    id, bill_id, bill_number, customer_id, customer_name,
                    product_id, product_name, category, quantity, unit_price,
                    total_price, tax_amount, discount_amount, payment_method,
                    business_owner_id, sale_date, sale_time, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sales_data)
            
            # ============================================================================
            # Handle payment records
            # ============================================================================
            payment_id = generate_id()
            
            if payment_method == 'credit':
                paid_amount = 0
                balance_due = total_amount
                
                conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'unpaid',
                           credit_paid_amount = ?, credit_balance = ?
                    WHERE id = ?""", (payment_method, paid_amount, balance_due, bill_id))
                
                conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                    WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                
                conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                    VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, current_time))
                
                # Credit transaction record
                transaction_id = generate_id()
                transaction_customer_id = data.get('customer_id') or 'walk-in-customer'
                conn.execute("""INSERT INTO credit_transactions (
                        id, bill_id, customer_id, transaction_type, amount, 
                        payment_method, reference_number, notes, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    transaction_id, bill_id, transaction_customer_id, 'credit_issued',
                    balance_due, payment_method, bill_number,
                    f'Credit bill created for {customer_name}', current_time
                ))
                
            elif payment_method == 'partial':
                partial_amount = float(data.get('partial_amount', 0))
                balance_due = total_amount - partial_amount
                partial_payment_method = data.get('partial_payment_method', 'cash')
                
                if partial_amount <= 0:
                    partial_amount = 0
                    balance_due = total_amount
                
                conn.execute("""UPDATE bills SET is_credit = 1, payment_method = ?, payment_status = 'partial',
                           credit_paid_amount = ?, credit_balance = ?, partial_payment_method = ?
                    WHERE id = ?""", (payment_method, partial_amount, balance_due, partial_payment_method, bill_id))
                
                conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                    WHERE bill_id = ?""", (balance_due, partial_amount, bill_id))
                
                conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                    VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, partial_amount, current_time))
                
                # Credit transaction records
                transaction_customer_id = data.get('customer_id') or 'walk-in-customer'
                
                transaction_id_credit = generate_id()
                conn.execute("""INSERT INTO credit_transactions (
                        id, bill_id, customer_id, transaction_type, amount, 
                        payment_method, reference_number, notes, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    transaction_id_credit, bill_id, transaction_customer_id, 'credit_issued',
                    total_amount, payment_method, bill_number,
                    f'Partial payment bill created for {customer_name}', current_time
                ))
                
                if partial_amount > 0:
                    transaction_id_payment = generate_id()
                    conn.execute("""INSERT INTO credit_transactions (
                            id, bill_id, customer_id, transaction_type, amount, 
                            payment_method, reference_number, notes, created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        transaction_id_payment, bill_id, transaction_customer_id, 'payment',
                        partial_amount, partial_payment_method, bill_number,
                        f'Initial partial payment by {customer_name}', current_time
                    ))
                
            else:
                # Regular payment
                paid_amount = total_amount
                balance_due = 0
                
                conn.execute("""UPDATE bills SET payment_method = ?, payment_status = 'paid'
                    WHERE id = ?""", (payment_method, bill_id))
                
                conn.execute("""UPDATE sales SET balance_due = ?, paid_amount = ? 
                    WHERE bill_id = ?""", (balance_due, paid_amount, bill_id))
                
                conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                    VALUES (?, ?, ?, ?, ?)""", (payment_id, bill_id, payment_method, paid_amount, current_time))
            
            # Commit transaction - CRITICAL: Do this BEFORE notifications/logging
            conn.commit()
            conn.close()
            
            print(f"✅ [BILLING SERVICE] Bill created successfully: {bill_number}")
            
            # ============================================================================
            # ASYNC OPERATIONS - After commit (non-blocking)
            # ============================================================================
            
            # Stock transactions (if service available)
            if stock_service and stock_transactions:
                for st in stock_transactions:
                    try:
                        stock_service.create_sale_transaction(
                            product_id=st['product_id'],
                            quantity=st['quantity'],
                            bill_id=st['bill_id'],
                            bill_number=st['bill_number'],
                            created_by=business_owner_id,
                            business_owner_id=business_owner_id
                        )
                    except Exception as e:
                        print(f"⚠️ [STOCK] Transaction failed: {e}")
            
            # Low stock notifications
            for product in low_stock_products:
                try:
                    if product['stock'] == 0:
                        create_notification_for_user(
                            user_id=business_owner_id,
                            notification_type='alert',
                            message=f"Out of stock: {product['name']} (0 remaining)",
                            action_url='/retail/products'
                        )
                    else:
                        create_notification_for_user(
                            user_id=business_owner_id,
                            notification_type='alert',
                            message=f"Low stock alert: {product['name']} (Only {product['stock']} left)",
                            action_url='/retail/products'
                        )
                except Exception as e:
                    print(f"⚠️ [NOTIFICATION] Low stock alert failed: {e}")
            
            # Activity logging
            try:
                if total_amount > 15000:
                    log_order_activity(
                        order_id=bill_id,
                        amount=total_amount,
                        order_type='processed',
                        customer_name=customer_name,
                        item_count=len(data['items'])
                    )
                elif payment_method == 'credit':
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
                elif payment_method in ['upi', 'card']:
                    ActivityTracker.log_activity(
                        activity_type='sale',
                        title=f'{payment_method.upper()} payment {"received" if payment_method == "upi" else "processed"}',
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
                else:
                    log_sale_activity(
                        bill_id=bill_id,
                        amount=total_amount,
                        customer_name=customer_name
                    )
            except Exception as e:
                print(f"⚠️ [ACTIVITY] Logging failed: {e}")
            
            # Sale notification
            try:
                if payment_method == 'credit':
                    notification_message = f"Credit sale completed: ₹{total_amount:,.0f} from {customer_name}"
                elif payment_method == 'partial':
                    partial_amount = float(data.get('partial_amount', 0))
                    notification_message = f"Partial payment sale: ₹{partial_amount:,.0f} paid, ₹{total_amount - partial_amount:,.0f} due from {customer_name}"
                else:
                    notification_message = f"Sale completed: ₹{total_amount:,.0f} from {customer_name}"
                
                create_notification_for_user(
                    user_id=business_owner_id,
                    notification_type='sale',
                    message=notification_message,
                    action_url='/retail/sales'
                )
            except Exception as e:
                print(f"⚠️ [NOTIFICATION] Sale notification failed: {e}")
            
            # Sync broadcasting
            try:
                from modules.sync.utils import broadcast_data_change
                for item in data['items']:
                    sale_data = {
                        'bill_id': bill_id,
                        'bill_number': bill_number,
                        'customer_name': customer_name,
                        'product_name': item['product_name'],
                        'quantity': item['quantity'],
                        'total_price': item['total_price'],
                        'payment_method': payment_method,
                        'created_at': current_time
                    }
                    broadcast_data_change('create', 'sales', sale_data, business_owner_id)
            except Exception as e:
                print(f"⚠️ [SYNC] Broadcasting failed: {e}")
            
            # E-Way Bill check
            try:
                from modules.eway.service import eway_service
                if eway_service.check_eway_requirement(total_amount, 'Maharashtra', 'Maharashtra'):
                    print(f"💡 [E-WAY BILL] Invoice {bill_number} (₹{total_amount}) requires E-Way Bill generation")
            except Exception as e:
                print(f"⚠️ [E-WAY BILL] Check failed: {e}")
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