"""
Invoice service - Handle all invoice data and analytics
Invoices are the source of truth - they read from bills table
"""

from modules.shared.database import get_db_connection, generate_id
from datetime import datetime, timedelta

class InvoiceService:
    
    def get_invoices(self, filters=None):
        """Get invoices with comprehensive filtering and pagination"""
        conn = get_db_connection()
        
        try:
            # Get query parameters with defaults
            page = filters.get('page', 1) if filters else 1
            limit = filters.get('limit', 50) if filters else 50
            offset = (page - 1) * limit
            
            # Base query - bills are invoices
            base_query = '''
                SELECT b.*, 
                       COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name, 
                       c.phone as customer_phone,
                       c.email as customer_email,
                       DATE(b.created_at) as invoice_date,
                       TIME(b.created_at) as invoice_time,
                       COALESCE(SUM(p.amount), 0) as paid_amount,
                       CASE 
                           WHEN b.payment_status = 'paid' THEN 'paid'
                           WHEN b.payment_status = 'partial' THEN 'partial'
                           WHEN b.payment_status = 'unpaid' THEN 'unpaid'
                           WHEN COALESCE(SUM(p.amount), 0) = 0 THEN 'unpaid'
                           WHEN COALESCE(SUM(p.amount), 0) < b.total_amount THEN 'partial'
                           WHEN COALESCE(SUM(p.amount), 0) >= b.total_amount THEN 'paid'
                           ELSE 'paid'
                       END as payment_status_calc
                FROM bills b
                LEFT JOIN customers c ON b.customer_id = c.id
                LEFT JOIN payments p ON b.id = p.bill_id
            '''
            
            # Build WHERE conditions
            conditions = []
            params = []
            
            if filters:
                # Date filtering
                if filters.get('date_filter') == 'today':
                    today = datetime.now().strftime('%Y-%m-%d')
                    conditions.append("DATE(b.created_at) = ?")
                    params.append(today)
                elif filters.get('date_filter') == 'yesterday':
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    conditions.append("DATE(b.created_at) = ?")
                    params.append(yesterday)
                elif filters.get('date_filter') == 'week':
                    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    conditions.append("DATE(b.created_at) >= ?")
                    params.append(week_ago)
                elif filters.get('date_filter') == 'month':
                    month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    conditions.append("DATE(b.created_at) >= ?")
                    params.append(month_ago)
                elif filters.get('date_filter') == 'custom' and filters.get('custom_date'):
                    conditions.append("DATE(b.created_at) = ?")
                    params.append(filters['custom_date'])
                
                # Date range filtering
                if filters.get('date_from'):
                    conditions.append('DATE(b.created_at) >= ?')
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append('DATE(b.created_at) <= ?')
                    params.append(filters['date_to'])
            
            # Add WHERE clause if conditions exist
            if conditions:
                base_query += ' WHERE ' + ' AND '.join(conditions)
            
            # Group by bill to aggregate payments
            base_query += ' GROUP BY b.id'
            
            # Add payment status filter after GROUP BY
            if filters and filters.get('status') and filters['status'] != 'all':
                status = filters['status']
                base_query += f" HAVING payment_status_calc = '{status}'"
            
            # Order by creation date (newest first)
            base_query += ' ORDER BY b.created_at DESC'
            
            # Get total count for pagination
            count_query = f'SELECT COUNT(*) as total FROM ({base_query})'
            total_count = conn.execute(count_query, params).fetchone()['total']
            
            # Add pagination
            base_query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # Execute main query
            bills = conn.execute(base_query, params).fetchall()
            
            # Format invoices
            invoices = []
            for bill in bills:
                invoice = dict(bill)
                
                # Rename fields for invoice context
                invoice["invoice_id"] = invoice["id"]
                invoice["invoice_number"] = invoice["bill_number"]
                invoice["payment_status"] = invoice.get("payment_status_calc", invoice.get("payment_status", "paid"))
                
                # Format dates
                if invoice.get('invoice_date'):
                    try:
                        date_obj = datetime.strptime(invoice['invoice_date'], '%Y-%m-%d')
                        invoice['formatted_date'] = date_obj.strftime('%d/%m/%Y')
                        invoice['display_date'] = date_obj.strftime('%d %b %Y')
                    except:
                        invoice['formatted_date'] = invoice['invoice_date']
                        invoice['display_date'] = invoice['invoice_date']
                
                # Calculate balance due
                paid_amount = invoice.get('paid_amount', 0) or 0
                total_amount = invoice.get('total_amount', 0) or 0
                invoice['balance_due'] = max(0, total_amount - paid_amount)
                
                # Add status badge color
                status_colors = {
                    'paid': 'success',
                    'partial': 'warning', 
                    'unpaid': 'danger'
                }
                invoice['status_color'] = status_colors.get(invoice['payment_status'], 'success')
                
                invoices.append(invoice)
            
            # Calculate pagination info
            total_pages = max(1, (total_count + limit - 1) // limit)
            
            return {
                "success": True,
                "invoices": invoices,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_records": total_count,
                    "per_page": limit,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "invoices": [],
                "pagination": {"total_records": 0}
            }
            
        finally:
            conn.close()

    
    def get_invoice_by_id(self, invoice_id):
        """Get invoice details by ID"""
        conn = get_db_connection()
        
        try:
            # Get bill details
            bill = conn.execute('''
                SELECT b.*, 
                       COALESCE(b.customer_name, c.name, 'Walk-in Customer') as customer_name, 
                       c.phone as customer_phone, 
                       c.address as customer_address
                FROM bills b
                LEFT JOIN customers c ON b.customer_id = c.id
                WHERE b.id = ?
            ''', (invoice_id,)).fetchone()
            
            if not bill:
                return {"success": False, "error": "Invoice not found"}
            
            # Get bill items
            items = conn.execute('''
                SELECT * FROM bill_items WHERE bill_id = ?
            ''', (invoice_id,)).fetchall()
            
            # Get payments
            payments = conn.execute('''
                SELECT * FROM payments WHERE bill_id = ?
            ''', (invoice_id,)).fetchall()
            
            invoice = dict(bill)
            invoice["invoice_id"] = invoice["id"]
            invoice["invoice_number"] = invoice["bill_number"]
            
            return {
                "success": True,
                "invoice": invoice,
                "items": [dict(row) for row in items],
                "payments": [dict(row) for row in payments]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
        finally:
            conn.close()
    
    def create_invoice(self, data):
        """Create invoice - delegates to billing service"""
        from modules.billing.service import BillingService
        billing_service = BillingService()
        return billing_service.create_bill(data)
    
    def delete_invoice(self, invoice_id):
        """Delete invoice and revert all changes"""
        conn = get_db_connection()
        
        try:
            # Check if bill exists
            bill = conn.execute('SELECT * FROM bills WHERE id = ?', (invoice_id,)).fetchone()
            if not bill:
                return {"success": False, "error": "Invoice not found"}
            
            # Get all bill items to revert stock
            bill_items = conn.execute('''
                SELECT product_id, quantity FROM bill_items WHERE bill_id = ?
            ''', (invoice_id,)).fetchall()
            
            # Revert stock for each item
            for item in bill_items:
                conn.execute('''
                    UPDATE products SET stock = stock + ? WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            # Delete related records in correct order
            conn.execute('DELETE FROM payments WHERE bill_id = ?', (invoice_id,))
            conn.execute('DELETE FROM sales WHERE bill_id = ?', (invoice_id,))
            conn.execute('DELETE FROM bill_items WHERE bill_id = ?', (invoice_id,))
            conn.execute('DELETE FROM bills WHERE id = ?', (invoice_id,))
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Invoice {bill['bill_number']} deleted successfully",
                "reverted_items": len(bill_items)
            }
            
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": f"Delete failed: {str(e)}"}
            
        finally:
            conn.close()
    
    def get_invoice_summary(self, filters=None):
        """Get invoice summary statistics"""
        conn = get_db_connection()
        
        try:
            # Build date filter
            conditions = []
            params = []
            
            if filters:
                if filters.get('date_from'):
                    conditions.append("DATE(created_at) >= ?")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    conditions.append("DATE(created_at) <= ?")
                    params.append(filters['date_to'])
            
            where_clause = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
            
            # Get summary statistics
            summary = conn.execute(f'''
                SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_value,
                    COALESCE(AVG(total_amount), 0) as avg_value,
                    COUNT(CASE WHEN payment_status = 'paid' OR status = 'completed' THEN 1 END) as paid_count,
                    COUNT(CASE WHEN payment_status = 'partial' THEN 1 END) as partial_count,
                    COUNT(CASE WHEN payment_status = 'unpaid' THEN 1 END) as unpaid_count
                FROM bills
                {where_clause}
            ''', params).fetchone()
            
            return {
                "success": True,
                "summary": dict(summary) if summary else {
                    "total_invoices": 0,
                    "total_value": 0,
                    "avg_value": 0,
                    "paid_count": 0,
                    "partial_count": 0,
                    "unpaid_count": 0
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "summary": {}}
            
        finally:
            conn.close()
    
    def check_database_health(self):
        """Check if invoice data is being stored properly"""
        conn = get_db_connection()
        
        try:
            # Check total bills count
            total_bills = conn.execute("SELECT COUNT(*) as count FROM bills").fetchone()
            
            # Check recent bills (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            recent_bills = conn.execute("""
                SELECT COUNT(*) as count FROM bills 
                WHERE created_at >= ?
            """, (yesterday,)).fetchone()
            
            # Check total sales
            total_sales = conn.execute("SELECT COUNT(*) as count FROM sales").fetchone()
            
            return {
                "total_invoices": total_bills['count'] if total_bills else 0,
                "recent_invoices_24h": recent_bills['count'] if recent_bills else 0,
                "total_sales_records": total_sales['count'] if total_sales else 0,
                "database_status": "healthy" if total_bills and total_bills['count'] >= 0 else "no_data"
            }
            
        finally:
            conn.close()
