import psycopg2
import os

def init_db():
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname='postgres',  # Connect to default database first
        user='postgres',
        password='12345',
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'kasikash'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE kasikash")
        
        # Connect to the new database
        conn.close()
        conn = psycopg2.connect(
            dbname='kasikash',
            user='postgres',
            password='12345',
            host='localhost',
            port='5432'
        )
        cursor = conn.cursor()

        # Read and execute the schema.sql file
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