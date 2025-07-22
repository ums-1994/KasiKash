import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def run_migration():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'kasikash_db'),
            user=os.getenv('DB_USER', 'kasikash_user'),
            password=os.getenv('DB_PASSWORD', 'test123'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()

        # Check if the user_id column is already VARCHAR
        cur.execute("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'diary' AND column_name = 'user_id';
        """)
        result = cur.fetchone()
        if result and result[0] == 'character varying':
            print("✅ Diary table user_id is already VARCHAR. Migration not needed.")
            return

        print("Starting diary table migration...")

        # Add temporary column if it doesn't exist
        cur.execute("""
            ALTER TABLE diary
            ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
        """)
        print("1. temp_user_id column added.")

        # Update the temporary column with firebase_uid from users
        cur.execute("""
            UPDATE diary d
            SET temp_user_id = u.firebase_uid
            FROM users u
            WHERE d.user_id::text = u.id::text;
        """)
        print("2. temp_user_id populated with firebase_uid.")

        # Drop the old foreign key constraint if it exists
        cur.execute("""
            ALTER TABLE diary
            DROP CONSTRAINT IF EXISTS diary_user_id_fkey;
        """)
        print("3. Dropped old foreign key constraint.")

        # Drop the old user_id column
        cur.execute("""
            ALTER TABLE diary
            DROP COLUMN user_id;
        """)
        print("4. Dropped old user_id column.")

        # Rename temp column to user_id
        cur.execute("""
            ALTER TABLE diary
            RENAME COLUMN temp_user_id TO user_id;
        """)
        print("5. Renamed temp_user_id to user_id.")

        # Add new foreign key constraint
        cur.execute("""
            ALTER TABLE diary
            ADD CONSTRAINT diary_user_id_fkey
            FOREIGN KEY (user_id)
            REFERENCES users(firebase_uid)
            ON DELETE CASCADE;
        """)
        print("6. Added new foreign key constraint.")

        conn.commit()
        print("✅ Successfully migrated diary table to use firebase_uid")

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error during migration: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration() 