import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_firebase_migration():
    print("Applying Firebase authentication migration...")
    conn = None
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Read and execute the migration SQL
        with open('migrations/update_users_table_for_firebase.sql', 'r') as file:
            sql = file.read()
            cur.execute(sql)

        conn.commit()
        print("Firebase authentication migration applied successfully!")

    except Exception as e:
        print(f"Error applying Firebase migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    apply_firebase_migration() 