"""
Assign existing data to default user automatically
"""
import sqlite3

def assign_data():
    print("=" * 80)
    print("ASSIGNING EXISTING DATA TO DEFAULT USER")
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
        print(f"\n🔍 Default user: {user[1]} (ID: {default_user_id})")
        
        tables_to_update = [
            ('products', 'user_id'),
            ('customers', 'user_id'),
            ('bills', 'business_owner_id'),
            ('bill_items', 'user_id'),
            ('sales', 'business_owner_id'),
            ('payments', 'user_id'),
            ('hotel_guests', 'user_id'),
            ('hotel_services', 'user_id'),
        ]
        
        print("\n📊 Assigning data...\n")
        
        for table, column in tables_to_update:
            try:
                cursor.execute(f"UPDATE {table} SET {column} = ? WHERE {column} IS NULL", (default_user_id,))
                updated = cursor.rowcount
                if updated > 0:
                    print(f"   ✅ {table}: {updated} records assigned")
                else:
                    print(f"   ℹ️  {table}: No unassigned records")
            except Exception as e:
                print(f"   ❌ {table}: {e}")
        
        conn.commit()
        print("\n✅ All existing data assigned to default user")
    else:
        print("\n⚠️  No users found.")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("ASSIGNMENT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    assign_data()
