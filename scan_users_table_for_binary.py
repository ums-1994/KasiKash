import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def scan_users_table_for_binary():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM users LIMIT 20")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        print(f"Scanning {len(rows)} rows in users table...")
        for idx, row in enumerate(rows):
            for col_idx, value in enumerate(row):
                if isinstance(value, bytes):
                    try:
                        value.decode('utf-8')
                    except Exception as e:
                        print(f"Row {idx+1}, Column '{columns[col_idx]}': Binary/Non-UTF8 data detected! Error: {e}")
                elif isinstance(value, str):
                    try:
                        value.encode('utf-8')
                    except Exception as e:
                        print(f"Row {idx+1}, Column '{columns[col_idx]}': String cannot be encoded as UTF-8! Error: {e}")
        print("Scan complete.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    scan_users_table_for_binary() 