"""
Production-Grade Sales Service
Clean sales data management and reporting
"""

from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Optional, Tuple


class SalesService:
    """
    Professional sales service for reporting and analytics
    Sales are auto-created from invoices - this service is read-only for sales data
    """
    
    def __init__(self, db_path: str = 'billing.db'):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_sales(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get sales data with filtering options
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Build date filter based on local time
            now = datetime.now()
            date_condition = "1=1"
            params = []
            
            if filters:
                date_filter = filters.get('filter', 'today')
                
                if date_filter == 'today':
                    filter_date = now.strftime('%Y-%m-%d')
                    date_condition = "DATE(s.created_at) = ?"
                    params = [filter_date]
                elif date_filter == 'yesterday':
                    filter_date = (now - timedelta(days=1)).strftime('%Y-%m-%d')
                    date_condition = "DATE(s.created_at) = ?"
                    params = [filter_date]
                elif date_filter == 'week':
                    week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
                    date_condition = "DATE(s.created_at) >= ?"
                    params = [week_start]
                elif date_filter == 'month':
                    month_start = now.replace(day=1).strftime('%Y-%m-%d')
                    date_condition = "DATE(s.created_at) >= ?"
                    params = [month_start]
                elif date_filter == 'custom':
                    if filters.get('from_date') and filters.get('to_date'):
                        date_condition = "DATE(s.created_at) BETWEEN ? AND ?"
                        params = [filters['from_date'], filters['to_date']]
            
            # Get sales data with joins
            limit = filters.get('limit', 100) if filters else 100
            
            sales = conn.execute(f'''
                SELECT 
                    s.*,
                    b.bill_number,
                    b.total_amount as bill_total,
                    b.status as bill_status,
                    c.name as customer_name,
                    c.phone as customer_phone,
                    p.name as product_name,
                    p.category as product_category,
                    p.cost as product_cost,
                    (s.total_price - (p.cost * s.quantity)) as profit
                FROM sales s
                LEFT JOIN bills b ON s.bill_id = b.id
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN products p ON s.product_id = p.id
                WHERE {date_condition}
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', params + [limit]).fetchall()
            
            # Get summary statistics
            summary = conn.execute(f'''
                SELECT 
                    COUNT(DISTINCT s.bill_id) as total_bills,
                    COUNT(*) as total_items,
                    COALESCE(SUM(s.total_price), 0) as total_revenue,
                    COALESCE(SUM(s.quantity), 0) as total_quantity,
                    COALESCE(AVG(s.unit_price), 0) as avg_unit_price,
                    COALESCE(SUM(s.total_price - (p.cost * s.quantity)), 0) as total_profit
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                WHERE {date_condition}
            ''', params).fetchone()
            
            return True, {
                "success": True,
                "sales": [dict(row) for row in sales],
                "summary": dict(summary) if summary else {},
                "filter_applied": filters.get('filter', 'today') if filters else 'today',
                "total_records": len(sales)
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_sales_summary(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get sales summary for different time periods
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
            week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
            month_start = now.replace(day=1).strftime('%Y-%m-%d')
            
            # Today's sales
            today_sales = conn.execute('''
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM bills WHERE DATE(created_at) = ?
            ''', (today,)).fetchone()
            
            # Yesterday's sales
            yesterday_sales = conn.execute('''
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM bills WHERE DATE(created_at) = ?
            ''', (yesterday,)).fetchone()
            
            # Week's sales
            week_sales = conn.execute('''
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM bills WHERE DATE(created_at) >= ?
            ''', (week_start,)).fetchone()
            
            # Month's sales
            month_sales = conn.execute('''
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM bills WHERE DATE(created_at) >= ?
            ''', (month_start,)).fetchone()
            
            # Top selling products today
            top_products = conn.execute('''
                SELECT 
                    p.name as product_name,
                    SUM(s.quantity) as quantity_sold,
                    SUM(s.total_price) as revenue
                FROM sales s
                JOIN products p ON s.product_id = p.id
                WHERE DATE(s.created_at) = ?
                GROUP BY s.product_id, p.name
                ORDER BY quantity_sold DESC
                LIMIT 5
            ''', (today,)).fetchall()
            
            return True, {
                "success": True,
                "today": dict(today_sales),
                "yesterday": dict(yesterday_sales),
                "week": dict(week_sales),
                "month": dict(month_sales),
                "top_products": [dict(row) for row in top_products]
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_sales_by_product(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get sales grouped by product
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Default date range
            date_from = filters.get('from', datetime.now().strftime('%Y-%m-%d')) if filters else datetime.now().strftime('%Y-%m-%d')
            date_to = filters.get('to', datetime.now().strftime('%Y-%m-%d')) if filters else datetime.now().strftime('%Y-%m-%d')
            
            product_sales = conn.execute('''
                SELECT 
                    s.product_id,
                    s.product_name,
                    s.category,
                    COUNT(DISTINCT s.bill_id) as transactions,
                    SUM(s.quantity) as total_quantity,
                    SUM(s.total_price) as total_sales,
                    AVG(s.unit_price) as avg_price,
                    p.stock as current_stock,
                    p.min_stock
                FROM sales s
                LEFT JOIN products p ON s.product_id = p.id
                WHERE s.sale_date BETWEEN ? AND ?
                GROUP BY s.product_id, s.product_name, s.category
                ORDER BY total_sales DESC
            ''', (date_from, date_to)).fetchall()
            
            return True, {
                "success": True,
                "product_sales": [dict(row) for row in product_sales],
                "date_range": {"from": date_from, "to": date_to}
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()
    
    def get_sales_by_category(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get sales grouped by category
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Default date range
            date_from = filters.get('from', datetime.now().strftime('%Y-%m-%d')) if filters else datetime.now().strftime('%Y-%m-%d')
            date_to = filters.get('to', datetime.now().strftime('%Y-%m-%d')) if filters else datetime.now().strftime('%Y-%m-%d')
            
            category_sales = conn.execute('''
                SELECT 
                    s.category,
                    COUNT(DISTINCT s.bill_id) as transactions,
                    COUNT(DISTINCT s.product_id) as unique_products,
                    SUM(s.quantity) as total_quantity,
                    SUM(s.total_price) as total_sales,
                    AVG(s.total_price) as avg_sale_value
                FROM sales s
                WHERE s.sale_date BETWEEN ? AND ?
                GROUP BY s.category
                ORDER BY total_sales DESC
            ''', (date_from, date_to)).fetchall()
            
            return True, {
                "success": True,
                "category_sales": [dict(row) for row in category_sales],
                "date_range": {"from": date_from, "to": date_to}
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()