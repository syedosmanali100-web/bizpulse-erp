"""
Super Admin Service
Manage clients, subscriptions, and system-wide operations
"""

from modules.shared.database import get_db_connection, generate_id, hash_password
from datetime import datetime, timedelta
import json
import secrets
import hashlib


def encrypt_data(data):
    """Simple encryption using base64 (for demo - use Fernet in production)"""
    if not data:
        return None
    import base64
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


def decrypt_data(encrypted_data):
    """Simple decryption using base64 (for demo - use Fernet in production)"""
    if not encrypted_data:
        return None
    try:
        import base64
        return base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
    except Exception:
        return None


def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash


def generate_temp_password(length=12):
    """Generate secure temporary password"""
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_tenant_id():
    """Generate unique tenant ID"""
    return f"TNT-{secrets.token_hex(8).upper()}"


def generate_username(business_name):
    """Generate username from business name"""
    clean_name = ''.join(c for c in business_name if c.isalnum() or c.isspace())
    words = clean_name.lower().split()[:3]
    base_username = '_'.join(words)
    suffix = secrets.token_hex(3)
    return f"{base_username}_{suffix}"


def log_audit(tenant_id, user_id, user_type, action, module, resource_type, resource_id, old_value, new_value, status, error_message):
    """Simple audit logging"""
    pass  # Skip for now


