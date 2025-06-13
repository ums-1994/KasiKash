import sys
import os

# Add current directory to path so we can import support
sys.path.append('.')
from support import execute_query

def check_users():
    """Check users in the database"""
    print("Checking users in database...")
    print("=" * 40)
    
    try:
        # Check if users table exists and has data
        users = execute_query('search', "SELECT * FROM users")
        
        if users:
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  ID: {user[0]}, Firebase UID: {user[1]}, Username: {user[2]}, Email: {user[3]}")
        else:
            print("No users found in database.")
            
        # Check if the user is in session (this would be set during login)
        print("\nNote: If you're logged in, check if your Firebase UID is stored in the session.")
        
    except Exception as e:
        print(f"Error checking users: {e}")

if __name__ == "__main__":
    check_users() 