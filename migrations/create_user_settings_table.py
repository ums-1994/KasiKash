import sys
import os
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def create_user_settings_table():
    """
    Creates the user_settings table and populates it with default
    settings for existing users.
    """
    print("=== Create user_settings table Migration ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the table already exists
                cur.execute("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name='user_settings'
                """)
                if cur.fetchone():
                    print("✅ Table 'user_settings' already exists.")
                else:
                    print("Creating 'user_settings' table...")
                    cur.execute("""
                        CREATE TABLE user_settings (
                            user_id VARCHAR(255) PRIMARY KEY REFERENCES users(firebase_uid) ON DELETE CASCADE,
                            email_notifications BOOLEAN DEFAULT TRUE,
                            sms_notifications BOOLEAN DEFAULT FALSE,
                            push_notifications BOOLEAN DEFAULT TRUE,
                            receive_promotions BOOLEAN DEFAULT TRUE,
                            receive_updates BOOLEAN DEFAULT TRUE,
                            weekly_summary BOOLEAN DEFAULT FALSE,
                            monthly_summary BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    print("✅ 'user_settings' table created successfully.")

                print("Populating settings for existing users...")
                # Get all existing user IDs from the users table
                cur.execute("SELECT firebase_uid FROM users")
                users = cur.fetchall()

                # Insert default settings for each user if they don't exist
                for user in users:
                    user_id = user[0]
                    cur.execute("""
                        INSERT INTO user_settings (user_id)
                        VALUES (%s)
                        ON CONFLICT (user_id) DO NOTHING;
                    """, (user_id,))
                
                print(f"✅ Default settings ensured for {len(users)} users.")

            conn.commit()
            print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    create_user_settings_table() 