"""
Product Variants Service
Handles product variants (different sizes, prices for same product)
"""

from modules.shared.database import get_db_connection, generate_id
from datetime import datetime

class ProductVariantsService:
    
    def add_variant(self, product_id, variant_data):
        """Add a variant to a product"""
        conn = get_db_connection()
        
        try:
            variant_id = generate_id()
            
            conn.execute("""INSERT INTO product_variants (
                    id, product_id, variant_name, size, price, cost, stock, 
                    sku, barcode, is_active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                variant_id,
                product_id,
                variant_data.get('variant_name'),
                variant_data.get('size'),
                float(variant_data.get('price', 0)),
                float(variant_data.get('cost', 0)),
                int(variant_data.get('stock', 0)),
                variant_data.get('sku'),
                variant_data.get('barcode'),
                1,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Variant added successfully",
                "variant_id": variant_id
            }
            
        except Exception as e:
            conn.close()
            print(f"❌ [VARIANT ADD] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_product_variants(self, product_id):
        """Get all variants for a product"""
        conn = get_db_connection()
        
        variants = conn.execute("""SELECT * FROM product_variants 
            WHERE product_id = ? AND is_active = 1 
            ORDER BY price ASC""", (product_id,)).fetchall()
        
        conn.close()
        
        return [dict(row) for row in variants]
    
    def update_variant(self, variant_id, variant_data):
        """Update a variant"""
        conn = get_db_connection()
        
        try:
            conn.execute("""UPDATE product_variants SET
                    variant_name = ?, size = ?, price = ?, cost = ?, 
                    stock = ?, sku = ?, barcode = ?
                WHERE id = ?""", (
                variant_data.get('variant_name'),
                variant_data.get('size'),
                float(variant_data.get('price', 0)),
                float(variant_data.get('cost', 0)),
                int(variant_data.get('stock', 0)),
                variant_data.get('sku'),
                variant_data.get('barcode'),
                variant_id
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Variant updated successfully"
            }
            
        except Exception as e:
            conn.close()
            print(f"❌ [VARIANT UPDATE] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_variant(self, variant_id):
        """Delete a variant (soft delete)"""
        conn = get_db_connection()
        
        try:
            conn.execute("UPDATE product_variants SET is_active = 0 WHERE id = ?", (variant_id,))
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Variant deleted successfully"
            }
            
        except Exception as e:
            conn.close()
            print(f"❌ [VARIANT DELETE] Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
