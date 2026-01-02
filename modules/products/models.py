"""
Products models
COPIED AS-IS from app.py
"""

from modules.shared.database import get_db_connection

class ProductsModels:
    
    @staticmethod
    def get_all_products():
        """Get all active products"""
        conn = get_db_connection()
        try:
            products = conn.execute('SELECT * FROM products WHERE is_active = 1').fetchall()
            return [dict(row) for row in products]
        finally:
            conn.close()
    
    @staticmethod
    def get_product_by_id(product_id):
        """Get product by ID"""
        conn = get_db_connection()
        try:
            product = conn.execute('SELECT * FROM products WHERE id = ? AND is_active = 1', (product_id,)).fetchone()
            return dict(product) if product else None
        finally:
            conn.close()
    
    @staticmethod
    def get_product_by_barcode(barcode):
        """Get product by barcode"""
        conn = get_db_connection()
        try:
            product = conn.execute('SELECT * FROM products WHERE barcode_data = ? AND is_active = 1', (barcode,)).fetchone()
            return dict(product) if product else None
        finally:
            conn.close()
    
    @staticmethod
    def get_products_with_barcodes():
        """Get all products that have barcodes"""
        conn = get_db_connection()
        try:
            products = conn.execute("SELECT id, name, barcode_data FROM products WHERE barcode_data IS NOT NULL AND barcode_data != '' AND is_active = 1").fetchall()
            return [dict(row) for row in products]
        finally:
            conn.close()
    
    @staticmethod
    def check_product_code_exists(code, exclude_id=None):
        """Check if product code already exists"""
        conn = get_db_connection()
        try:
            if exclude_id:
                product = conn.execute('SELECT id FROM products WHERE code = ? AND id != ?', (code, exclude_id)).fetchone()
            else:
                product = conn.execute('SELECT id FROM products WHERE code = ?', (code,)).fetchone()
            return product is not None
        finally:
            conn.close()
    
    @staticmethod
    def check_barcode_exists(barcode, exclude_id=None):
        """Check if barcode already exists"""
        conn = get_db_connection()
        try:
            if exclude_id:
                product = conn.execute('SELECT id, name FROM products WHERE barcode_data = ? AND is_active = 1 AND id != ?', (barcode, exclude_id)).fetchone()
            else:
                product = conn.execute('SELECT id, name FROM products WHERE barcode_data = ? AND is_active = 1', (barcode,)).fetchone()
            return dict(product) if product else None
        finally:
            conn.close()
    
    @staticmethod
    def create_product(product_data):
        """Create a new product"""
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO products (
                    id, code, name, category, price, cost, stock, min_stock, 
                    unit, business_type, barcode_data, barcode_image, image_url, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", product_data)
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def update_product(product_id, product_data):
        """Update an existing product"""
        conn = get_db_connection()
        try:
            conn.execute("""UPDATE products SET
                    code = ?, name = ?, category = ?, price = ?, cost = ?, 
                    stock = ?, min_stock = ?, unit = ?, business_type = ?,
                    barcode_data = ?, barcode_image = ?, image_url = ?
                WHERE id = ?""", product_data + (product_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def delete_product(product_id):
        """Delete a product"""
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    
    @staticmethod
    def update_product_barcode(product_id, barcode):
        """Update product barcode"""
        conn = get_db_connection()
        try:
            conn.execute("UPDATE products SET barcode_data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (barcode, product_id))
            conn.commit()
            return True
        finally:
            conn.close()