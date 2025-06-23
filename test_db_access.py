import support

def test_db_access():
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Test basic query
                cur.execute("SELECT COUNT(*) FROM users")
                count = cur.fetchone()[0]
                print(f"✅ Successfully accessed users table. Found {count} users.")
                
                # Test a more complex query
                cur.execute("SELECT firebase_uid, username FROM users LIMIT 1")
                user = cur.fetchone()
                if user:
                    print(f"✅ Successfully queried user data: {user}")
                else:
                    print("✅ Table accessible but no users found.")
                    
    except Exception as e:
        print(f"❌ Database access error: {e}")

if __name__ == "__main__":
    test_db_access() 