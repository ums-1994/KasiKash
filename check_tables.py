import support
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def check_tables():
    print("Starting database check...")
    print(f"Database connection details:")
    print(f"DB_NAME: {os.getenv('DB_NAME')}")
    print(f"DB_USER: {os.getenv('DB_USER')}")
    print(f"DB_HOST: {os.getenv('DB_HOST')}")
    print(f"DB_PORT: {os.getenv('DB_PORT')}")
    
    try:
        with support.db_connection() as conn:
            print("Successfully connected to database!")
            with conn.cursor() as cur:
                # Check if users table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    );
                """)
                users_exists = cur.fetchone()[0]
                print(f"Users table exists: {users_exists}")

                # Check if expenses table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'expenses'
                    );
                """)
                expenses_exists = cur.fetchone()[0]
                print(f"Expenses table exists: {expenses_exists}")

                # List all tables in the database
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public';
                """)
                tables = cur.fetchall()
                print("\nAll tables in the database:")
                for table in tables:
                    print(f"- {table[0]}")

    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        print("\nPlease check:")
        print("1. Is PostgreSQL running?")
        print("2. Are the database credentials in .env correct?")
        print("3. Does the database exist?")
    except Exception as e:
        print(f"Error checking tables: {e}")

if __name__ == "__main__":
    check_tables() 