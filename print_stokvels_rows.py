import psycopg2
import os

DB_NAME = os.getenv('DB_NAME', 'your_db_name')
DB_USER = os.getenv('DB_USER', 'your_db_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_db_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def print_stokvels_rows():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, created_by FROM stokvels ORDER BY id")
                rows = cur.fetchall()
                print(f"{'Stokvel ID':<12} {'Name':<30} {'Created By'}")
                print('-'*60)
                for row in rows:
                    print(f"{row[0]:<12} {row[1]:<30} {row[2]}")
    finally:
        conn.close()

if __name__ == '__main__':
    print_stokvels_rows() 