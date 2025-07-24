import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MIGRATION_SQL = '''
ALTER TABLE financial_statement_analysis
    ALTER COLUMN user_id TYPE VARCHAR(64);
-- Optionally, add a foreign key constraint (uncomment if you want strict FK)
-- ALTER TABLE financial_statement_analysis
--     ADD CONSTRAINT fk_fsa_user FOREIGN KEY (user_id) REFERENCES users(firebase_uid);
'''

def run_migration():
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
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