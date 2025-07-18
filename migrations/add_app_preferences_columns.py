#!/usr/bin/env python3
"""
Migration script to add columns for App Preferences to the users table.
Requires postgres superuser access.
"""

import os
import psycopg2
from dotenv import load_dotenv
import getpass

# Load environment variables
load_dotenv()

def add_app_preference_columns():
    """Adds weekly_summary and reminders_enabled columns to the users table."""
    
    print("=== App Preferences Migration ===")
    print("This script will add 'weekly_summary' and 'reminders_enabled' columns.")
    print("You need superuser access to run this migration.\n")
    
    # Get superuser credentials
    superuser_name = input("Enter your PostgreSQL superuser name (e.g., postgres): ")
    superuser_password = getpass.getpass(f"Enter password for user '{superuser_name}': ")
    
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': superuser_name,
        'password': superuser_password,
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # --- Check and add weekly_summary column ---
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'weekly_summary'")
        if cursor.fetchone():
            print("✅ Column 'weekly_summary' already exists.")
        else:
            print("Adding column 'weekly_summary'...")
            cursor.execute("ALTER TABLE users ADD COLUMN weekly_summary BOOLEAN DEFAULT TRUE")
            cursor.execute("UPDATE users SET weekly_summary = TRUE WHERE weekly_summary IS NULL")
            print("✅ 'weekly_summary' column added and defaults set.")

        # --- Check and add reminders_enabled column ---
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'reminders_enabled'")
        if cursor.fetchone():
            print("✅ Column 'reminders_enabled' already exists.")
        else:
            print("Adding column 'reminders_enabled'...")
            cursor.execute("ALTER TABLE users ADD COLUMN reminders_enabled BOOLEAN DEFAULT TRUE")
            cursor.execute("UPDATE users SET reminders_enabled = TRUE WHERE reminders_enabled IS NULL")
            print("✅ 'reminders_enabled' column added and defaults set.")
            
        conn.commit()
        
        print("\n🎉 Migration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    add_app_preference_columns() 