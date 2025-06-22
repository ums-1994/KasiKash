import psycopg2
from dotenv import load_dotenv
import os
import bcrypt

# Load environment variables
load_dotenv()

def init_db():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname='postgres',  # Connect to default database first
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (os.getenv('DB_NAME'),))
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME')}")
        
        # Connect to the new database
        conn.close()
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cursor = conn.cursor()

        # Read and execute the complete schema.sql file
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)

        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_db() 