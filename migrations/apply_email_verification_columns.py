import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_email_verification_migration():
    print("Applying email verification columns migration...")
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
        with open('migrations/add_email_verification_columns.sql', 'r') as file:
            sql = file.read()
            cur.execute(sql)

        conn.commit()
        print("Email verification columns added successfully!")

    except Exception as e:
        print(f"Error applying email verification migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    apply_email_verification_migration() 