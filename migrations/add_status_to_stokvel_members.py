import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def apply_migration():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        print("Adding status column to stokvel_members...")
        try:
            cur.execute("ALTER TABLE stokvel_members ADD COLUMN status VARCHAR(20) DEFAULT 'pending';")
            print("Column added.")
        except Exception as e:
            print(f"Could not add column (it may already exist): {e}")
        conn.commit()
        cur.close()
        conn.close()
        print("Migration complete.")
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    apply_migration()
