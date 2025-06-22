import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

# Get database configuration from environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

try:
    # Connect to the database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("Successfully connected to the database!")
    
    # Create a cursor
    cur = conn.cursor()
    
    # Test query
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    # Close cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to the database: {str(e)}") 