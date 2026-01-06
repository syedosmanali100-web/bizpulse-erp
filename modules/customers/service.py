"""
Customers service
"""

import sqlite3
from datetime import datetime
from modules.shared.database import get_db_connection, generate_id

class CustomersService:
    
    def get_all_customers(self, user_id=None):
        """Get all active customers filtered by user_id"""
        conn = get_db_connection()
        
        if user_id:
            # Filter by user_id for multi-tenant support
            customers = conn.execute('''
                SELECT * FROM customers 
                WHERE is_active = 1 AND (user_id = ? OR user_id IS NULL)
                ORDER BY created_at DESC
            ''', (user_id,)).fetchall()
        else:
            # Fallback to all customers if no user_id provided
            customers = conn.execute('''
                SELECT * FROM customers 
                WHERE is_active = 1 
                ORDER BY created_at DESC
            ''').fetchall()
        
        conn.close()
        
        return {
            "success": True,
            "customers": [dict(row) for row in customers],
            "count": len(customers)
        }
    
    def add_customer(self, data):
        """Add a new customer with user_id for multi-tenant support"""
        print(f"[CUSTOMER ADD] Received data: {data}")
        
        # Extract user_id from data
        user_id = data.get('user_id')
        print(f"[CUSTOMER ADD] user_id: {user_id}")
        
        # Validate required fields
        if not data or not data.get('name'):
            return {
                "success": False,
                "error": "Customer name is required"
            }
        
        conn = get_db_connection()
        
        # Check if customer with same name and phone already exists for this user
        name = data['name'].strip()
        phone = data.get('phone', '').strip()
        
        if phone and user_id:
            existing_customer = conn.execute('''
                SELECT id, name FROM customers 
                WHERE name = ? AND phone = ? AND is_active = 1 AND (user_id = ? OR user_id IS NULL)
            ''', (name, phone, user_id)).fetchone()
            
            if existing_customer:
                conn.close()
                return {
                    "success": False,
                    "error": f"Customer '{name}' with phone '{phone}' already exists",
                    "existing_customer": {
                        "id": existing_customer['id'],
                        "name": existing_customer['name']
                    }
                }
        elif phone:
            existing_customer = conn.execute('''
                SELECT id, name FROM customers 
                WHERE name = ? AND phone = ? AND is_active = 1
            ''', (name, phone)).fetchone()
            
            if existing_customer:
                conn.close()
                return {
                    "success": False,
                    "error": f"Customer '{name}' with phone '{phone}' already exists",
                    "existing_customer": {
                        "id": existing_customer['id'],
                        "name": existing_customer['name']
                    }
                }
        
        # Generate customer ID
        customer_id = generate_id()
        
        # Insert customer with user_id
        try:
            conn.execute('''
                INSERT INTO customers (
                    id, name, phone, email, address, credit_limit, 
                    customer_type, is_active, user_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id,
                name,
                phone,
                data.get('email', '').strip(),
                data.get('address', '').strip(),
                float(data.get('credit_limit', 0)),
                data.get('customer_type', 'regular'),
                1,  # is_active
                user_id,  # 🔥 Store user_id for multi-tenant support
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            conn.commit()
            print(f"[CUSTOMER ADD] Successfully added customer: {customer_id} for user: {user_id}")
            
        except sqlite3.IntegrityError as e:
            conn.close()
            return {
                "success": False,
                "error": f"Database constraint error: {str(e)}"
            }
        
        conn.close()
        
        # 🔥 LOG REAL-TIME ACTIVITY - New customer registered
        try:
            from modules.dashboard.models import log_customer_activity
            log_customer_activity(
                customer_id=customer_id,
                customer_name=name,
                action='registered',
                phone=phone
            )
            print(f"✅ [DASHBOARD] Activity logged: Customer registered - {name}")
        except Exception as e:
            print(f"⚠️ [DASHBOARD] Failed to log customer activity: {e}")
        
        return {
            "success": True,
            "message": "Customer added successfully",
            "customer": {
                "id": customer_id,
                "name": name,
                "phone": phone,
                "email": data.get('email', ''),
                "address": data.get('address', '')
            }
        }
    
    def update_customer(self, customer_id, data):
        """Update an existing customer"""
        print(f"[CUSTOMER UPDATE] Updating customer {customer_id} with data: {data}")
        
        # Validate required fields
        if not data or not data.get('name'):
            return {
                "success": False,
                "error": "Customer name is required"
            }
        
        conn = get_db_connection()
        
        # Check if customer exists
        existing_customer = conn.execute('''
            SELECT * FROM customers WHERE id = ? AND is_active = 1
        ''', (customer_id,)).fetchone()
        
        if not existing_customer:
            conn.close()
            return {
                "success": False,
                "error": "Customer not found"
            }
        
        # Check if another customer with same name and phone exists (excluding current customer)
        name = data['name'].strip()
        phone = data.get('phone', '').strip()
        
        if phone:
            duplicate_customer = conn.execute('''
                SELECT id, name FROM customers 
                WHERE name = ? AND phone = ? AND is_active = 1 AND id != ?
            ''', (name, phone, customer_id)).fetchone()
            
            if duplicate_customer:
                conn.close()
                return {
                    "success": False,
                    "error": f"Another customer '{name}' with phone '{phone}' already exists",
                    "existing_customer": {
                        "id": duplicate_customer['id'],
                        "name": duplicate_customer['name']
                    }
                }
        
        # Update customer
        try:
            conn.execute('''
                UPDATE customers SET
                    name = ?, phone = ?, email = ?, address = ?, 
                    credit_limit = ?, customer_type = ?
                WHERE id = ?
            ''', (
                name,
                phone,
                data.get('email', existing_customer['email']),
                data.get('address', existing_customer['address']),
                float(data.get('credit_limit', existing_customer['credit_limit'])),
                data.get('customer_type', existing_customer['customer_type']),
                customer_id
            ))
            
            conn.commit()
            print(f"[CUSTOMER UPDATE] Successfully updated customer: {customer_id}")
            
        except sqlite3.IntegrityError as e:
            conn.close()
            return {
                "success": False,
                "error": f"Database constraint error: {str(e)}"
            }
        
        conn.close()
        
        # 🔥 LOG REAL-TIME ACTIVITY - Customer updated
        try:
            from modules.dashboard.models import log_customer_activity
            log_customer_activity(
                customer_id=customer_id,
                customer_name=name,
                action='updated profile',
                phone=phone
            )
            print(f"✅ [DASHBOARD] Activity logged: Customer updated - {name}")
        except Exception as e:
            print(f"⚠️ [DASHBOARD] Failed to log customer activity: {e}")
        
        return {
            "success": True,
            "message": "Customer updated successfully",
            "customer": {
                "id": customer_id,
                "name": name,
                "phone": phone,
                "email": data.get('email', ''),
                "address": data.get('address', '')
            }
        }
    
    def delete_customer(self, customer_id):
        """Soft delete customer (set is_active = 0)"""
        print(f"[CUSTOMER DELETE] Deleting customer: {customer_id}")
        
        conn = get_db_connection()
        
        # Check if customer exists
        customer = conn.execute('''
            SELECT id, name, phone FROM customers WHERE id = ? AND is_active = 1
        ''', (customer_id,)).fetchone()
        
        if not customer:
            conn.close()
            return {
                "success": False,
                "error": "Customer not found"
            }
        
        # Soft delete - set is_active = 0
        conn.execute('UPDATE customers SET is_active = 0 WHERE id = ?', (customer_id,))
        conn.commit()
        conn.close()
        
        print(f"[CUSTOMER DELETE] Successfully deleted: {customer['name']}")
        
        return {
            "success": True,
            "message": f"Customer '{customer['name']}' deleted successfully",
            "deleted_customer": {
                "id": customer_id,
                "name": customer['name'],
                "phone": customer['phone']
            }
        }
    
    def search_customers(self, query, user_id=None):
        """Search customers by name or phone filtered by user_id"""
        conn = get_db_connection()
        
        if user_id:
            # Search by name or phone for specific user
            customers = conn.execute('''
                SELECT * FROM customers 
                WHERE (name LIKE ? OR phone LIKE ?) AND is_active = 1 AND (user_id = ? OR user_id IS NULL)
                ORDER BY name
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%', user_id)).fetchall()
        else:
            # Search by name or phone (all users)
            customers = conn.execute('''
                SELECT * FROM customers 
                WHERE (name LIKE ? OR phone LIKE ?) AND is_active = 1
                ORDER BY name
                LIMIT 20
            ''', (f'%{query}%', f'%{query}%')).fetchall()
        
        conn.close()
        
        return {
            "success": True,
            "customers": [dict(row) for row in customers],
            "count": len(customers),
            "query": query
        }