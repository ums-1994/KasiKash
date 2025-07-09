import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'kasikash_db')
DB_USER = os.getenv('DB_USER', 'kasikash_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'kasikash_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

tables = ['chat_messages', 'chat_members', 'chat_rooms']

def drop_tables():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        with conn:
            with conn.cursor() as cur:
                for table in tables:
                    try:
                        cur.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table)))
                        print(f"Dropped table (if existed): {table}")
                    except Exception as e:
                        print(f"Error dropping {table}: {e}")
        conn.close()
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    drop_tables() 