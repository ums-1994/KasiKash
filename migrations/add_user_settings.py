import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def add_settings_columns():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Add new columns to users table
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS profile_picture TEXT,
            ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS reminders_enabled BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS sms_notifications BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS weekly_summary BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS dark_mode BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS remember_me BOOLEAN DEFAULT TRUE;
        """)
        
        conn.commit()
        print("Successfully added settings columns to users table")
        
    except Exception as e:
        print(f"Error adding settings columns: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_settings_columns() 