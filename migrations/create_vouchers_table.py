import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_vouchers_table():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'kasikash_db'),
            user=os.getenv('DB_USER', 'kasikash_user'),
            password=os.getenv('DB_PASSWORD', 'test123'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS vouchers (
                id SERIAL PRIMARY KEY,
                code VARCHAR(100) UNIQUE NOT NULL,
                user_id VARCHAR(128) REFERENCES users(firebase_uid),
                amount NUMERIC(10, 2) NOT NULL,
                is_redeemed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                redeemed_at TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        print("✅ vouchers table created or already exists.")
    except Exception as e:
        print(f"❌ Error creating vouchers table: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_vouchers_table() 