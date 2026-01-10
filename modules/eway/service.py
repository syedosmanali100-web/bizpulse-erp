"""
E-Way Bill Service
Handles E-Way Bill generation for invoices above required value
"""

import sqlite3
from datetime import datetime, timedelta
from modules.shared.database import get_db_connection, generate_id
import logging
import json

logger = logging.getLogger(__name__)

class EWayBillService:
    
    def __init__(self):
        self.eway_threshold = 50000  # E-Way Bill required for invoices above ₹50,000
        self.init_eway_tables()
    
    def init_eway_tables(self):
        """Initialize E-Way Bill related tables"""
        conn = get_db_connection()
        try:
            # E-Way Bills table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS eway_bills (
                    id TEXT PRIMARY KEY,
                    invoice_id TEXT NOT NULL,
                    bill_id TEXT,
                    eway_bill_number TEXT UNIQUE,
                    invoice_value REAL NOT NULL,
                    transport_mode TEXT NOT NULL,
                    vehicle_number TEXT,
                    transporter_name TEXT,
                    transporter_id TEXT,
                    distance INTEGER,
                    from_place TEXT NOT NULL,
                    to_place TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    from_pincode TEXT NOT NULL,
                    to_pincode TEXT NOT NULL,
                    supply_type TEXT NOT NULL,
                    sub_supply_type TEXT,
                    document_type TEXT NOT NULL,
                    document_number TEXT NOT NULL,
                    document_date TEXT NOT NULL,
                    hsn_code TEXT,
                    product_description TEXT,
                    quantity REAL,
                    unit TEXT,
                    cgst_rate REAL DEFAULT 0,
                    sgst_rate REAL DEFAULT 0,
                    igst_rate REAL DEFAULT 0,
                    cess_rate REAL DEFAULT 0,
                    cgst_amount REAL DEFAULT 0,
                    sgst_amount REAL DEFAULT 0,
                    igst_amount REAL DEFAULT 0,
                    cess_amount REAL DEFAULT 0,
                    total_tax_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'generated',
                    valid_until TEXT,
                    generated_by TEXT,
                    generated_at TEXT NOT NULL,
                    updated_at TEXT,
                    business_owner_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                    FOREIGN KEY (bill_id) REFERENCES bills (id)
                )
            ''')
            
            # E-Way Bill Transport Details table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS eway_transport_details (
                    id TEXT PRIMARY KEY,
                    eway_bill_id TEXT NOT NULL,
                    transport_mode TEXT NOT NULL,
                    vehicle_type TEXT,
                    vehicle_number TEXT,
                    driver_name TEXT,
                    driver_license TEXT,
                    transporter_name TEXT,
                    transporter_gstin TEXT,
                    lr_number TEXT,
                    lr_date TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (eway_bill_id) REFERENCES eway_bills (id)
                )
            ''')
            
            # E-Way Bill Settings table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS eway_settings (
                    id TEXT PRIMARY KEY,
                    business_owner_id TEXT NOT NULL,
                    gstin TEXT,
                    business_name TEXT,
                    business_address TEXT,
                    state_code TEXT,
                    pincode TEXT,
                    auto_generate BOOLEAN DEFAULT 0,
                    threshold_amount REAL DEFAULT 50000,
                    default_transport_mode TEXT DEFAULT 'Road',
                    api_username TEXT,
                    api_password TEXT,
                    api_endpoint TEXT,
                    is_production BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            logger.info("✅ E-Way Bill tables initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize E-Way Bill tables: {e}")
        finally:
            conn.close()
    
    def check_eway_requirement(self, invoice_value: float, from_state: str, to_state: str) -> bool:
        """Check if E-Way Bill is required for this invoice"""
        # E-Way Bill required for:
        # 1. Inter-state supply of goods above ₹50,000
        # 2. Intra-state supply of goods above ₹50,000 (in some states)
        
        if invoice_value >= self.eway_threshold:
            return True
        
        # Additional checks can be added based on state-specific rules
        return False
    
    def generate_eway_bill_number(self) -> str:
        """Generate unique E-Way Bill number"""
        # Format: EWB + timestamp + random digits
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        import random
        random_digits = str(random.randint(1000, 9999))
        return f"EWB{timestamp}{random_digits}"
    
    def create_eway_bill(self, data: dict) -> tuple:
        """Create E-Way Bill for invoice"""
        try:
            conn = get_db_connection()
            
            # Validate required fields
            required_fields = [
                'invoice_id', 'invoice_value', 'transport_mode',
                'from_place', 'to_place', 'from_state', 'to_state',
                'from_pincode', 'to_pincode', 'supply_type', 'document_type',
                'document_number', 'document_date'
            ]
            
            for field in required_fields:
                if not data.get(field):
                    return False, f"Missing required field: {field}"
            
            # Check if E-Way Bill already exists for this invoice
            existing = conn.execute(
                "SELECT id FROM eway_bills WHERE invoice_id = ? AND is_active = 1",
                (data['invoice_id'],)
            ).fetchone()
            
            if existing:
                conn.close()
                return False, "E-Way Bill already exists for this invoice"
            
            # Generate E-Way Bill
            eway_id = generate_id()
            eway_number = self.generate_eway_bill_number()
            
            # Calculate validity (72 hours for distances up to 1000 km)
            distance = data.get('distance', 0)
            validity_hours = 72 if distance <= 1000 else 72 + ((distance - 1000) // 300) * 24
            valid_until = (datetime.now() + timedelta(hours=validity_hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert E-Way Bill
            conn.execute('''
                INSERT INTO eway_bills (
                    id, invoice_id, bill_id, eway_bill_number, invoice_value,
                    transport_mode, vehicle_number, transporter_name, transporter_id,
                    distance, from_place, to_place, from_state, to_state,
                    from_pincode, to_pincode, supply_type, sub_supply_type,
                    document_type, document_number, document_date,
                    hsn_code, product_description, quantity, unit,
                    cgst_rate, sgst_rate, igst_rate, cess_rate,
                    cgst_amount, sgst_amount, igst_amount, cess_amount,
                    total_tax_amount, status, valid_until, generated_by,
                    generated_at, business_owner_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                eway_id, data['invoice_id'], data.get('bill_id'),
                eway_number, data['invoice_value'],
                data['transport_mode'], data.get('vehicle_number'),
                data.get('transporter_name'), data.get('transporter_id'),
                data.get('distance', 0), data['from_place'], data['to_place'],
                data['from_state'], data['to_state'], data['from_pincode'], data['to_pincode'],
                data['supply_type'], data.get('sub_supply_type'),
                data['document_type'], data['document_number'], data['document_date'],
                data.get('hsn_code'), data.get('product_description'),
                data.get('quantity', 0), data.get('unit', 'NOS'),
                data.get('cgst_rate', 0), data.get('sgst_rate', 0),
                data.get('igst_rate', 0), data.get('cess_rate', 0),
                data.get('cgst_amount', 0), data.get('sgst_amount', 0),
                data.get('igst_amount', 0), data.get('cess_amount', 0),
                data.get('total_tax_amount', 0), 'generated', valid_until,
                data.get('generated_by'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('business_owner_id')
            ))
            
            # Insert transport details if provided
            if data.get('transport_details'):
                transport_id = generate_id()
                transport_data = data['transport_details']
                
                conn.execute('''
                    INSERT INTO eway_transport_details (
                        id, eway_bill_id, transport_mode, vehicle_type,
                        vehicle_number, driver_name, driver_license,
                        transporter_name, transporter_gstin, lr_number,
                        lr_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transport_id, eway_id, data['transport_mode'],
                    transport_data.get('vehicle_type'),
                    transport_data.get('vehicle_number'),
                    transport_data.get('driver_name'),
                    transport_data.get('driver_license'),
                    transport_data.get('transporter_name'),
                    transport_data.get('transporter_gstin'),
                    transport_data.get('lr_number'),
                    transport_data.get('lr_date'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            
            # Broadcast E-Way Bill creation for real-time sync
            try:
                from modules.sync.utils import broadcast_data_change
                eway_data = {
                    'id': eway_id,
                    'eway_bill_number': eway_number,
                    'invoice_id': data['invoice_id'],
                    'invoice_value': data['invoice_value'],
                    'status': 'generated',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                broadcast_data_change('create', 'eway_bills', eway_data, data.get('business_owner_id'))
            except Exception as sync_error:
                logger.warning(f"⚠️ [SYNC] Failed to broadcast E-Way Bill creation: {sync_error}")
            
            return True, {
                'eway_bill_id': eway_id,
                'eway_bill_number': eway_number,
                'valid_until': valid_until,
                'status': 'generated'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create E-Way Bill: {e}")
            return False, str(e)
    
    def get_eway_bills(self, business_owner_id: str = None, filters: dict = None) -> list:
        """Get E-Way Bills with optional filters"""
        try:
            conn = get_db_connection()
            
            query = '''
                SELECT e.*, i.bill_number as invoice_number, i.customer_name
                FROM eway_bills e
                LEFT JOIN invoices i ON e.invoice_id = i.id
                WHERE e.is_active = 1
            '''
            params = []
            
            if business_owner_id:
                query += ' AND e.business_owner_id = ?'
                params.append(business_owner_id)
            
            if filters:
                if filters.get('status'):
                    query += ' AND e.status = ?'
                    params.append(filters['status'])
                
                if filters.get('from_date'):
                    query += ' AND DATE(e.generated_at) >= ?'
                    params.append(filters['from_date'])
                
                if filters.get('to_date'):
                    query += ' AND DATE(e.generated_at) <= ?'
                    params.append(filters['to_date'])
            
            query += ' ORDER BY e.generated_at DESC'
            
            eway_bills = conn.execute(query, params).fetchall()
            conn.close()
            
            return [dict(row) for row in eway_bills]
            
        except Exception as e:
            logger.error(f"❌ Failed to get E-Way Bills: {e}")
            return []
    
    def get_eway_bill_by_id(self, eway_bill_id: str) -> dict:
        """Get E-Way Bill by ID with transport details"""
        try:
            conn = get_db_connection()
            
            # Get E-Way Bill
            eway_bill = conn.execute(
                '''SELECT e.*, i.bill_number as invoice_number, i.customer_name
                   FROM eway_bills e
                   LEFT JOIN invoices i ON e.invoice_id = i.id
                   WHERE e.id = ? AND e.is_active = 1''',
                (eway_bill_id,)
            ).fetchone()
            
            if not eway_bill:
                conn.close()
                return {}
            
            eway_data = dict(eway_bill)
            
            # Get transport details
            transport_details = conn.execute(
                'SELECT * FROM eway_transport_details WHERE eway_bill_id = ?',
                (eway_bill_id,)
            ).fetchall()
            
            eway_data['transport_details'] = [dict(row) for row in transport_details]
            
            conn.close()
            return eway_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get E-Way Bill: {e}")
            return {}
    
    def cancel_eway_bill(self, eway_bill_id: str, reason: str, user_id: str) -> tuple:
        """Cancel E-Way Bill"""
        try:
            conn = get_db_connection()
            
            # Check if E-Way Bill exists and is active
            eway_bill = conn.execute(
                'SELECT * FROM eway_bills WHERE id = ? AND is_active = 1',
                (eway_bill_id,)
            ).fetchone()
            
            if not eway_bill:
                conn.close()
                return False, "E-Way Bill not found"
            
            if eway_bill['status'] == 'cancelled':
                conn.close()
                return False, "E-Way Bill already cancelled"
            
            # Update status to cancelled
            conn.execute('''
                UPDATE eway_bills 
                SET status = 'cancelled', updated_at = ?
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), eway_bill_id))
            
            conn.commit()
            conn.close()
            
            # Broadcast cancellation for real-time sync
            try:
                from modules.sync.utils import broadcast_data_change
                cancel_data = {
                    'id': eway_bill_id,
                    'status': 'cancelled',
                    'cancelled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'cancelled_by': user_id,
                    'reason': reason
                }
                broadcast_data_change('update', 'eway_bills', cancel_data, eway_bill['business_owner_id'])
            except Exception as sync_error:
                logger.warning(f"⚠️ [SYNC] Failed to broadcast E-Way Bill cancellation: {sync_error}")
            
            return True, "E-Way Bill cancelled successfully"
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel E-Way Bill: {e}")
            return False, str(e)
    
    def get_eway_settings(self, business_owner_id: str) -> dict:
        """Get E-Way Bill settings for business"""
        try:
            conn = get_db_connection()
            
            settings = conn.execute(
                'SELECT * FROM eway_settings WHERE business_owner_id = ?',
                (business_owner_id,)
            ).fetchone()
            
            conn.close()
            
            if settings:
                return dict(settings)
            else:
                # Return default settings
                return {
                    'threshold_amount': 50000,
                    'auto_generate': False,
                    'default_transport_mode': 'Road',
                    'is_production': False
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get E-Way Bill settings: {e}")
            return {}
    
    def update_eway_settings(self, business_owner_id: str, settings: dict) -> tuple:
        """Update E-Way Bill settings"""
        try:
            conn = get_db_connection()
            
            # Check if settings exist
            existing = conn.execute(
                'SELECT id FROM eway_settings WHERE business_owner_id = ?',
                (business_owner_id,)
            ).fetchone()
            
            if existing:
                # Update existing settings
                conn.execute('''
                    UPDATE eway_settings SET
                        gstin = ?, business_name = ?, business_address = ?,
                        state_code = ?, pincode = ?, auto_generate = ?,
                        threshold_amount = ?, default_transport_mode = ?,
                        api_username = ?, api_password = ?, api_endpoint = ?,
                        is_production = ?, updated_at = ?
                    WHERE business_owner_id = ?
                ''', (
                    settings.get('gstin'), settings.get('business_name'),
                    settings.get('business_address'), settings.get('state_code'),
                    settings.get('pincode'), settings.get('auto_generate', False),
                    settings.get('threshold_amount', 50000),
                    settings.get('default_transport_mode', 'Road'),
                    settings.get('api_username'), settings.get('api_password'),
                    settings.get('api_endpoint'), settings.get('is_production', False),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    business_owner_id
                ))
            else:
                # Create new settings
                settings_id = generate_id()
                conn.execute('''
                    INSERT INTO eway_settings (
                        id, business_owner_id, gstin, business_name, business_address,
                        state_code, pincode, auto_generate, threshold_amount,
                        default_transport_mode, api_username, api_password,
                        api_endpoint, is_production, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    settings_id, business_owner_id, settings.get('gstin'),
                    settings.get('business_name'), settings.get('business_address'),
                    settings.get('state_code'), settings.get('pincode'),
                    settings.get('auto_generate', False),
                    settings.get('threshold_amount', 50000),
                    settings.get('default_transport_mode', 'Road'),
                    settings.get('api_username'), settings.get('api_password'),
                    settings.get('api_endpoint'), settings.get('is_production', False),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            conn.commit()
            conn.close()
            
            return True, "E-Way Bill settings updated successfully"
            
        except Exception as e:
            logger.error(f"❌ Failed to update E-Way Bill settings: {e}")
            return False, str(e)

# Global service instance
eway_service = EWayBillService()