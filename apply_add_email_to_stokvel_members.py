import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Load DB connection info from environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

print(f"Using DB credentials: host={DB_HOST}, port={DB_PORT}, db={DB_NAME}, user={DB_USER}")

migration_sql = """
ALTER TABLE stokvel_members ADD COLUMN email VARCHAR(255);
"""

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
        cur.execute(migration_sql)
        conn.commit()
        print("Migration applied: email column added to stokvel_members table.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error applying migration: {e}")

if __name__ == "__main__":
    apply_migration() 