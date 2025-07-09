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

def add_show_tutorial_popups_column():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            ALTER TABLE user_settings
            ADD COLUMN IF NOT EXISTS show_tutorial_popups BOOLEAN DEFAULT TRUE;
        """)
        conn.commit()
        print("Successfully added show_tutorial_popups column to user_settings table")
    except Exception as e:
        print(f"Error adding column: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_show_tutorial_popups_column() 