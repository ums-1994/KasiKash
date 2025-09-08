import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_card_id_column():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'kasikash_db'),
            user=os.getenv('DB_USER', 'kasikash_user'),
            password=os.getenv('DB_PASSWORD', 'test123'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        # Check if card_id already exists
        cur.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_name='reward_transactions' AND column_name='card_id'
        """)
        if cur.fetchone():
            print("✅ Column 'card_id' already exists in 'reward_transactions' table.")
        else:
            print("Adding 'card_id' column to 'reward_transactions' table...")
            cur.execute("""
                ALTER TABLE reward_transactions
                ADD COLUMN card_id INTEGER REFERENCES virtual_reward_cards(id)
            """)
            print("✅ Column 'card_id' added successfully.")
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"❌ Error adding card_id column: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_card_id_column() 