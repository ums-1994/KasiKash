import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def check_session():
    print("Checking session and database data...")
    print("=" * 40)
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Print all users in the database
        print("\nAll users in the database:")
        cur.execute("SELECT id, firebase_uid, username, email FROM users")
        users = cur.fetchall()
        for user in users:
            print(f"ID: {user[0]}, Firebase UID: {user[1]}, Username: {user[2]}, Email: {user[3]}")

        # Print all stokvel_members
        print("\nAll stokvel_members:")
        cur.execute("SELECT id, stokvel_id, user_id, role FROM stokvel_members")
        members = cur.fetchall()
        for member in members:
            print(f"ID: {member[0]}, Stokvel ID: {member[1]}, User ID: {member[2]}, Role: {member[3]}")

        # Print the current session's firebase_uid and user_id
        print("\nCurrent session data:")
        print("firebase_uid:", os.getenv('FIREBASE_UID', 'Not set'))
        print("user_id:", os.getenv('USER_ID', 'Not set'))

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_session() 