class SuperAdminService:
    """Service for Super Admin operations"""
    
    def __init__(self):
        pass  # Don't store connection as instance variable
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    def login(self, username: str, password: str, ip_address: str, user_agent: str) -> dict:
        """Super Admin login"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get super admin
        cursor.execute('''
            SELECT id, username, email, password_hash, full_name, is_active
            FROM super_admins
            WHERE username = ? OR email = ?
        ''', (username, username))
        
        admin = cursor.fetchone()
        
        if not admin:
            return {'success': False, 'message': 'Invalid credentials'}
        
        admin_id, admin_username, email, password_hash, full_name, is_active = admin
        
        # Check if active
        if not is_active:
            return {'success': False, 'message': 'Account is inactive'}
        
        # Verify password
        if not verify_password(password, password_hash):
            return {'success': False, 'message': 'Invalid credentials'}
        
        # Update last login
        cursor.execute('''
            UPDATE super_admins
            SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
            WHERE id = ?
        ''', (admin_id,))
        
        conn.commit()
        
        return {
            'success': True,
            'access_token': 'dummy_token',
            'refresh_token': 'dummy_token',
            'user': {
                'id': admin_id,
                'username': admin_username,
                'email': email,
                'full_name': full_name,
                'user_type': 'super_admin'
            }
        }
    
    # ========================================================================
    # CLIENT (TENANT) MANAGEMENT
    # ========================================================================
    
    def create_client(self, data: dict, created_by: str) -> dict:
        """Create new client/tenant"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate credentials
            tenant_id = generate_tenant_id()
            username = data.get('username') or generate_username(data['business_name'])
            temp_password = generate_temp_password()
            password_hash = hash_password(temp_password)
            
            # Encrypt sensitive data
            mobile_encrypted = encrypt_data(data['mobile'])
            email_encrypted = encrypt_data(data['email'])
            
            # Calculate plan expiry
            plan_type = data.get('plan_type', 'trial')
            plan_duration = data.get('plan_duration', 30)  # days
            plan_start_date = datetime.now().date()
            plan_expiry_date = plan_start_date + timedelta(days=plan_duration)
            
            # Insert tenant
            client_id = generate_id()
            cursor.execute('''
                INSERT INTO tenants (
                    id, tenant_id, business_name, owner_name, mobile_encrypted, email_encrypted,
                    gst_number, address, city, state, pincode, country,
                    username, password_hash, temp_password,
                    plan_type, plan_start_date, plan_expiry_date, subscription_status,
                    status, is_active, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                client_id, tenant_id, data['business_name'], data['owner_name'],
                mobile_encrypted, email_encrypted, data.get('gst_number'),
                data.get('address'), data.get('city'), data.get('state'),
                data.get('pincode'), data.get('country', 'India'),
                username, password_hash, temp_password,
                plan_type, plan_start_date, plan_expiry_date, 'active',
                'active', 1, created_by
            ))
            
            # Record subscription history
            cursor.execute('''
                INSERT INTO subscription_history (
                    id, tenant_id, plan_type, plan_duration, start_date, expiry_date,
                    status, changed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                generate_id(), tenant_id, plan_type, f"{plan_duration} days",
                plan_start_date, plan_expiry_date, 'active', created_by
            ))
            
            conn.commit()
            
            # Log audit
            log_audit(tenant_id, created_by, 'super_admin', 'create_client', 'clients', 'tenant', client_id, None, json.dumps(data), 'success', None)
            
            return {
                'success': True,
                'client_id': client_id,
                'tenant_id': tenant_id,
                'username': username,
                'temp_password': temp_password,
                'plan_expiry_date': plan_expiry_date.isoformat()
            }
        
        except Exception as e:
            conn.rollback()
            log_audit(None, created_by, 'super_admin', 'create_client', 'clients', None, None, None, None, 'failed', str(e))
            return {'success': False, 'message': str(e)}
    
    def get_all_clients(self, filters: dict = None) -> dict:
        """Get all clients with filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, tenant_id, business_name, owner_name, mobile_encrypted, email_encrypted,
                   gst_number, address, city, state, pincode, country,
                   username, plan_type, plan_start_date, plan_expiry_date, subscription_status,
                   status, is_active, last_login, login_count, created_at
            FROM tenants
            WHERE 1=1
        '''
        params = []
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query += ' AND status = ?'
                params.append(filters['status'])
            
            if filters.get('plan_type'):
                query += ' AND plan_type = ?'
                params.append(filters['plan_type'])
            
            if filters.get('search'):
                query += ' AND (business_name LIKE ? OR owner_name LIKE ? OR username LIKE ?)'
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        clients = cursor.fetchall()
        
        result = []
        for client in clients:
            result.append({
                'id': client[0],
                'tenant_id': client[1],
                'business_name': client[2],
                'owner_name': client[3],
                'mobile': decrypt_data(client[4]),
                'email': decrypt_data(client[5]),
                'gst_number': client[6],
                'address': client[7],
                'city': client[8],
                'state': client[9],
                'pincode': client[10],
                'country': client[11],
                'username': client[12],
                'plan_type': client[13],
                'plan_start_date': client[14],
                'plan_expiry_date': client[15],
                'subscription_status': client[16],
                'status': client[17],
                'is_active': client[18],
                'last_login': client[19],
                'login_count': client[20],
                'created_at': client[21]
            })
        
        conn.close()
        return {'success': True, 'clients': result, 'total': len(result)}
    
    def get_client_details(self, client_id: str) -> dict:
        """Get detailed client information"""
        try:
            # Use fresh connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            print(f"[SERVICE DEBUG] Looking for client: {client_id}")
            
            cursor.execute('''
                SELECT id, tenant_id, business_name, owner_name, mobile_encrypted, email_encrypted,
                       gst_number, address, city, state, pincode, country,
                       username, temp_password, plan_type, plan_start_date, plan_expiry_date,
                       subscription_status, status, is_active, last_login, login_count, created_at
                FROM tenants WHERE id = ? OR tenant_id = ?
            ''', (client_id, client_id))
            
            client = cursor.fetchone()
            conn.close()
            
            if not client:
                print(f"[SERVICE DEBUG] Client not found: {client_id}")
                return {'success': False, 'message': 'Client not found'}
            
            print(f"[SERVICE DEBUG] Client found: {client[2]}")
            
            # Convert to dict
            client_dict = {
                'id': client[0],
                'tenant_id': client[1],
                'business_name': client[2],
                'owner_name': client[3],
                'mobile': decrypt_data(client[4]),
                'email': decrypt_data(client[5]),
                'gst_number': client[6],
                'address': client[7],
                'city': client[8],
                'state': client[9],
                'pincode': client[10],
                'country': client[11],
                'username': client[12],
                'temp_password': client[13],
                'plan_type': client[14],
                'plan_start_date': client[15],
                'plan_expiry_date': client[16],
                'subscription_status': client[17],
                'status': client[18],
                'is_active': client[19],
                'last_login': client[20],
                'login_count': client[21],
                'created_at': client[22]
            }
            
            print(f"[SERVICE DEBUG] Returning client dict with {len(client_dict)} fields")
            
            return {
                'success': True,
                'client': client_dict
            }
        except Exception as e:
            print(f"[SERVICE DEBUG] Exception in get_client_details: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    def update_client(self, client_id: str, data: dict, updated_by: str) -> dict:
        """Update client information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Build update query dynamically
            update_fields = []
            params = []
            
            if 'business_name' in data:
                update_fields.append('business_name = ?')
                params.append(data['business_name'])
            
            if 'owner_name' in data:
                update_fields.append('owner_name = ?')
                params.append(data['owner_name'])
            
            if 'mobile' in data:
                update_fields.append('mobile_encrypted = ?')
                params.append(encrypt_data(data['mobile']))
            
            if 'email' in data:
                update_fields.append('email_encrypted = ?')
                params.append(encrypt_data(data['email']))
            
            if 'gst_number' in data:
                update_fields.append('gst_number = ?')
                params.append(data['gst_number'])
            
            if 'address' in data:
                update_fields.append('address = ?')
                params.append(data['address'])
            
            if 'city' in data:
                update_fields.append('city = ?')
                params.append(data['city'])
            
            if 'state' in data:
                update_fields.append('state = ?')
                params.append(data['state'])
            
            if 'pincode' in data:
                update_fields.append('pincode = ?')
                params.append(data['pincode'])
            
            update_fields.append('updated_at = CURRENT_TIMESTAMP')
            params.append(client_id)
            
            query = f"UPDATE tenants SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            
            log_audit(None, updated_by, 'super_admin', 'update_client', 'clients', 'tenant', client_id, None, json.dumps(data), 'success', None)
            
            return {'success': True, 'message': 'Client updated successfully'}
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
    
    def reset_client_password(self, client_id: str, reset_by: str) -> dict:
        """Reset client password"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Generate new temp password
            temp_password = generate_temp_password()
            password_hash = hash_password(temp_password)
            
            cursor.execute('''
                UPDATE tenants
                SET password_hash = ?, temp_password = ?, failed_login_attempts = 0, account_locked_until = NULL
                WHERE id = ?
            ''', (password_hash, temp_password, client_id))
            
            conn.commit()
            
            log_audit(None, reset_by, 'super_admin', 'reset_password', 'clients', 'tenant', client_id, None, None, 'success', None)
            
            return {'success': True, 'temp_password': temp_password}
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
    
    def toggle_client_status(self, client_id: str, action: str, reason: str, changed_by: str) -> dict:
        """Activate/Suspend/Expire client"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if action == 'suspend':
                cursor.execute('''
                    UPDATE tenants
                    SET status = 'suspended', is_active = 0, suspended_reason = ?, suspended_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (reason, client_id))
            
            elif action == 'activate':
                cursor.execute('''
                    UPDATE tenants
                    SET status = 'active', is_active = 1, suspended_reason = NULL, suspended_at = NULL
                    WHERE id = ?
                ''', (client_id,))
            
            elif action == 'expire':
                cursor.execute('''
                    UPDATE tenants
                    SET status = 'expired', subscription_status = 'expired'
                    WHERE id = ?
                ''', (client_id,))
            
            conn.commit()
            
            log_audit(None, changed_by, 'super_admin', f'{action}_client', 'clients', 'tenant', client_id, None, reason, 'success', None)
            
            return {'success': True, 'message': f'Client {action}d successfully'}
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
    
    def force_logout_client(self, client_id: str, logged_out_by: str) -> dict:
        """Force logout all client sessions"""
        try:
            log_audit(None, logged_out_by, 'super_admin', 'force_logout', 'clients', 'tenant', client_id, None, None, 'success', None)
            return {'success': True, 'message': 'All sessions terminated'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_subscription(self, client_id: str, plan_type: str, duration_days: int, amount: float, changed_by: str) -> dict:
        """Update client subscription"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get current tenant_id
            cursor.execute('SELECT tenant_id, plan_expiry_date FROM tenants WHERE id = ?', (client_id,))
            result = cursor.fetchone()
            if not result:
                return {'success': False, 'message': 'Client not found'}
            
            tenant_id, current_expiry = result
            
            # Calculate new dates
            start_date = datetime.now().date()
            expiry_date = start_date + timedelta(days=duration_days)
            
            # Update tenant
            cursor.execute('''
                UPDATE tenants
                SET plan_type = ?, plan_start_date = ?, plan_expiry_date = ?, 
                    subscription_status = 'active', status = 'active'
                WHERE id = ?
            ''', (plan_type, start_date, expiry_date, client_id))
            
            # Record in subscription history
            cursor.execute('''
                INSERT INTO subscription_history (
                    id, tenant_id, plan_type, plan_duration, amount, start_date, expiry_date,
                    status, changed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                generate_id(), tenant_id, plan_type, f"{duration_days} days", amount,
                start_date, expiry_date, 'active', changed_by
            ))
            
            conn.commit()
            
            log_audit(tenant_id, changed_by, 'super_admin', 'update_subscription', 'subscriptions', 'tenant', client_id, current_expiry, expiry_date.isoformat(), 'success', None)
            
            return {'success': True, 'expiry_date': expiry_date.isoformat()}
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': str(e)}
