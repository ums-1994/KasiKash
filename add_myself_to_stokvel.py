import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

STOKVEL_ID = 2  # Change if needed
USER_ID = 1    # Replace with your actual user ID

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO stokvel_members (stokvel_id, user_id, role)
        VALUES (%s, %s, 'admin')
        ON CONFLICT (stokvel_id, user_id) DO UPDATE SET role = 'admin'
    """, (STOKVEL_ID, USER_ID))
    conn.commit()
    print(f"Added user {USER_ID} as admin to stokvel {STOKVEL_ID}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()