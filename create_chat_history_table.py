#!/usr/bin/env python3
"""
Script to create the chat_history table for the KasiKash chatbot
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import support

def create_chat_history_table():
    """Create the chat_history table if it doesn't exist"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        mode VARCHAR(50) DEFAULT 'ai',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE
    );
    """
    
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()
                print("✅ chat_history table created successfully!")
                
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'chat_history'
                    );
                """)
                exists = cur.fetchone()[0]
                
                if exists:
                    print("✅ chat_history table verified and ready to use!")
                else:
                    print("❌ chat_history table creation failed!")
                    
    except Exception as e:
        print(f"❌ Error creating chat_history table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Creating chat_history table for KasiKash chatbot...")
    success = create_chat_history_table()
    
    if success:
        print("\n🎉 Chatbot database setup complete!")
        print("The chatbot should now work properly with chat history persistence.")
    else:
        print("\n❌ Chatbot database setup failed!")
        print("Please check your database connection and try again.") 