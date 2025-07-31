#!/usr/bin/env python3
"""
Script to check the structure of the events table.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from support import db_connection

def check_events_table():
    """Check the structure of the events table."""
    
    with db_connection() as conn:
        with conn.cursor() as cur:
            
            # Check if events table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'events'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print("❌ Events table does not exist!")
                return
            
            print("✅ Events table exists")
            
            # Get table structure
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'events'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            print("\n📋 Events table structure:")
            print("Column Name | Data Type | Nullable")
            print("-" * 40)
            for col in columns:
                print(f"{col[0]:<12} | {col[1]:<10} | {col[2]}")
            
            # Check for sample data
            cur.execute("SELECT COUNT(*) FROM events")
            count = cur.fetchone()[0]
            print(f"\n📊 Total events: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM events LIMIT 3")
                sample_data = cur.fetchall()
                print("\n📝 Sample data:")
                for row in sample_data:
                    print(row)

if __name__ == "__main__":
    check_events_table() 