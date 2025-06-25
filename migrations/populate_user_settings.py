import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def populate_user_settings():
    """Populates the user_settings table with default values for all existing users."""
    print("=== Populate User Settings Migration ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Get all existing users
                cur.execute("SELECT firebase_uid FROM users")
                users = cur.fetchall()

                # Insert default settings for each user
                for user in users:
                    user_id = user[0]
                    print(f"Setting up default settings for user: {user_id}")
                    
                    # Check if user already has settings
                    cur.execute("""
                        SELECT 1 FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                    
                    if not cur.fetchone():
                        # Insert default settings if none exist
                        cur.execute("""
                            INSERT INTO user_settings (
                                user_id,
                                email_notifications,
                                sms_notifications,
                                push_notifications,
                                receive_promotions,
                                receive_updates,
                                weekly_summary,
                                monthly_summary
                            ) VALUES (
                                %s, TRUE, FALSE, TRUE, TRUE, TRUE, FALSE, TRUE
                            )
                        """, (user_id,))
                        print(f"✅ Created default settings for user: {user_id}")
                    else:
                        print(f"⏩ User {user_id} already has settings configured")

                print(f"\n✅ Default settings ensured for {len(users)} users")
                conn.commit()
                print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    populate_user_settings() 