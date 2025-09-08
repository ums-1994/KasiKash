#!/usr/bin/env python3
"""
Migration script to add language_preference column to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import support

def add_language_preference_column():
    """Add language_preference column to users table"""
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if column already exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'language_preference'
                """)
                
                if cur.fetchone():
                    print("Column 'language_preference' already exists in users table")
                    return True
                
                # Add the language_preference column
                cur.execute("""
                    ALTER TABLE users 
                    ADD COLUMN language_preference VARCHAR(10) DEFAULT 'en'
                """)
                
                conn.commit()
                print("Successfully added 'language_preference' column to users table")
                return True
                
    except Exception as e:
        print(f"Error adding language_preference column: {e}")
        return False

if __name__ == "__main__":
    print("Adding language_preference column to users table...")
    success = add_language_preference_column()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1) 