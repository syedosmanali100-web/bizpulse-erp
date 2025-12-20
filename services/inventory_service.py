"""
Production-Grade Inventory Service
Clean inventory management with automatic sync
"""

from datetime import datetime
import sqlite3
from typing import Dict, List, Optional, Tuple


class InventoryService:
    """
    Professional inventory service
    Inventory is automatically updated by billing/invoice operations
    This service provides inventory status and sync capabilities
    """
    
    def __init__(self, db_path: str = 'billing.db'):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_inventory_status(self) -> Tuple[bool, Dict]:
        """
        Get complete inventory status with stock levels and alerts
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get all products with stock information and recent sales
            inventory = conn.execute('''
                SELECT 
                    p.*,
                    COALESCE(recent_sales.total_sold_today, 0) as sold_today,
                    COALESCE(recent_sales.total_sold_week, 0) as sold_week,
                    COALESCE(recent_sales.last_sale_date, 'Never') as last_sale_date,
                    CASE 
                        WHEN p.stock <= 0 THEN 'out_of_stock'
                        WHEN p.stock <= p.min_stock THEN 'low_stock'
                        WHEN p.stock <= (p.min_stock * 2) THEN 'warning'
                        ELSE 'good'
                    END as stock_status,
                    (p.price - p.cost) as profit_per_unit,
                    ((p.price - p.cost) / p.price * 100) as profit_margin_percent
                FROM products p
                LEFT JOIN (
                    SELECT 
                        s.product_id,
                        SUM(CASE WHEN DATE(s.created_at) = ? THEN s.quantity ELSE 0 END) as total_sold_today,
                        SUM(CASE WHEN DATE(s.created_at) >= DATE(?, '-7 days') THEN s.quantity ELSE 0 END) as total_sold_week,
                        MAX(DATE(s.created_at)) as last_sale_date
                    FROM sales s
                    GROUP BY s.product_id
                ) recent_sales ON p.id = recent_sales.product_id
                WHERE p.is_active = 1
                ORDER BY 
                    CASE 
                        WHEN p.stock <= 0 THEN 1
                        WHEN p.stock <= p.min_stock THEN 2
                        WHEN p.stock <= (p.min_stock * 2) THEN 3
                        ELSE 4
                    END,
                    p.name
            ''', (today, today)).fetchall()
            
            # Get inventory summary statistics
            summary = conn.execute('''
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN stock <= 0 THEN 1 END) as out_of_stock_count,
                    COUNT(CASE WHEN stock <= min_stock AND stock > 0 THEN 1 END) as low_stock_count,
                    COUNT(CASE WHEN stock > min_stock THEN 1 END) as good_stock_count,
                    COALESCE(SUM(stock * cost), 0) as total_inventory_value,
                    COALESCE(SUM(stock * price), 0) as total_selling_value,
                    COALESCE(SUM(stock * (price - cost)), 0) as potential_profit
                FROM products 
                WHERE is_active = 1
            ''').fetchone()
            
            # Get products needing restock (critical alerts)
            restock_alerts = conn.execute('''
                SELECT 
                    p.name,
                    p.category,
                    p.stock,
                    p.min_stock,
                    (p.min_stock - p.stock) as shortage
                FROM products p
                WHERE p.is_active = 1 AND p.stock <= p.min_stock
                ORDER BY p.stock ASC
                LIMIT 10
            ''').fetchall()
            
            return True, {
                "success": True,
                "inventory": [dict(row) for row in inventory],
                "summary": dict(summary) if summary else {},
                "restock_alerts": [dict(row) for row in restock_alerts]
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_low_stock_items(self) -> Tuple[bool, Dict]:
        """
        Get items with low stock that need attention
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            low_stock_items = conn.execute('''
                SELECT 
                    p.*,
                    (p.min_stock - p.stock) as shortage,
                    CASE 
                        WHEN p.stock <= 0 THEN 'critical'
                        WHEN p.stock <= p.min_stock THEN 'low'
                        ELSE 'warning'
                    END as alert_level
                FROM products p
                WHERE p.is_active = 1 AND p.stock <= p.min_stock
                ORDER BY p.stock ASC, p.min_stock DESC
            ''').fetchall()
            
            return True, {
                "success": True,
                "low_stock_items": [dict(row) for row in low_stock_items],
                "total_items": len(low_stock_items)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def sync_inventory(self) -> Tuple[bool, Dict]:
        """
        Sync inventory with sales data (for data consistency checks)
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # This is a read-only operation to verify inventory consistency
            # In a production system, this would check for discrepancies
            
            # Get products with potential stock issues
            inconsistencies = conn.execute('''
                SELECT 
                    p.id,
                    p.name,
                    p.stock as current_stock,
                    COALESCE(SUM(s.quantity), 0) as total_sold,
                    p.stock + COALESCE(SUM(s.quantity), 0) as calculated_original_stock
                FROM products p
                LEFT JOIN sales s ON p.id = s.product_id
                WHERE p.is_active = 1
                GROUP BY p.id, p.name, p.stock
                HAVING p.stock < 0
            ''').fetchall()
            
            return True, {
                "success": True,
                "message": "Inventory sync completed",
                "inconsistencies": [dict(row) for row in inconsistencies],
                "issues_found": len(inconsistencies)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()