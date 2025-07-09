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

STOKVEL_ID = 8  # Change as needed
USER_ID = 'YOUR_USER_ID'  # Replace with your actual user id or firebase_uid
ROLE = 'member'  # or 'admin'

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (STOKVEL_ID, USER_ID))
        if cur.fetchone():
            print(f"User {USER_ID} is already a member of stokvel {STOKVEL_ID}.")
        else:
            cur.execute(
                "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
                (STOKVEL_ID, USER_ID, ROLE)
            )
            conn.commit()
            print(f"Added user {USER_ID} as {ROLE} to stokvel {STOKVEL_ID}.")
    finally:
        cur.close()
        conn.close()
        print("Done.")

if __name__ == '__main__':
    main() 