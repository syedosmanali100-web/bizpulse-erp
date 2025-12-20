"""
Production-Grade Invoice Service
Clean invoice management with proper business logic
"""

from datetime import datetime
import sqlite3
import uuid
from typing import Dict, List, Optional, Tuple
from .billing_service import BillingService


class InvoiceService:
    """
    Professional invoice service built on top of billing service
    Invoice is the source of truth for all transactions
    """
    
    def __init__(self, db_path: str = 'billing.db'):
        self.db_path = db_path
        self.billing_service = BillingService(db_path)
    
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
    
    def create_invoice(self, data: Dict) -> Tuple[bool, Dict]:
        """
        Create invoice - this is the main entry point for all transactions
        Invoice creation automatically creates bill, sales, and updates inventory
        Returns: (success, result_data)
        """
        # Use billing service to create the transaction
        success, result = self.billing_service.create_bill(data)
        
        if success:
            # Transform response to invoice format
            return True, {
                "success": True,
                "message": "Invoice created successfully",
                "invoice_id": result["bill_id"],
                "invoice_number": result["bill_number"],
                "total_amount": result["total_amount"],
                "items_count": result["items_count"],
                "created_at": result["created_at"]
            }
        else:
            return False, {
                "success": False,
                "message": result.get("error", "Invoice creation failed")
            }
    
    def get_invoices(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get invoices with filtering options
        Returns: (success, result_data)
        """
        success, result = self.billing_service.get_bills(filters)
        
        if success:
            # Transform bills to invoices format
            invoices = []
            for bill in result["bills"]:
                invoice = dict(bill)
                # Rename fields for invoice context
                invoice["invoice_id"] = invoice["id"]
                invoice["invoice_number"] = invoice["bill_number"]
                invoices.append(invoice)
            
            return True, {
                "success": True,
                "invoices": invoices,
                "total_records": result["total_records"]
            }
        else:
            return False, {
                "success": False,
                "message": result.get("error", "Failed to fetch invoices")
            }
    
    def get_invoice_by_id(self, invoice_id: str) -> Tuple[bool, Dict]:
        """
        Get invoice details by ID
        Returns: (success, result_data)
        """
        success, result = self.billing_service.get_bill_by_id(invoice_id)
        
        if success:
            # Transform bill to invoice format
            invoice = dict(result["bill"])
            invoice["invoice_id"] = invoice["id"]
            invoice["invoice_number"] = invoice["bill_number"]
            
            return True, {
                "success": True,
                "invoice": invoice,
                "items": result["items"],
                "payments": result["payments"]
            }
        else:
            return False, {
                "success": False,
                "message": result.get("error", "Invoice not found")
            }
    
    def delete_invoice(self, invoice_id: str) -> Tuple[bool, Dict]:
        """
        Delete invoice and revert all changes
        This deletes the bill, reverts inventory, and removes sales records
        Returns: (success, result_data)
        """
        success, result = self.billing_service.delete_bill(invoice_id)
        
        if success:
            return True, {
                "success": True,
                "message": result["message"],
                "reverted_items": result["reverted_items"]
            }
        else:
            return False, {
                "success": False,
                "message": result.get("error", "Invoice deletion failed")
            }
    
    def get_invoice_summary(self, filters: Dict = None) -> Tuple[bool, Dict]:
        """
        Get invoice summary statistics
        Returns: (success, result_data)
        """
        conn = self._get_connection()
        
        try:
            # Build date filter
            date_condition = "1=1"
            params = []
            
            if filters:
                if filters.get('date_from'):
                    date_condition += " AND DATE(created_at) >= ?"
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    date_condition += " AND DATE(created_at) <= ?"
                    params.append(filters['date_to'])
            
            # Get summary statistics
            summary = conn.execute(f'''
                SELECT 
                    COUNT(*) as total_invoices,
                    COALESCE(SUM(total_amount), 0) as total_value,
                    COALESCE(AVG(total_amount), 0) as avg_value,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count
                FROM bills
                WHERE {date_condition}
            ''', params).fetchone()
            
            return True, {
                "success": True,
                "summary": dict(summary) if summary else {}
            }
            
        except Exception as e:
            return False, {
                "success": False,
                "message": str(e)
            }
            
        finally:
            conn.close()