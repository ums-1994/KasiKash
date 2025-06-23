#!/usr/bin/env python3
"""
Migration script to create the 'notifications' table.
Requires postgres superuser access.
"""

import os
import psycopg2
from dotenv import load_dotenv
import getpass

# Load environment variables
load_dotenv()

def create_notifications_table():
    """Creates the notifications table in the database."""
    
    print("=== Notifications Table Migration ===")
    print("This script will create a 'notifications' table to store in-app alerts.")
    print("You need superuser access to run this migration.\n")
    
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

        # Check if the table already exists
        cursor.execute("SELECT to_regclass('public.notifications')")
        if cursor.fetchone()[0]:
            print("✅ Table 'notifications' already exists.")
        else:
            print("Creating 'notifications' table...")
            cursor.execute("""
                CREATE TABLE notifications (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL REFERENCES users(firebase_uid),
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    link_url VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ 'notifications' table created successfully.")
            
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_notifications_table() 