import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "kasikash_db"),
        user=os.getenv("DB_USER", "kasikash_user"),
        password=os.getenv("DB_PASSWORD", "yourpassword"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Alter user_id to integer, casting existing values
        cur.execute("""
            ALTER TABLE stokvel_members
            ALTER COLUMN user_id TYPE INTEGER USING user_id::integer;
        """)
        conn.commit()
        print("Successfully changed stokvel_members.user_id to INTEGER.")
    except Exception as e:
        print(f"Error updating user_id column: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 