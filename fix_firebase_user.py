import firebase_admin
from firebase_admin import credentials, auth
import psycopg2
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

def fix_firebase_user():
    try:
        # Initialize Firebase Admin with the service account key
        service_account_path = 'kasikashapp-4f72a-firebase-adminsdk-fbsvc-b3a75155f2.json'
        
        # Check if Firebase is already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            # Initialize Firebase if not already initialized
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Get user from database
        email = "nkabindethabang77@gmail.com"
        cur.execute("SELECT id, username, email, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if user:
            print(f"\nUser found in database:")
            print(f"ID: {user[0]}")
            print(f"Username: {user[1]}")
            print(f"Email: {user[2]}")

            try:
                # Try to create user in Firebase
                user_properties = {
                    'email': email,
                    'email_verified': True,
                    'display_name': user[1],
                    'password': 'TemporaryPassword123!'  # This will be changed by the user
                }
                
                firebase_user = auth.create_user(**user_properties)
                print(f"\nUser created in Firebase:")
                print(f"Firebase UID: {firebase_user.uid}")

                # Update Firebase UID in database
                cur.execute("UPDATE users SET firebase_uid = %s WHERE email = %s", 
                          (firebase_user.uid, email))
                conn.commit()
                print("\nUpdated Firebase UID in database")

                # Send password reset email
                reset_link = auth.generate_password_reset_link(email)
                print(f"\nPassword reset link generated: {reset_link}")
                print("Please check your email for the password reset link")

            except auth.EmailAlreadyExistsError:
                print("\nUser already exists in Firebase")
                # Get the existing Firebase user
                firebase_user = auth.get_user_by_email(email)
                print(f"Firebase UID: {firebase_user.uid}")

                # Update Firebase UID in database
                cur.execute("UPDATE users SET firebase_uid = %s WHERE email = %s", 
                          (firebase_user.uid, email))
                conn.commit()
                print("\nUpdated Firebase UID in database")

                # Generate a new password reset link
                reset_link = auth.generate_password_reset_link(email)
                print(f"\nNew password reset link generated: {reset_link}")
                print("Please check your email for the password reset link")

        else:
            print(f"\nNo user found with email: {email}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_firebase_user() 