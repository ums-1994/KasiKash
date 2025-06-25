import psycopg2

DB_NAME = 'kasikash'
DB_USER = 'postgres'
DB_PASSWORD = 'dev_password'
DB_HOST = 'localhost'
DB_PORT = '5432'

migration_steps = [
    # 1. Add a temporary column for the Firebase UID
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);",
    # 2. Copy the Firebase UID from users into the new column
    "UPDATE transactions t SET temp_user_id = u.firebase_uid FROM users u WHERE t.user_id::text = u.id::text;",
    # 3. Drop the old foreign key constraint if it exists
    "ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;",
    # 4. Drop the old user_id column
    "ALTER TABLE transactions DROP COLUMN user_id;",
    # 5. Rename the temp_user_id column to user_id
    "ALTER TABLE transactions RENAME COLUMN temp_user_id TO user_id;",
    # 6. Add the new foreign key constraint
    "ALTER TABLE transactions ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;"
]

def main():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        for step in migration_steps:
            print(f"Executing: {step}")
            try:
                cur.execute(step)
                conn.commit()
            except Exception as e:
                print(f"Step failed (may be ok if already applied): {e}")
                conn.rollback()
        cur.close()
        conn.close()
        print('Migration to convert transactions.user_id to Firebase UID completed!')
    except Exception as e:
        print(f'Error applying migration: {e}')

if __name__ == '__main__':
    main() 