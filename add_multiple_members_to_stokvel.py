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

STOKVEL_ID = 8  # or your target stokvel
USER_IDS = [
    'byhpFgGbCHVwO71hEukuehLgxN43',  # Sibusisiwe
    'VzGHuqkhJBaUiooYEmN49mNHTNz2',  # Thabang
]
ROLE = 'member'  # or 'admin'

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        for user_id in USER_IDS:
            cur.execute("SELECT * FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s", (STOKVEL_ID, user_id))
            if cur.fetchone():
                print(f"User {user_id} is already a member of stokvel {STOKVEL_ID}.")
            else:
                cur.execute(
                    "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
                    (STOKVEL_ID, user_id, ROLE)
                )
                print(f"Added user {user_id} as {ROLE} to stokvel {STOKVEL_ID}.")
        conn.commit()
    finally:
        cur.close()
        conn.close()
        print("Done.")

if __name__ == '__main__':
    main() 