import support

try:
    with support.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'notifications' 
                ORDER BY ordinal_position
            """)
            print("Notifications table structure:")
            print("Column Name\t\tData Type\t\tNullable")
            print("-" * 60)
            for row in cur.fetchall():
                print(f"{row[0]:<20}\t{row[1]:<20}\t{row[2]}")
            
            # Check if there are any notifications
            cur.execute("SELECT COUNT(*) FROM notifications")
            count = cur.fetchone()[0]
            print(f"\nTotal notifications: {count}")
            
            if count > 0:
                cur.execute("SELECT user_id, type, message FROM notifications LIMIT 3")
                print("\nSample notifications:")
                for row in cur.fetchall():
                    print(f"user_id: {row[0]} (type: {type(row[0])}), type: {row[1]}, message: {row[2][:50]}...")
                    
except Exception as e:
    print(f"Error: {e}") 