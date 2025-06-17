import sys
import os

# Add current directory to path so we can import support
sys.path.append('.')
from support import execute_query

def create_user():
    """Create a user record for the logged-in user"""
    print("Creating user record...")
    print("=" * 40)
    
    # Your Firebase UID from the logs
    firebase_uid = "FFlqY8853MbdDJnovrNdTKuchRr1"
    
    try:
        # Check if user already exists
        existing_user = execute_query('search', "SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
        
        if existing_user:
            print(f"User already exists: {existing_user[0]}")
            return
        
        # Create user record
        print(f"Creating user with Firebase UID: {firebase_uid}")
        execute_query('insert', """
            INSERT INTO users (firebase_uid, username, email, notification_preferences, two_factor_enabled)
            VALUES (%s, %s, %s, %s, %s)
        """, (firebase_uid, "User", "user@example.com", "email", False))
        
        print("User created successfully!")
        
        # Verify the user was created
        user = execute_query('search', "SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
        if user:
            print(f"User record: {user[0]}")
        
    except Exception as e:
        print(f"Error creating user: {e}")

if __name__ == "__main__":
    create_user() 