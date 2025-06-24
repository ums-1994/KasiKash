import sys
import os

# Add current directory to path so we can import support
sys.path.append('.')
from support import execute_query

def check_stokvels():
    """Check stokvels in the database"""
    print("Checking stokvels in database...")
    print("=" * 40)
    
    try:
        # Check if stokvels table exists and has data
        stokvels = execute_query('search', "SELECT * FROM stokvels")
        
        if stokvels:
            print(f"Found {len(stokvels)} stokvels:")
            for stokvel in stokvels:
                print(f"  ID: {stokvel[0]}, Name: {stokvel[1]}, Purpose: {stokvel[2]}, Monthly: {stokvel[3]}, Target: {stokvel[4]}, Date: {stokvel[5]}")
        else:
            print("No stokvels found in database.")
            
        # Check stokvel_members table
        print("\nChecking stokvel members...")
        members = execute_query('search', "SELECT * FROM stokvel_members")
        
        if members:
            print(f"Found {len(members)} stokvel memberships:")
            for member in members:
                print(f"  Stokvel ID: {member[0]}, User ID: {member[1]}")
        else:
            print("No stokvel memberships found.")
            
    except Exception as e:
        print(f"Error checking stokvels: {e}")

if __name__ == "__main__":
    check_stokvels() 