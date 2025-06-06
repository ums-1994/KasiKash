import psycopg2

def test_connection():
    try:
        # Try to connect to the database
        conn = psycopg2.connect(
            dbname='kasikash_db',
            user='postgres',
            password='12345',
            host='localhost',
            port='5432'
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