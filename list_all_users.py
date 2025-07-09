import psycopg2
import os

# --- CONFIG ---
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'kasikash'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'dev_password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT firebase_uid, username, email FROM users ORDER BY username")
        users = cur.fetchall()
        print(f"{'firebase_uid':<36} {'username':<20} {'email'}")
        print('-'*80)
        for u in users:
            print(f"{u[0]:<36} {u[1]:<20} {u[2]}")
    finally:
        cur.close()
        conn.close()
        print("Done.")

if __name__ == '__main__':
    main() 