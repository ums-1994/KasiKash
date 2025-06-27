import sys
import os

# Add current directory to path so we can import support
sys.path.append('.')
from support import execute_query

def create_missing_tables():
    """Create missing tables and fix schema issues"""
    print("Creating missing tables and fixing schema...")
    print("=" * 40)
    
    try:
        # Create transactions table
        print("Creating transactions table...")
        execute_query('insert', """
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                stokvel_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                transaction_date DATE NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stokvel_id) REFERENCES stokvels (id)
            )
        """)
        
        # Create savings_goals table
        print("Creating savings_goals table...")
        execute_query('insert', """
            CREATE TABLE IF NOT EXISTS savings_goals (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline DATE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create payment_methods table
        print("Creating payment_methods table...")
        execute_query('insert', """
            CREATE TABLE IF NOT EXISTS payment_methods (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                card_number_last_four TEXT NOT NULL,
                card_type TEXT NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fix stokvel_members table - change user_id to TEXT
        print("Fixing stokvel_members table...")
        # First, create a backup table
        execute_query('insert', """
            CREATE TABLE IF NOT EXISTS stokvel_members_backup AS SELECT * FROM stokvel_members
        """)
        
        # Drop the old table
        execute_query('insert', "DROP TABLE stokvel_members")
        
        # Create the new table with correct schema
        execute_query('insert', """
            CREATE TABLE stokvel_members (
                id SERIAL PRIMARY KEY,
                stokvel_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stokvel_id) REFERENCES stokvels (id)
            )
        """)
        
        # Add missing columns to users table
        print("Adding missing columns to users table...")
        try:
            execute_query('insert', "ALTER TABLE users ADD COLUMN notification_preferences TEXT DEFAULT 'email'")
        except:
            print("notification_preferences column already exists or couldn't be added")
            
        try:
            execute_query('insert', "ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE")
        except:
            print("two_factor_enabled column already exists or couldn't be added")
        
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_missing_tables() 