"""
Earnings service - Handle all earnings and profit calculations
"""

from modules.shared.database import get_db_connection
from datetime import datetime, timedelta

class EarningsService:
    
    def get_earnings_summary(self, date_filter=None, user_id=None):
        """
        Get earnings summary with accurate profit calculations
        Profit = Revenue - Cost (only for PAID bills)
        Credit/Partial bills profit counted only when payment received
        """
        conn = get_db_connection()
        
        # Build date condition
        where_clauses = []
        params = []
        
        # Add user_id filter
        if user_id:
            where_clauses.append("(b.business_owner_id = ? OR b.business_owner_id IS NULL)")
            params.append(user_id)
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                where_clauses.append("DATE(b.created_at) = ?")
                params.append(today)
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(b.created_at) = ?")
                params.append(yesterday)
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(b.created_at) >= ?")
                params.append(week_ago)
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(b.created_at) >= ?")
                params.append(month_ago)
            elif date_filter == 'all':
                # All data - no date filter
                pass
        
        # Build WHERE clause
        date_condition = ""
        if where_clauses:
            date_condition = "WHERE " + " AND ".join(where_clauses)
        
        # Calculate REALIZED profit (only from paid bills)
        query_paid = f"""
            SELECT 
                COUNT(DISTINCT b.id) as transaction_count,
                COALESCE(SUM(b.total_amount), 0) as total_revenue,
                COALESCE(SUM(
                    (SELECT SUM(COALESCE(p.cost, 0) * bi.quantity)
                     FROM bill_items bi
                     LEFT JOIN products p ON bi.product_id = p.id
                     WHERE bi.bill_id = b.id)
                ), 0) as total_cost
            FROM bills b
            {date_condition}
            AND (b.payment_method NOT IN ('credit', 'partial') OR b.payment_method IS NULL)
        """
        
        # Calculate PENDING profit (from credit/partial bills)
        query_pending = f"""
            SELECT 
                COALESCE(SUM(b.credit_balance), 0) as pending_amount,
                COALESCE(SUM(
                    (SELECT SUM((bi.total_price - (COALESCE(p.cost, 0) * bi.quantity)) * (b.credit_balance / b.total_amount))
                     FROM bill_items bi
                     LEFT JOIN products p ON bi.product_id = p.id
                     WHERE bi.bill_id = b.id)
                ), 0) as pending_profit
            FROM bills b
            {date_condition}
            AND b.payment_method IN ('credit', 'partial')
            AND b.credit_balance > 0
        """
        
        result_paid = conn.execute(query_paid, params).fetchone()
        result_pending = conn.execute(query_pending, params).fetchone()
        conn.close()
        
        # Calculate realized profit
        total_revenue = float(result_paid['total_revenue'] or 0)
        total_cost = float(result_paid['total_cost'] or 0)
        total_profit = total_revenue - total_cost
        transaction_count = int(result_paid['transaction_count'] or 0)
        
        # Get pending amounts
        pending_amount = float(result_pending['pending_amount'] or 0)
        pending_profit = float(result_pending['pending_profit'] or 0)
        
        # Calculate profit margin percentage
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Calculate average profit per sale
        avg_profit_per_sale = (total_profit / transaction_count) if transaction_count > 0 else 0
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "transaction_count": transaction_count,
            "avg_profit_per_sale": round(avg_profit_per_sale, 2),
            "gross_profit": round(total_profit, 2),
            "pending_amount": round(pending_amount, 2),
            "pending_profit": round(pending_profit, 2)
        }
    
    def get_product_earnings(self, date_filter=None, user_id=None):
        """
        Get product-wise earnings with profit calculations
        Returns list of products sorted by profit (highest to lowest)
        """
        conn = get_db_connection()
        
        # Build date condition
        where_clauses = []
        params = []
        
        # Add user_id filter
        if user_id:
            where_clauses.append("(s.business_owner_id = ? OR s.business_owner_id IS NULL)")
            params.append(user_id)
        
        if date_filter:
            if date_filter == 'today':
                today = datetime.now().strftime('%Y-%m-%d')
                where_clauses.append("DATE(s.sale_date) = ?")
                params.append(today)
            elif date_filter == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(s.sale_date) = ?")
                params.append(yesterday)
            elif date_filter == 'week':
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(s.sale_date) >= ?")
                params.append(week_ago)
            elif date_filter == 'month':
                month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                where_clauses.append("DATE(s.sale_date) >= ?")
                params.append(month_ago)
            elif date_filter == 'all':
                # All data - no date filter
                pass
        
        # Build WHERE clause
        date_condition = ""
        if where_clauses:
            date_condition = "WHERE " + " AND ".join(where_clauses)
        
        # Get product-wise earnings
        query = f"""
            SELECT 
                p.id as product_id,
                p.name as product_name,
                p.price as product_price,
                p.cost as product_cost,
                SUM(s.quantity) as total_quantity_sold,
                COALESCE(SUM(s.total_price), 0) as total_sales,
                COALESCE(SUM(COALESCE(p.cost, 0) * s.quantity), 0) as total_cost,
                COALESCE(SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)), 0) as total_profit,
                CASE 
                    WHEN SUM(s.total_price) > 0 THEN 
                        (SUM(s.total_price - (COALESCE(p.cost, 0) * s.quantity)) / SUM(s.total_price)) * 100
                    ELSE 0
                END as profit_margin
            FROM sales s
            LEFT JOIN products p ON s.product_id = p.id
            {date_condition}
            GROUP BY p.id, p.name, p.price, p.cost
            HAVING total_quantity_sold > 0
            ORDER BY total_profit DESC
        """
        
        products = conn.execute(query, params).fetchall()
        conn.close()
        
        # Convert to list of dicts with proper formatting
        result = []
        for product in products:
            result.append({
                "product_id": product['product_id'],
                "name": product['product_name'],
                "price": float(product['product_price'] or 0),
                "cost": float(product['product_cost'] or 0),
                "quantity_sold": int(product['total_quantity_sold'] or 0),
                "total_sales": round(float(product['total_sales'] or 0), 2),
                "total_cost": round(float(product['total_cost'] or 0), 2),
                "total_profit": round(float(product['total_profit'] or 0), 2),
                "profit_margin": round(float(product['profit_margin'] or 0), 2),
                "margin_class": self._get_margin_class(float(product['profit_margin'] or 0))
            })
        
        return result
    
    def get_top_profitable_products(self, date_filter=None, limit=5, user_id=None):
        """
        Get most and least profitable products
        """
        products = self.get_product_earnings(date_filter, user_id)
        
        if not products:
            return {
                "most_profitable": [],
                "least_profitable": []
            }
        
        # Get top N most profitable
        most_profitable = products[:limit]
        
        # Get top N least profitable (reverse order)
        least_profitable = products[-limit:][::-1]
        
        return {
            "most_profitable": most_profitable,
            "least_profitable": least_profitable
        }
    
    def _get_margin_class(self, margin):
        """Get CSS class based on profit margin"""
        if margin >= 30:
            return 'margin-high'
        elif margin >= 15:
            return 'margin-medium'
        else:
            return 'margin-low'
