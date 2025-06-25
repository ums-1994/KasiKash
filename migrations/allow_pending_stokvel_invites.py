import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

migration_sql = [
    "ALTER TABLE stokvel_members ALTER COLUMN user_id DROP NOT NULL;",
    "CREATE UNIQUE INDEX IF NOT EXISTS stokvel_members_stokvel_id_email_idx ON stokvel_members(stokvel_id, email);"
]

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
        for sql in migration_sql:
            print(f"Running: {sql}")
            cur.execute(sql)
        conn.commit()
        print("Migration applied successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    apply_migration() 