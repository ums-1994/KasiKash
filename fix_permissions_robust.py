import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_permissions_robust():
    print("Attempting to fix database permissions...")
    
    # Get database credentials
    db_name = os.getenv('DB_NAME', 'kasikash_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    print(f"Connecting as: {db_user} to {db_name} on {db_host}:{db_port}")
    
    try:
        # Try to connect with current user
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Successfully connected to database")
        
        # Check if we have superuser privileges
        cur.execute("SELECT current_user, session_user")
        current_user, session_user = cur.fetchone()
        print(f"Current user: {current_user}, Session user: {session_user}")
        
        # Try to grant permissions
        try:
            # Grant permissions on all tables
            cur.execute("""
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                        EXECUTE 'GRANT ALL PRIVILEGES ON TABLE public.' || quote_ident(r.tablename) || ' TO ' || quote_ident(current_user);
                    END LOOP;
                END $$;
            """)
            print("✅ Granted permissions on all tables")
            
            # Grant permissions on sequences
            cur.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO " + current_user)
            print("✅ Granted permissions on sequences")
            
            # Grant schema permissions
            cur.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO " + current_user)
            print("✅ Granted schema permissions")
            
        except Exception as e:
            print(f"⚠️ Could not grant permissions: {e}")
            print("This might require superuser privileges")
        
        # Test access to users table
        try:
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            print(f"✅ Successfully accessed users table. Found {count} users.")
        except Exception as e:
            print(f"❌ Still cannot access users table: {e}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nManual steps to fix:")
        print("1. Connect as postgres superuser:")
        print("   sudo -u postgres psql")
        print("2. Grant permissions:")
        print(f"   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {db_user};")
        print("   GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO " + db_user + ";")
        print("   GRANT ALL PRIVILEGES ON SCHEMA public TO " + db_user + ";")

if __name__ == "__main__":
    fix_permissions_robust() 