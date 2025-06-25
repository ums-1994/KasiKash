import sys
import os
from dotenv import load_dotenv
from support import execute_query

load_dotenv()

def make_admin(email):
    if not email:
        print("Usage: python make_admin.py user@example.com")
        return
    try:
        # Update the user's role to admin
        result = execute_query('update', "UPDATE users SET role = 'admin' WHERE email = %s", (email,))
        if result is None:
            print(f"User with email {email} updated to admin (if they exist).")
        else:
            print(f"User with email {email} updated to admin.")
    except Exception as e:
        print(f"Error updating user: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py user@example.com")
    else:
        make_admin(sys.argv[1]) 