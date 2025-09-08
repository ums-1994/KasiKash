import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Adds missing columns to the events table."""
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

        print("Altering events table...")

        # Add event_type column if it doesn't exist
        cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);")
        print("✅ Checked/Added 'event_type' column.")

        # Add stokvel_id column if it doesn't exist
        cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS stokvel_id INTEGER REFERENCES stokvels(id);")
        print("✅ Checked/Added 'stokvel_id' column.")

        # Add name column if it doesn't exist
        cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS name VARCHAR(255);")
        print("✅ Checked/Added 'name' column.")

        # Add target_date column if it doesn't exist
        cur.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS target_date DATE;")
        print("✅ Checked/Added 'target_date' column.")

        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration() 