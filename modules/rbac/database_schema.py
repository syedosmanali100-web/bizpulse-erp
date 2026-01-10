"""
Enterprise RBAC Database Schema
Multi-tenant with strict data isolation
"""

import sqlite3
from modules.shared.database import get_db_connection, generate_id
import bcrypt
from datetime import datetime

def init_rbac_tables():
    """Initialize all RBAC tables with enterprise-grade security"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ============================================================================
    # 1. SUPER ADMIN TABLE (ERP Owner)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS super_admins (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============================================================================
    # 2. TENANTS TABLE (Clients/Shop Owners/Businesses)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            tenant_id TEXT UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            mobile_encrypted TEXT NOT NULL,
            email_encrypted TEXT NOT NULL,
            gst_number TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            country TEXT DEFAULT 'India',
            
            -- Credentials
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            temp_password TEXT,
            
            -- Subscription
            plan_type TEXT DEFAULT 'trial',
            plan_start_date DATE,
            plan_expiry_date DATE,
            subscription_status TEXT DEFAULT 'active',
            
            -- Status
            status TEXT DEFAULT 'active',
            is_active BOOLEAN DEFAULT 1,
            suspended_reason TEXT,
            suspended_at TIMESTAMP,
            
            -- Tracking
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP,
            
            -- Metadata
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (created_by) REFERENCES super_admins (id)
        )
    ''')
    
    # ============================================================================
    # 3. TENANT USERS TABLE (Employees created by clients)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenant_users (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            mobile TEXT,
            role_id TEXT NOT NULL,
            
            -- Status
            is_active BOOLEAN DEFAULT 1,
            status TEXT DEFAULT 'active',
            
            -- Tracking
            last_login TIMESTAMP,
            login_count INTEGER DEFAULT 0,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP,
            
            -- Metadata
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE RESTRICT,
            FOREIGN KEY (created_by) REFERENCES tenants (id)
        )
    ''')
    
    # ============================================================================
    # 4. ROLES TABLE (Predefined + Custom roles per tenant)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            role_name TEXT NOT NULL,
            role_code TEXT NOT NULL,
            description TEXT,
            is_system_role BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE,
            UNIQUE(tenant_id, role_code)
        )
    ''')
    
    # ============================================================================
    # 5. PERMISSIONS TABLE (Granular module-level permissions)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id TEXT PRIMARY KEY,
            module_name TEXT NOT NULL,
            module_code TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT DEFAULT 'general',
            display_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============================================================================
    # 6. ROLE_PERMISSIONS TABLE (Many-to-many mapping)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            id TEXT PRIMARY KEY,
            role_id TEXT NOT NULL,
            permission_id TEXT NOT NULL,
            can_view BOOLEAN DEFAULT 0,
            can_create BOOLEAN DEFAULT 0,
            can_edit BOOLEAN DEFAULT 0,
            can_delete BOOLEAN DEFAULT 0,
            can_export BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE,
            UNIQUE(role_id, permission_id)
        )
    ''')
    
    # ============================================================================
    # 7. AUDIT_LOGS TABLE (Complete activity tracking)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            user_id TEXT,
            user_type TEXT NOT NULL,
            action TEXT NOT NULL,
            module TEXT,
            resource_type TEXT,
            resource_id TEXT,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            user_agent TEXT,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
        )
    ''')
    
    # ============================================================================
    # 8. SESSION_TOKENS TABLE (JWT token management)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            user_type TEXT NOT NULL,
            tenant_id TEXT,
            access_token TEXT NOT NULL UNIQUE,
            refresh_token TEXT NOT NULL UNIQUE,
            access_token_expires_at TIMESTAMP NOT NULL,
            refresh_token_expires_at TIMESTAMP NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT 1,
            revoked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
        )
    ''')
    
    # ============================================================================
    # 9. LOGIN_ATTEMPTS TABLE (Rate limiting & security)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            attempt_type TEXT DEFAULT 'login',
            status TEXT DEFAULT 'failed',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ============================================================================
    # 10. SUBSCRIPTION_HISTORY TABLE (Track plan changes)
    # ============================================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscription_history (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            plan_duration TEXT,
            amount REAL,
            start_date DATE,
            expiry_date DATE,
            payment_method TEXT,
            payment_reference TEXT,
            status TEXT DEFAULT 'active',
            changed_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE,
            FOREIGN KEY (changed_by) REFERENCES super_admins (id)
        )
    ''')
    
    # ============================================================================
    # CREATE INDEXES FOR PERFORMANCE
    # ============================================================================
    
    # Tenants indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenants_tenant_id ON tenants(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenants_username ON tenants(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenants_plan_expiry ON tenants(plan_expiry_date)')
    
    # Tenant users indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant_id ON tenant_users(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_users_username ON tenant_users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_users_role_id ON tenant_users(role_id)')
    
    # Roles indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_roles_code ON roles(role_code)')
    
    # Audit logs indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_tenant_id ON audit_logs(tenant_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)')
    
    # Session tokens indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_access_token ON session_tokens(access_token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_refresh_token ON session_tokens(refresh_token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_user_id ON session_tokens(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_tenant_id ON session_tokens(tenant_id)')
    
    # Login attempts indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_created_at ON login_attempts(created_at)')
    
    conn.commit()
    
    # ============================================================================
    # INITIALIZE DEFAULT DATA
    # ============================================================================
    initialize_default_data(conn)
    
    conn.close()
    print("✅ RBAC tables initialized successfully")


def initialize_default_data(conn):
    """Initialize default super admin, roles, and permissions"""
    cursor = conn.cursor()
    
    # ============================================================================
    # 1. CREATE DEFAULT SUPER ADMIN
    # ============================================================================
    cursor.execute('SELECT COUNT(*) FROM super_admins')
    if cursor.fetchone()[0] == 0:
        admin_id = generate_id()
        # Default credentials: admin@bizpulse.com / Admin@123
        password_hash = bcrypt.hashpw('Admin@123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute('''
            INSERT INTO super_admins (id, username, email, password_hash, full_name, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (admin_id, 'superadmin', 'admin@bizpulse.com', password_hash, 'Super Administrator', 1))
        
        print("✅ Default Super Admin created: admin@bizpulse.com / Admin@123")
    
    # ============================================================================
    # 2. CREATE DEFAULT PERMISSIONS (Modules)
    # ============================================================================
    cursor.execute('SELECT COUNT(*) FROM permissions')
    if cursor.fetchone()[0] == 0:
        default_permissions = [
            ('dashboard', 'Dashboard', 'View business overview and analytics', 'core', 1),
            ('sales', 'Sales', 'Manage sales transactions and invoices', 'core', 2),
            ('purchases', 'Purchases', 'Manage purchase orders and suppliers', 'core', 3),
            ('products', 'Products', 'Manage product inventory and catalog', 'core', 4),
            ('customers', 'Customers', 'Manage customer database', 'core', 5),
            ('suppliers', 'Suppliers', 'Manage supplier relationships', 'core', 6),
            ('accounts', 'Accounts', 'Manage financial accounts and ledgers', 'finance', 7),
            ('reports', 'Reports', 'View and export business reports', 'analytics', 8),
            ('settings', 'Settings', 'Configure system settings', 'admin', 9),
            ('users', 'User Management', 'Manage internal users and roles', 'admin', 10),
            ('billing', 'Billing', 'Create and manage bills', 'core', 11),
            ('credit', 'Credit Management', 'Manage credit sales and payments', 'finance', 12),
            ('earnings', 'Earnings', 'View profit and earnings analytics', 'analytics', 13),
            ('hotel', 'Hotel Management', 'Manage hotel bookings and guests', 'specialized', 14),
            ('retail', 'Retail Management', 'Manage retail operations', 'specialized', 15),
        ]
        
        for code, name, desc, category, order in default_permissions:
            cursor.execute('''
                INSERT INTO permissions (id, module_code, module_name, description, category, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (generate_id(), code, name, desc, category, order))
        
        print("✅ Default permissions created")
    
    # ============================================================================
    # 3. CREATE DEFAULT SYSTEM ROLES
    # ============================================================================
    cursor.execute('SELECT COUNT(*) FROM roles WHERE is_system_role = 1')
    if cursor.fetchone()[0] == 0:
        default_roles = [
            ('admin', 'Administrator', 'Full system access', 1),
            ('manager', 'Manager', 'Manage operations and view reports', 1),
            ('accountant', 'Accountant', 'Manage accounts and financial data', 1),
            ('billing_executive', 'Billing Executive', 'Create bills and manage sales', 1),
            ('store_manager', 'Store Manager', 'Manage inventory and products', 1),
            ('viewer', 'Viewer', 'Read-only access to data', 1),
        ]
        
        for code, name, desc, is_system in default_roles:
            role_id = generate_id()
            cursor.execute('''
                INSERT INTO roles (id, tenant_id, role_code, role_name, description, is_system_role)
                VALUES (?, NULL, ?, ?, ?, ?)
            ''', (role_id, code, name, desc, is_system))
            
            # Assign permissions based on role
            assign_default_permissions(cursor, role_id, code)
        
        print("✅ Default system roles created")
    
    conn.commit()


def assign_default_permissions(cursor, role_id, role_code):
    """Assign default permissions to system roles"""
    
    # Get all permissions
    cursor.execute('SELECT id, module_code FROM permissions')
    permissions = cursor.fetchall()
    
    for perm_id, module_code in permissions:
        can_view = False
        can_create = False
        can_edit = False
        can_delete = False
        can_export = False
        
        # Administrator - Full access
        if role_code == 'admin':
            can_view = can_create = can_edit = can_delete = can_export = True
        
        # Manager - Most access except delete
        elif role_code == 'manager':
            can_view = can_create = can_edit = can_export = True
            can_delete = module_code not in ['settings', 'users']
        
        # Accountant - Finance focused
        elif role_code == 'accountant':
            if module_code in ['dashboard', 'accounts', 'reports', 'earnings', 'credit']:
                can_view = can_create = can_edit = can_export = True
            elif module_code in ['sales', 'purchases', 'customers', 'suppliers']:
                can_view = can_export = True
        
        # Billing Executive - Sales focused
        elif role_code == 'billing_executive':
            if module_code in ['dashboard', 'sales', 'billing', 'customers', 'products']:
                can_view = can_create = can_edit = True
            elif module_code in ['reports']:
                can_view = can_export = True
        
        # Store Manager - Inventory focused
        elif role_code == 'store_manager':
            if module_code in ['dashboard', 'products', 'purchases', 'suppliers']:
                can_view = can_create = can_edit = True
            elif module_code in ['sales', 'reports']:
                can_view = True
        
        # Viewer - Read only
        elif role_code == 'viewer':
            if module_code not in ['settings', 'users']:
                can_view = True
        
        # Insert permission mapping
        if can_view or can_create or can_edit or can_delete or can_export:
            cursor.execute('''
                INSERT INTO role_permissions (id, role_id, permission_id, can_view, can_create, can_edit, can_delete, can_export)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (generate_id(), role_id, perm_id, can_view, can_create, can_edit, can_delete, can_export))


if __name__ == '__main__':
    init_rbac_tables()
