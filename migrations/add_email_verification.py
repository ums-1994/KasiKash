import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'kasikash'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )

def add_verification_fields():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Add verification fields to users table
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS verification_token VARCHAR(100),
            ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE
        """)
        
        conn.commit()
        print("Successfully added email verification fields to users table")
    except Exception as e:
        print(f"Error adding verification fields: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_verification_fields() 