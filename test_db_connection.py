import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    try:
        # Get database credentials from environment variables
        db_name = os.getenv('DB_NAME', 'kasikash_db')
        db_user = os.getenv('DB_USER', 'kasikash_user')
        db_password = os.getenv('DB_PASSWORD', 'kasikash_password')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        
        print(f"Attempting to connect with:")
        print(f"DB_NAME: {db_name}")
        print(f"DB_USER: {db_user}")
        print(f"DB_HOST: {db_host}")
        print(f"DB_PORT: {db_port}")
        
        # Try to connect to the database
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Execute a test query
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("Successfully connected to PostgreSQL!")
        print(f"PostgreSQL version: {version[0]}")
        
        # List all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cur.fetchall()
        print("\nTables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error connecting to the database: {e}")

if __name__ == "__main__":
    test_connection() 