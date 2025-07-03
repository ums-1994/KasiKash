#!/usr/bin/env python3
"""
Migration script to add missing columns to user_settings table
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_settings_columns():
    """Add missing columns to user_settings table"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        
        with conn.cursor() as cur:
            # Check if user_settings table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_settings'
                );
            """)
            
            if not cur.fetchone()[0]:
                print("Creating user_settings table...")
                cur.execute("""
                    CREATE TABLE user_settings (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) UNIQUE NOT NULL,
                        email_notifications BOOLEAN DEFAULT FALSE,
                        sms_notifications BOOLEAN DEFAULT FALSE,
                        weekly_summary BOOLEAN DEFAULT FALSE,
                        receive_promotions BOOLEAN DEFAULT FALSE,
                        reminders_enabled BOOLEAN DEFAULT TRUE,
                        stokvel_updates BOOLEAN DEFAULT TRUE,
                        profile_visible BOOLEAN DEFAULT TRUE,
                        activity_sharing BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✓ user_settings table created")
            else:
                print("user_settings table already exists")
                
                # Add missing columns if they don't exist
                columns_to_add = [
                    ('reminders_enabled', 'BOOLEAN DEFAULT TRUE'),
                    ('stokvel_updates', 'BOOLEAN DEFAULT TRUE'),
                    ('profile_visible', 'BOOLEAN DEFAULT TRUE'),
                    ('activity_sharing', 'BOOLEAN DEFAULT FALSE')
                ]
                
                for column_name, column_def in columns_to_add:
                    cur.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_name = 'user_settings' 
                            AND column_name = '{column_name}'
                        );
                    """)
                    
                    if not cur.fetchone()[0]:
                        print(f"Adding column {column_name}...")
                        cur.execute(f"ALTER TABLE user_settings ADD COLUMN {column_name} {column_def};")
                        print(f"✓ Added column {column_name}")
                    else:
                        print(f"Column {column_name} already exists")
            
            # Check if users table has language_preference column
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'language_preference'
                );
            """)
            
            if not cur.fetchone()[0]:
                print("Adding language_preference column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN language_preference VARCHAR(10) DEFAULT 'en';")
                print("✓ Added language_preference column to users table")
            else:
                print("language_preference column already exists in users table")
            
            # Check if users table has two_factor_enabled column
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'two_factor_enabled'
                );
            """)
            
            if not cur.fetchone()[0]:
                print("Adding two_factor_enabled column to users table...")
                cur.execute("ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;")
                print("✓ Added two_factor_enabled column to users table")
            else:
                print("two_factor_enabled column already exists in users table")
            
            conn.commit()
            print("\n✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Starting settings migration...")
    add_settings_columns()
    print("Migration finished!") 