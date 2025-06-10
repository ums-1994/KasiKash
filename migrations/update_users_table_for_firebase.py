import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_users_table():
    print("Adding firebase_uid column...")
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        cur.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(128) UNIQUE;
        """)

        # Remove old columns if they exist (only if Firebase is fully replacing them)
        # Check if 'password' column exists before attempting to drop
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password');")
        if cur.fetchone()[0]:
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS password;")

        # Check if 'verification_token' column exists before attempting to drop
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token');")
        if cur.fetchone()[0]:
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS verification_token;")
        
        # Check if 'is_verified' column exists before attempting to drop
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_verified');")
        if cur.fetchone()[0]:
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS is_verified;")

        conn.commit()
        cur.close()
        print("firebase_uid column added and old columns removed successfully!")

    except psycopg2.Error as e:
        print(f"Error updating users table: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_users_table() 