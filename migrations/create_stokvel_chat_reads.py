import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def run_migration():
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
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS stokvel_chat_reads (
                user_id VARCHAR(64) NOT NULL,
                stokvel_id INTEGER NOT NULL REFERENCES stokvels(id) ON DELETE CASCADE,
                last_read_at TIMESTAMP NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, stokvel_id)
            );
            """
        )
        conn.commit()
        print("stokvel_chat_reads table ensured.")
    except Exception as e:
        print(f"Migration error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    run_migration()


