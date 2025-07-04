import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def create_transactions_table():
    print("=== Creating 'transactions' table ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'transactions'
                    );
                """)
                exists = cur.fetchone()[0]
                if exists:
                    print("✅ Table 'transactions' already exists.")
                    return
                print("Creating 'transactions' table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(128) NOT NULL REFERENCES users(firebase_uid) ON DELETE CASCADE,
                        stokvel_id INTEGER REFERENCES stokvels(id) ON DELETE SET NULL,
                        amount DECIMAL(10, 2) NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        description VARCHAR(255),
                        transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
                        status VARCHAR(50),
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        savings_goal_id INTEGER REFERENCES savings_goals(id) ON DELETE SET NULL
                    );
                """)
                conn.commit()
                print("✅ 'transactions' table created successfully.")
    except Exception as e:
        print(f"❌ Error creating 'transactions' table: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

def main():
    create_transactions_table()

if __name__ == "__main__":
    main() 