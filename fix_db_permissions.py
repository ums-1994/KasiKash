import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_permissions():
    try:
        # Connect as superuser or database owner to grant permissions
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Fixing database permissions...")
        
        # Get the database user from environment
        db_user = os.getenv('DB_USER')
        
        # Grant all permissions on all tables to the user
        tables = [
            'users', 'stokvels', 'stokvel_members', 'transactions', 
            'payment_methods', 'savings_goals', 'user_settings'
        ]
        
        for table in tables:
            try:
                # Grant all permissions on the table
                cur.execute(f"GRANT ALL PRIVILEGES ON TABLE {table} TO {db_user}")
                print(f"Granted permissions on {table} table")
                
                # Grant usage on sequences (for auto-incrementing IDs)
                cur.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {db_user}")
                print(f"Granted sequence permissions")
                
            except Exception as e:
                print(f"Error granting permissions on {table}: {e}")
        
        # Grant schema permissions
        cur.execute(f"GRANT ALL PRIVILEGES ON SCHEMA public TO {db_user}")
        print("Granted schema permissions")
        
        # Grant database permissions
        cur.execute(f"GRANT CONNECT ON DATABASE {os.getenv('DB_NAME')} TO {db_user}")
        print("Granted database connection permissions")
        
        print("Database permissions fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing permissions: {e}")
        print("\nIf you're still getting permission errors, you may need to:")
        print("1. Connect as a database superuser (postgres)")
        print("2. Run: GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;")
        print("3. Run: GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_database_permissions() 