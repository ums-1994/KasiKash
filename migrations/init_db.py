import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    print("Initializing database...")
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Read and execute the schema SQL
        with open('schema.sql', 'r') as file:
            sql = file.read()
            cur.execute(sql)

        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    init_database() 