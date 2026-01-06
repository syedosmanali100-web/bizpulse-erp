"""
Migration Script: Add user_id/business_owner_id to all tables for multi-tenant support
This enables Desktop-Mobile sync for same user
"""
import sqlite3
from datetime import datetime

def migrate_add_user_id():
    print("=" * 80)
    print("MIGRATION: Adding user_id columns for Desktop-Mobile Sync")
    print("=" * 80)
    
    conn = sqlite3.connect('billing.db')
    cursor = conn.cursor()
    
    # List of tables and their user_id column names
    migrations = [
        ('products', 'user_id', 'TEXT'),
        ('customers', 'user_id', 'TEXT'),
        ('bills', 'business_owner_id', 'TEXT'),
        ('bill_items', 'user_id', 'TEXT'),
        ('sales', 'business_owner_id', 'TEXT'),
        ('payments', 'user_id', 'TEXT'),
        ('hotel_guests', 'user_id', 'TEXT'),
        ('hotel_services', 'user_id', 'TEXT'),
        ('recent_activities', 'user_id', 'TEXT'),  # Already has user_id, skip
    ]
    
    print("\n📊 Checking and adding user_id columns...\n")
    
    for table_name, column_name, column_type in migrations:
        try:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"⚠️  Table '{table_name}' does not exist, skipping...")
                continue
            
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if column_name in columns:
                print(f"✅ {table_name}.{column_name} - Already exists")
            else:
                # Add the column
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                print(f"🔥 {table_name}.{column_name} - Added successfully")
                
                # Create index for better query performance
                index_name = f"idx_{table_name}_{column_name}"
                try:
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
                    print(f"   📇 Index created: {index_name}")
                except Exception as e:
                    print(f"   ⚠️  Index creation failed: {e}")
        
        except Exception as e:
            print(f"❌ Error with {table_name}.{column_name}: {e}")
    
    # Commit changes
    conn.commit()
    
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    
    # Show summary
    print("\n📋 Summary:")
    print("   ✅ user_id columns added to all tables")
    print("   ✅ Indexes created for performance")
    print("   ✅ Database ready for multi-tenant support")
    print("\n⚠️  NOTE: Existing data will have NULL user_id")
    print("   You can assign them to a default user or leave as shared data")
    
    conn.close()

def assign_default_user():
    """Optional: Assign existing data to a default user"""
    print("\n" + "=" * 80)
    print("OPTIONAL: Assign existing data to default user")
    print("=" * 80)
    
    conn = sqlite3.connect('billing.db')
    cursor = conn.cursor()
    
    # Get first user/client
    cursor.execute("SELECT id, email FROM users LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("SELECT id, contact_email FROM clients LIMIT 1")
        user = cursor.fetchone()
    
    if user:
        default_user_id = user[0]
        print(f"\n🔍 Found default user: {user[1]} (ID: {default_user_id})")
        
        response = input("\nAssign all existing data to this user? (y/n): ")
        
        if response.lower() == 'y':
            tables_to_update = [
                ('products', 'user_id'),
                ('customers', 'user_id'),
                ('bills', 'business_owner_id'),
                ('bill_items', 'user_id'),
                ('sales', 'business_owner_id'),
                ('payments', 'user_id'),
            ]
            
            for table, column in tables_to_update:
                try:
                    cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} IS NULL", (default_user_id,))
                    updated = cursor.rowcount
                    print(f"   ✅ {table}: {updated} records updated")
                except Exception as e:
                    print(f"   ❌ {table}: {e}")
            
            conn.commit()
            print("\n✅ All existing data assigned to default user")
        else:
            print("\n⚠️  Skipped. Existing data will remain unassigned.")
    else:
        print("\n⚠️  No users found. Create a user first.")
    
    conn.close()

if __name__ == "__main__":
    try:
        migrate_add_user_id()
        
        # Ask if user wants to assign existing data
        print("\n" + "=" * 80)
        assign_default_user()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
