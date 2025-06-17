#!/usr/bin/env python3
"""
Database migration script to add missing columns to existing tables
"""

import support
import sqlite3

def main():
    print("🔄 Running database migration...")
    
    # Check current database structure
    try:
        with support.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print(f"Current users table columns: {[col[1] for col in columns]}")
    except Exception as e:
        print(f"Error checking current structure: {e}")
    
    # Initialize database (this will run the migration)
    success = support.init_database()
    
    if success:
        print("✅ Database migration completed successfully!")
        
        # Check new database structure
        try:
            with support.db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(users)")
                columns = cursor.fetchall()
                print(f"Updated users table columns: {[col[1] for col in columns]}")
        except Exception as e:
            print(f"Error checking updated structure: {e}")
    else:
        print("❌ Database migration failed!")

if __name__ == "__main__":
    main() 