import os
import support
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def debug_user_kyc_status():
    """
    Connects to the database and fetches all records for a specific email
    to diagnose data inconsistencies.
    """
    user_email = 'dzunisanimabunda85@gmail.com'
    print(f"--- Diagnosing KYC issue for email: {user_email} ---")

    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                print(f"Searching for user records with email: '{user_email}'...")
                query = "SELECT id, username, email, firebase_uid, kyc_status, kyc_verified_at FROM users WHERE email = %s"
                cur.execute(query, (user_email,))
                
                results = cur.fetchall()

                if not results:
                    print("\n[ERROR] No user found with that email address.")
                    return

                print(f"\nFound {len(results)} record(s) associated with this email:")
                print("-" * 60)

                for i, user in enumerate(results):
                    print(f"RECORD #{i + 1}")
                    print(f"  - Internal DB ID: {user['id']}")
                    print(f"  - Username:         {user['username']}")
                    print(f"  - Email:            {user['email']}")
                    print(f"  - Firebase UID:     {user['firebase_uid']}")
                    print(f"  - KYC Status:       {user['kyc_status']}")
                    print(f"  - KYC Verified At:  {user['kyc_verified_at']}")
                    print("-" * 60)

                print("\n[Analysis]")
                if len(results) > 1:
                    print("Multiple records found. This is the likely source of the problem.")
                    print("The system may be updating one record while you are logged in with another.")
                else:
                    print("Only one record found. Please verify the 'KYC Status' above is 'approved'.")

    except Exception as e:
        print(f"\n[ERROR] An error occurred while running the diagnostic script: {e}")

if __name__ == '__main__':
    debug_user_kyc_status() 