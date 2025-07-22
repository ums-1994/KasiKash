import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'kasikash_db')
DB_USER = os.getenv('DB_USER', 'kasikash_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

MIGRATION_SQL = '''
ALTER TABLE financial_statement_analysis
    ALTER COLUMN user_id TYPE VARCHAR(64);
-- Optionally, add a foreign key constraint (uncomment if you want strict FK)
-- ALTER TABLE financial_statement_analysis
--     ADD CONSTRAINT fk_fsa_user FOREIGN KEY (user_id) REFERENCES users(firebase_uid);
'''

def run_migration():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        print('Running migration to fix user_id type in financial_statement_analysis...')
        cur.execute(MIGRATION_SQL)
        conn.commit()
        cur.close()
        conn.close()
        print('✅ Migration completed successfully!')
    except Exception as e:
        print(f'❌ Migration failed: {e}')
        if 'conn' in locals() and conn:
            conn.rollback()
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    run_migration() 