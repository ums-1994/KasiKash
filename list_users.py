import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users")
    rows = cur.fetchall()
    if rows:
        print("Existing users:")
        for row in rows:
            print(f"ID: {row[0]}, Email: {row[1]}")
    else:
        print("No users found.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()