"""
Production-Grade Product Service
Clean product management with proper validation
"""

from datetime import datetime
import sqlite3
import uuid
from typing import Dict, List, Optional, Tuple


class ProductService:
    """
    Professional product service
    Products are never directly edited during billing - only stock is reduced
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
    
    def get_products(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get products with optional filtering
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            query = 'SELECT * FROM products WHERE is_active = 1'
            params = []
            
            if filters:
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                
                if filters.get('low_stock'):
                    query += ' AND stock <= min_stock'
                
                if filters.get('search'):
                    query += ' AND (name LIKE ? OR code LIKE ?)'
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
            
            query += ' ORDER BY name'
            
            if filters and filters.get('limit'):
                query += ' LIMIT ?'
                params.append(filters['limit'])
            
            products = conn.execute(query, params).fetchall()
            
            return True, {
                "success": True,
                "products": [dict(row) for row in products],
                "total_records": len(products)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_product_by_id(self, product_id: str) -> Tuple[bool, Dict]:
        """
        Get product by ID
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            product = conn.execute(
                'SELECT * FROM products WHERE id = ? AND is_active = 1',
                (product_id,)
            ).fetchone()
            
            if not product:
                return False, {
                    "success": False,
                    "message": "Product not found"
                }
            
            return True, {
                "success": True,
                "product": dict(product)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_product_by_barcode(self, barcode: str) -> Tuple[bool, Dict]:
        """
        Get product by barcode
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            product = conn.execute(
                'SELECT * FROM products WHERE barcode_data = ? AND is_active = 1',
                (barcode,)
            ).fetchone()
            
            if not product:
                return False, {
                    "success": False,
                    "message": "Product not found"
                }
            
            return True, {
                "success": True,
                "product": dict(product)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def create_product(self, data: Dict) -> Tuple[bool, Dict]:
        """
        Create new product
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Validate required fields
            if not data.get('name'):
                return False, {
                    "success": False,
                    "message": "Product name is required"
                }
            
            if not data.get('price') or data['price'] <= 0:
                return False, {
                    "success": False,
                    "message": "Valid price is required"
                }
            
            # Generate product ID and code if not provided
            product_id = self._generate_id()
            product_code = data.get('code') or f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Check if code already exists
            existing = conn.execute(
                'SELECT id FROM products WHERE code = ?',
                (product_code,)
            ).fetchone()
            
            if existing:
                return False, {
                    "success": False,
                    "message": "Product code already exists"
                }
            
            # Check if barcode already exists (if provided)
            if data.get('barcode_data'):
                existing_barcode = conn.execute(
                    'SELECT id FROM products WHERE barcode_data = ?',
                    (data['barcode_data'],)
                ).fetchone()
                
                if existing_barcode:
                    return False, {
                        "success": False,
                        "message": "Barcode already exists"
                    }
            
            # Insert product
            conn.execute('''
                INSERT INTO products (
                    id, code, name, category, price, cost, stock, min_stock, 
                    unit, business_type, barcode_data, barcode_image, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product_id,
                product_code,
                data['name'],
                data.get('category', 'General'),
                data['price'],
                data.get('cost', 0),
                data.get('stock', 0),
                data.get('min_stock', 0),
                data.get('unit', 'piece'),
                data.get('business_type', 'retail'),
                data.get('barcode_data'),
                data.get('barcode_image'),
                1
            ))
            
            conn.commit()
            
            return True, {
                "success": True,
                "message": "Product created successfully",
                "product_id": product_id,
                "product_code": product_code
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def update_product(self, product_id: str, data: Dict) -> Tuple[bool, Dict]:
        """
        Update product (excluding stock - stock is managed by billing)
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Check if product exists
            existing = conn.execute(
                'SELECT * FROM products WHERE id = ? AND is_active = 1',
                (product_id,)
            ).fetchone()
            
            if not existing:
                return False, {
                    "success": False,
                    "message": "Product not found"
                }
            
            # Update product (excluding stock)
            conn.execute('''
                UPDATE products SET
                    name = ?,
                    category = ?,
                    price = ?,
                    cost = ?,
                    min_stock = ?,
                    unit = ?,
                    business_type = ?,
                    barcode_data = ?,
                    barcode_image = ?
                WHERE id = ?
            ''', (
                data.get('name', existing['name']),
                data.get('category', existing['category']),
                data.get('price', existing['price']),
                data.get('cost', existing['cost']),
                data.get('min_stock', existing['min_stock']),
                data.get('unit', existing['unit']),
                data.get('business_type', existing['business_type']),
                data.get('barcode_data', existing['barcode_data']),
                data.get('barcode_image', existing['barcode_image']),
                product_id
            ))
            
            conn.commit()
            
            return True, {
                "success": True,
                "message": "Product updated successfully"
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def delete_product(self, product_id: str) -> Tuple[bool, Dict]:
        """
        Soft delete product (set is_active = 0)
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Check if product exists
            existing = conn.execute(
                'SELECT name FROM products WHERE id = ? AND is_active = 1',
                (product_id,)
            ).fetchone()
            
            if not existing:
                return False, {
                    "success": False,
                    "message": "Product not found"
                }
            
            # Soft delete
            conn.execute(
                'UPDATE products SET is_active = 0 WHERE id = ?',
                (product_id,)
            )
            
            conn.commit()
            
            return True, {
                "success": True,
                "message": f"Product '{existing['name']}' deleted successfully"
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()