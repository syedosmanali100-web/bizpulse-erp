"""
Production-Grade Billing Service
Clean, scalable, and error-free billing backend
"""

from datetime import datetime
import sqlite3
import uuid
from typing import Dict, List, Optional, Tuple


class BillingService:
    """
    Professional billing service with atomic transactions and proper error handling
    """
    
    def __init__(self, db_path: str = 'billing.db'):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format (IST timezone safe)"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def validate_bill_data(self, data: Dict) -> Tuple[bool, str]:
        """
        Validate bill data before processing
        Returns: (is_valid, error_message)
        """
        if not data.get('items') or len(data['items']) == 0:
            return False, "No items in bill"
        
        if not data.get('total_amount') or data['total_amount'] <= 0:
            return False, "Invalid total amount"
        
        # Validate each item
        for item in data['items']:
            if not item.get('product_id'):
                return False, "Product ID required for all items"
            
            if not item.get('quantity') or item['quantity'] <= 0:
                return False, "Invalid quantity for item"
            
            if not item.get('unit_price') or item['unit_price'] <= 0:
                return False, "Invalid unit price for item"
        
        return True, ""
    
    def check_inventory_availability(self, items: List[Dict]) -> Tuple[bool, str]:
        """
        Check if all items have sufficient stock
        Returns: (is_available, error_message)
        """
        conn = self._get_connection()
        
        try:
            for item in items:
                product_id = item['product_id']
                required_quantity = item['quantity']
                
                # Get current stock
                product = conn.execute(
                    'SELECT name, stock FROM products WHERE id = ? AND is_active = 1',
                    (product_id,)
                ).fetchone()
                
                if not product:
                    return False, f"Product {product_id} not found or inactive"
                
                if product['stock'] < required_quantity:
                    return False, f"Insufficient stock for {product['name']}. Available: {product['stock']}, Required: {required_quantity}"
            
            return True, ""
            
        finally:
            conn.close()
    
    def create_bill(self, data: Dict) -> Tuple[bool, Dict]:
        """
        Create a new bill with atomic transaction handling
        Returns: (success, result_data)
        """
        # Step 1: Validate input data
        is_valid, error_msg = self.validate_bill_data(data)
        if not is_valid:
            return False, {"error": error_msg}
        
        # Step 2: Check inventory availability
        is_available, error_msg = self.check_inventory_availability(data['items'])
        if not is_available:
            return False, {"error": error_msg}
        
        # Step 3: Create bill with atomic transaction
        conn = self._get_connection()
        
        try:
            # Start transaction
            conn.execute('BEGIN TRANSACTION')
            
            # Generate bill details
            bill_id = self._generate_id()
            current_time = self._get_current_timestamp()
            bill_number = f"BILL-{datetime.now().strftime('%Y%m%d')}-{bill_id[:8]}"
            
            # Create bill record
            conn.execute('''
                INSERT INTO bills (
                    id, bill_number, customer_id, business_type, 
                    subtotal, tax_amount, discount_amount, total_amount, 
                    status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bill_id,
                bill_number,
                data.get('customer_id'),
                data.get('business_type', 'retail'),
                data.get('subtotal', data['total_amount']),
                data.get('tax_amount', 0),
                data.get('discount_amount', 0),
                data['total_amount'],
                'completed',
                current_time
            ))
            
            # Get customer name if exists
            customer_name = None
            if data.get('customer_id'):
                customer = conn.execute(
                    'SELECT name FROM customers WHERE id = ?',
                    (data['customer_id'],)
                ).fetchone()
                customer_name = customer['name'] if customer else None
            
            # Process each bill item
            for item in data['items']:
                item_id = self._generate_id()
                product_id = item['product_id']
                quantity = item['quantity']
                unit_price = item['unit_price']
                total_price = quantity * unit_price
                
                # Insert bill item
                conn.execute('''
                    INSERT INTO bill_items (
                        id, bill_id, product_id, product_name, 
                        quantity, unit_price, total_price
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, bill_id, product_id, 
                    item.get('product_name', 'Unknown Product'),
                    quantity, unit_price, total_price
                ))
                
                # Reduce inventory stock
                conn.execute('''
                    UPDATE products 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (quantity, product_id))
                
                # Get product details for sales entry
                product = conn.execute(
                    'SELECT category, cost FROM products WHERE id = ?',
                    (product_id,)
                ).fetchone()
                
                # Create sales entry
                sale_id = self._generate_id()
                # Use the bill's created_at timestamp for consistency
                sale_date = current_time.split(' ')[0]  # Extract date part
                sale_time = current_time.split(' ')[1]  # Extract time part
                
                # Calculate proportional tax and discount
                subtotal = data.get('subtotal', data['total_amount'])
                item_tax = (total_price / subtotal) * data.get('tax_amount', 0) if subtotal > 0 else 0
                item_discount = (total_price / subtotal) * data.get('discount_amount', 0) if subtotal > 0 else 0
                
                conn.execute('''
                    INSERT INTO sales (
                        id, bill_id, bill_number, customer_id, customer_name,
                        product_id, product_name, category, quantity, unit_price,
                        total_price, tax_amount, discount_amount, payment_method,
                        sale_date, sale_time, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sale_id, bill_id, bill_number, data.get('customer_id'), customer_name,
                    product_id, item.get('product_name', 'Unknown Product'),
                    product['category'] if product else 'General',
                    quantity, unit_price, total_price,
                    item_tax, item_discount, data.get('payment_method', 'cash'),
                    sale_date, sale_time, current_time
                ))
            
            # Add payment record if payment method specified
            if data.get('payment_method'):
                payment_id = self._generate_id()
                conn.execute('''
                    INSERT INTO payments (id, bill_id, method, amount, processed_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (payment_id, bill_id, data['payment_method'], data['total_amount'], current_time))
            
            # Commit transaction
            conn.commit()
            
            return True, {
                "bill_id": bill_id,
                "bill_number": bill_number,
                "total_amount": data['total_amount'],
                "items_count": len(data['items']),
                "created_at": current_time
            }
            
        except Exception as e:
            # Rollback transaction on any error
            conn.rollback()
            return False, {"error": f"Transaction failed: {str(e)}"}
            
        finally:
            conn.close()
    
    def get_bills(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get bills with optional filtering
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Build query with filters
            query = '''
                SELECT b.*, c.name as customer_name, c.phone as customer_phone
                FROM bills b
                LEFT JOIN customers c ON b.customer_id = c.id
            '''
            
            params = []
            conditions = []
            
            if filters:
                if filters.get('status'):
                    conditions.append('b.status = ?')
                    params.append(filters['status'])
                
                if filters.get('date_from'):
                    conditions.append('DATE(b.created_at) >= ?')
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append('DATE(b.created_at) <= ?')
                    params.append(filters['date_to'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY b.created_at DESC'
            
            if filters and filters.get('limit'):
                query += ' LIMIT ?'
                params.append(filters['limit'])
            
            bills = conn.execute(query, params).fetchall()
            
            return True, {
                "bills": [dict(row) for row in bills],
                "total_records": len(bills)
            }
            
        except Exception as e:
            return False, {"error": str(e)}
            
        finally:
            conn.close()
    
    def get_bill_by_id(self, bill_id: str) -> Tuple[bool, Dict]:
        """
        Get bill details by ID including items
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Get bill details
            bill = conn.execute('''
                SELECT b.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address
                FROM bills b
                LEFT JOIN customers c ON b.customer_id = c.id
                WHERE b.id = ?
            ''', (bill_id,)).fetchone()
            
            if not bill:
                return False, {"error": "Bill not found"}
            
            # Get bill items
            items = conn.execute('''
                SELECT * FROM bill_items WHERE bill_id = ?
            ''', (bill_id,)).fetchall()
            
            # Get payments
            payments = conn.execute('''
                SELECT * FROM payments WHERE bill_id = ?
            ''', (bill_id,)).fetchall()
            
            return True, {
                "bill": dict(bill),
                "items": [dict(row) for row in items],
                "payments": [dict(row) for row in payments]
            }
            
        except Exception as e:
            return False, {"error": str(e)}
            
        finally:
            conn.close()
    
    def delete_bill(self, bill_id: str) -> Tuple[bool, Dict]:
        """
        Delete bill and revert all changes atomically
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Start transaction
            conn.execute('BEGIN TRANSACTION')
            
            # Check if bill exists
            bill = conn.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
            if not bill:
                return False, {"error": "Bill not found"}
            
            # Get all bill items to revert stock
            bill_items = conn.execute('''
                SELECT product_id, quantity FROM bill_items WHERE bill_id = ?
            ''', (bill_id,)).fetchall()
            
            # Revert stock for each item
            for item in bill_items:
                conn.execute('''
                    UPDATE products SET stock = stock + ? WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            # Delete related records in correct order
            conn.execute('DELETE FROM payments WHERE bill_id = ?', (bill_id,))
            conn.execute('DELETE FROM sales WHERE bill_id = ?', (bill_id,))
            conn.execute('DELETE FROM bill_items WHERE bill_id = ?', (bill_id,))
            conn.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
            
            # Commit transaction
            conn.commit()
            
            return True, {
                "message": f"Bill {bill['bill_number']} deleted successfully",
                "reverted_items": len(bill_items)
            }
            
        except Exception as e:
            # Rollback transaction on error
            conn.rollback()
            return False, {"error": f"Delete failed: {str(e)}"}
            
        finally:
            conn.close()