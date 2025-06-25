import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

EMAIL = os.getenv('MY_EMAIL')  # Set this in your .env or replace with your email
FIREBASE_UID = os.getenv('MY_FIREBASE_UID')  # Optional: set this if you want to use firebase_uid

def print_my_stokvels():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    # Find user by email or firebase_uid
    if EMAIL:
        cur.execute("SELECT id, email, firebase_uid FROM users WHERE email = %s", (EMAIL,))
    elif FIREBASE_UID:
        cur.execute("SELECT id, email, firebase_uid FROM users WHERE firebase_uid = %s", (FIREBASE_UID,))
    else:
        print("Please set MY_EMAIL or MY_FIREBASE_UID in your .env file.")
        return
    user = cur.fetchone()
    if not user:
        print("User not found.")
        return
    user_id, email, firebase_uid = user
    print(f"User: id={user_id}, email={email}, firebase_uid={firebase_uid}")
    # Find stokvels created by user_id (int) and firebase_uid (str)
    created = set()
    try:
        cur.execute("SELECT id, name FROM stokvels WHERE created_by = %s", (str(user_id),))
        for row in cur.fetchall():
            created.add((row[0], row[1]))
    except Exception as e:
        print(f"Error querying stokvels by user_id: {e}")
        conn.rollback()
    try:
        cur.execute("SELECT id, name FROM stokvels WHERE created_by = %s", (firebase_uid,))
        for row in cur.fetchall():
            created.add((row[0], row[1]))
    except Exception as e:
        print(f"Error querying stokvels by firebase_uid: {e}")
        conn.rollback()
    # Find stokvels where user is a member (by user_id and firebase_uid)
    member = set()
    try:
        cur.execute("SELECT s.id, s.name FROM stokvel_members sm JOIN stokvels s ON sm.stokvel_id = s.id WHERE sm.user_id = %s", (str(user_id),))
        for row in cur.fetchall():
            member.add((row[0], row[1]))
    except Exception as e:
        print(f"Error querying stokvel memberships by user_id: {e}")
        conn.rollback()
    try:
        cur.execute("SELECT s.id, s.name FROM stokvel_members sm JOIN stokvels s ON sm.stokvel_id = s.id WHERE sm.user_id = %s", (firebase_uid,))
        for row in cur.fetchall():
            member.add((row[0], row[1]))
    except Exception as e:
        print(f"Error querying stokvel memberships by firebase_uid: {e}")
        conn.rollback()
    print("\nStokvels created by user:")
    for row in created:
        print(f"  id={row[0]}, name={row[1]}")
    print("\nStokvels where user is a member:")
    for row in member:
        print(f"  id={row[0]}, name={row[1]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    print_my_stokvels() 