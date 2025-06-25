import psycopg2
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, auth

# Load environment variables
load_dotenv()

def check_and_fix_user():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        
        # Check user in database
        email = "nkabindethabang77@gmail.com"
        cur.execute("SELECT id, username, email, firebase_uid FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user:
            print(f"\nUser found in database:")
            print(f"ID: {user[0]}")
            print(f"Username: {user[1]}")
            print(f"Email: {user[2]}")
            print(f"Firebase UID: {user[3]}")
            
            # Initialize Firebase Admin
            cred = credentials.Certificate(os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH'))
            firebase_admin.initialize_app(cred)
            
            try:
                # Try to get user from Firebase
                firebase_user = auth.get_user_by_email(email)
                print(f"\nUser found in Firebase:")
                print(f"Firebase UID: {firebase_user.uid}")
                
                # Update Firebase UID in database if different
                if user[3] != firebase_user.uid:
                    cur.execute("UPDATE users SET firebase_uid = %s WHERE email = %s", 
                              (firebase_user.uid, email))
                    conn.commit()
                    print("\nUpdated Firebase UID in database")
                
            except auth.UserNotFoundError:
                print("\nUser not found in Firebase")
                response = input("\nDo you want to delete this user from the database? (yes/no): ")
                if response.lower() == 'yes':
                    cur.execute("DELETE FROM users WHERE email = %s", (email,))
                    conn.commit()
                    print("User deleted from database")
                else:
                    print("User kept in database")
        
        else:
            print(f"\nNo user found with email: {email}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_and_fix_user() 