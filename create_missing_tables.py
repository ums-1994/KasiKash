#!/usr/bin/env python3
"""
Script to create missing database tables that are causing errors.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from support import db_connection

def create_missing_tables():
    """Create missing database tables."""
    
    with db_connection() as conn:
        with conn.cursor() as cur:
            
            # Create diary table
            print("Creating diary table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS diary (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create stokvel_chat_messages table
            print("Creating stokvel_chat_messages table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stokvel_chat_messages (
                    id SERIAL PRIMARY KEY,
                    stokvel_id INTEGER NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stokvel_id) REFERENCES stokvels(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            print("✅ All missing tables created successfully!")

if __name__ == "__main__":
    create_missing_tables() 