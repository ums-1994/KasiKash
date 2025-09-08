import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def run_migration():
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

        # Add missing profile columns
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS full_name VARCHAR(100),
            ADD COLUMN IF NOT EXISTS phone VARCHAR(20),
            ADD COLUMN IF NOT EXISTS id_number VARCHAR(20),
            ADD COLUMN IF NOT EXISTS address TEXT,
            ADD COLUMN IF NOT EXISTS date_of_birth DATE,
            ADD COLUMN IF NOT EXISTS bio TEXT,
            ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(255),
            ADD COLUMN IF NOT EXISTS id_document VARCHAR(255),
            ADD COLUMN IF NOT EXISTS proof_of_address VARCHAR(255),
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
        """)

        conn.commit()
        print("Successfully added profile columns to users table")

    except Exception as e:
        print(f"Error running migration: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run_migration() 