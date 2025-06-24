#!/usr/bin/env python3
import sqlite3

def create_all_tables():
    try:
        conn = sqlite3.connect('kasikash.db')
        cursor = conn.cursor()
        
        print("Creating all necessary tables...")
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firebase_uid TEXT UNIQUE,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                notification_preferences TEXT DEFAULT 'email',
                two_factor_enabled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created users table")
        
        # Create stokvels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stokvels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                purpose TEXT,
                monthly_contribution REAL,
                target_amount REAL,
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created stokvels table")
        
        # Create stokvel_members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stokvel_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stokvel_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stokvel_id) REFERENCES stokvels (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Created stokvel_members table")
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stokvel_id INTEGER,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                transaction_date DATE DEFAULT CURRENT_DATE,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (stokvel_id) REFERENCES stokvels (id)
            )
        ''')
        print("✅ Created transactions table")
        
        # Create savings_goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Created savings_goals table")
        
        # Create payment_methods table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT NOT NULL,
                account_number TEXT,
                bank_name TEXT,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print("✅ Created payment_methods table")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 All tables created successfully!")
        print("Your navigation links should now work!")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_all_tables() 