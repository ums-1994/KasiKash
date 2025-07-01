import os
import support
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def force_approve_kyc():
    """
    Connects to the database and forcibly updates the KYC status
    for a specific user to 'approved'.
    """
    user_email = 'dzunisanimabunda85@gmail.com'
    print(f"--- Forcibly updating KYC status for email: {user_email} ---")

    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                print(f"Updating user record for email: '{user_email}'...")
                
                # The SQL command to fix the data
                query = "UPDATE users SET kyc_status = 'approved', kyc_verified_at = NOW() WHERE email = %s"
                
                cur.execute(query, (user_email,))
                
                # Check if the update was successful
                if cur.rowcount > 0:
                    conn.commit()
                    print("\n[SUCCESS] The user's KYC status has been successfully updated to 'approved'.")
                    print("Please hard refresh your profile page (Ctrl+F5 or Cmd+Shift+R) to see the change.")
                else:
                    conn.rollback()
                    print("\n[ERROR] Could not find a user with that email to update.")

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        print(f"\n[ERROR] An error occurred: {e}")

if __name__ == '__main__':
    force_approve_kyc() 