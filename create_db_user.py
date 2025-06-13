import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database_user():
    """Create the kasikash_user and database"""
    
    # Connect as postgres superuser
    try:
        # Try to connect with postgres user first
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="postgres"
        )
        print("✅ Connected to PostgreSQL as postgres user")
    except Exception as e:
        print(f"❌ Failed to connect as postgres user: {e}")
        print("Trying alternative connection...")
        
        # Try without password (trust authentication)
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="postgres",
                user="postgres"
            )
            print("✅ Connected to PostgreSQL without password")
        except Exception as e2:
            print(f"❌ Failed to connect: {e2}")
            print("\nPlease try one of these solutions:")
            print("1. Set a password for postgres user")
            print("2. Use pgAdmin to create the user manually")
            print("3. Use the default postgres user in your .env file")
            return False
    
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Create user if not exists
        print("Creating kasikash_user...")
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'kasikash_user') THEN
                    CREATE USER kasikash_user WITH PASSWORD 'kasikash_password';
                END IF;
            END
            $$;
        """)
        print("✅ User kasikash_user created/verified")
        
        # Create database if not exists
        print("Creating kasikash_db...")
        cursor.execute("""
            SELECT 'CREATE DATABASE kasikash_db OWNER kasikash_user'
            WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kasikash_db')\gexec
        """)
        print("✅ Database kasikash_db created/verified")
        
        # Grant privileges
        print("Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE kasikash_db TO kasikash_user;")
        print("✅ Privileges granted")
        
        # Test connection with new user
        print("Testing connection with kasikash_user...")
        test_conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="kasikash_db",
            user="kasikash_user",
            password="kasikash_password"
        )
        test_conn.close()
        print("✅ Connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Creating PostgreSQL User and Database...")
    print("=" * 50)
    
    if create_database_user():
        print("\n🎉 Success! Your database is ready.")
        print("\nYour .env file should contain:")
        print("DB_USER=kasikash_user")
        print("DB_PASSWORD=kasikash_password")
        print("DB_NAME=kasikash_db")
    else:
        print("\n❌ Failed to create database user.")
        print("You may need to:")
        print("1. Set a password for the postgres user")
        print("2. Use pgAdmin to create the user manually")
        print("3. Use the default postgres user instead") 