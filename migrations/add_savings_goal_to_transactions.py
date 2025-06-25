import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def add_savings_goal_column():
    """Adds the savings_goal_id column to the transactions table."""
    print("=== Add savings_goal_id to transactions Migration ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the column already exists
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='transactions' AND column_name='savings_goal_id'
                """)
                if cur.fetchone():
                    print("✅ Column 'savings_goal_id' already exists in 'transactions' table.")
                else:
                    print("Adding 'savings_goal_id' column to 'transactions' table...")
                    cur.execute("""
                        ALTER TABLE transactions
                        ADD COLUMN savings_goal_id INTEGER REFERENCES savings_goals(id) ON DELETE SET NULL;
                    """)
                    print("✅ Column 'savings_goal_id' added successfully.")

                conn.commit()
                print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    add_savings_goal_column() 