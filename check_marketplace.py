#!/usr/bin/env python3
"""
Script to check and create marketplace_items table
"""

import psycopg2

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="localhost",
        database="kasikash_db",
        user="kasikash_user",
        password="kasikash_password"
    )

def check_and_create_table():
    """Check if marketplace_items table exists and create it if needed"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'marketplace_items'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("Creating marketplace_items table...")
            cur.execute("""
                CREATE TABLE marketplace_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    price_in_points INTEGER NOT NULL,
                    image_url VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("marketplace_items table created successfully!")
        else:
            print("marketplace_items table already exists")
        
        # Check current count
        cur.execute("SELECT COUNT(*) FROM marketplace_items")
        count = cur.fetchone()[0]
        print(f"Current marketplace items count: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_and_create_table() 