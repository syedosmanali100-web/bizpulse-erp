"""
Billing models
COPIED AS-IS from app_original_backup.py
"""

from modules.shared.database import get_db_connection

class BillingModels:
    
    @staticmethod
    def get_all_bills():
        """Get all bills with customer information"""
        conn = get_db_connection()
        try:
            bills = conn.execute("""SELECT b.*, c.name as customer_name 
                FROM bills b 
                LEFT JOIN customers c ON b.customer_id = c.id 
                ORDER BY b.created_at DESC""").fetchall()
            return [dict(row) for row in bills]
        finally:
            conn.close()
    
    @staticmethod
    def get_bill_items(bill_id):
        """Get items for a specific bill"""
        conn = get_db_connection()
        try:
            items = conn.execute("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,)).fetchall()
            return [dict(row) for row in items]
        finally:
            conn.close()
    
    @staticmethod
    def get_product_stock(product_id):
        """Get current stock for a product"""
        conn = get_db_connection()
        try:
            product = conn.execute("SELECT name, stock FROM products WHERE id = ?", (product_id,)).fetchone()
            return dict(product) if product else None
        finally:
            conn.close()
    
    @staticmethod
    def create_bill_record(bill_data):
        """Create a bill record in the database"""
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO bills (id, bill_number, customer_id, customer_name, business_type, subtotal, tax_amount, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", bill_data)
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def create_bill_item(item_data):
        """Create a bill item record"""
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO bill_items (id, bill_id, product_id, product_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", item_data)
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def update_product_stock(product_id, quantity):
        """Update product stock after sale"""
        conn = get_db_connection()
        try:
            conn.execute("""UPDATE products SET stock = CASE 
                    WHEN stock - ? >= 0 THEN stock - ?
                    ELSE 0
                END 
                WHERE id = ?""", (quantity, quantity, product_id))
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def create_sales_entry(sales_data):
        """Create a sales entry record"""
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO sales (
                    id, bill_id, bill_number, customer_id, customer_name,
                    product_id, product_name, category, quantity, unit_price,
                    total_price, tax_amount, discount_amount, payment_method,
                    sale_date, sale_time, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sales_data)
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def create_payment_record(payment_data):
        """Create a payment record"""
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO payments (id, bill_id, method, amount, processed_at)
                VALUES (?, ?, ?, ?, ?)""", payment_data)
            conn.commit()
            return True
        finally:
            conn.close()