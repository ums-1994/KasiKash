import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def add_link_url_column():
    """Adds the link_url column to the notifications table if it doesn't exist."""
    print("=== Add link_url to notifications Migration ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the column already exists
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='notifications' AND column_name='link_url'
                """)
                if cur.fetchone():
                    print("✅ Column 'link_url' already exists in 'notifications' table.")
                else:
                    print("Adding 'link_url' column to 'notifications' table...")
                    cur.execute("""
                        ALTER TABLE notifications
                        ADD COLUMN link_url VARCHAR(255);
                    """)
                    print("✅ Column 'link_url' added successfully.")
                
                # Add 'type' column as well, as it's in the create_notification function
                cur.execute("""
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='notifications' AND column_name='type'
                """)
                if cur.fetchone():
                    print("✅ Column 'type' already exists in 'notifications' table.")
                else:
                    print("Adding 'type' column to 'notifications' table...")
                    cur.execute("""
                        ALTER TABLE notifications
                        ADD COLUMN type VARCHAR(50) DEFAULT 'general';
                    """)
                    print("✅ Column 'type' added successfully.")

            conn.commit()
            print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    add_link_url_column() 