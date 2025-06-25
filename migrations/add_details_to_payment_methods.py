import psycopg2
from psycopg2 import sql

# Update these with your actual DB credentials if needed
DB_NAME = 'kasikash'
DB_USER = 'postgres'
DB_PASSWORD = ''  # Add password if needed
DB_HOST = 'localhost'
DB_PORT = '5432'

def add_details_column():
    conn = None
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cur = conn.cursor()
        # Check if column exists
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='payment_methods' AND column_name='details';
        """)
        if not cur.fetchone():
            print("Adding 'details' column to payment_methods table...")
            cur.execute("""
                ALTER TABLE payment_methods ADD COLUMN details TEXT NOT NULL DEFAULT '{}';
            """)
            conn.commit()
            print("'details' column added.")
        else:
            print("'details' column already exists.")
        cur.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_details_column() 