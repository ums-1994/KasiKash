import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def allow_null_user_id():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Altering stokvel_members table to allow user_id to be NULL...")
        cur.execute("ALTER TABLE stokvel_members ALTER COLUMN user_id DROP NOT NULL;")
        print("Migration applied successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    allow_null_user_id() 