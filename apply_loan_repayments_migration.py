import psycopg2
import os

# Use provided DB connection info
DB_NAME = 'kasikash'
DB_USER = 'postgres'
DB_PASSWORD = 'dev_password'
DB_HOST = 'localhost'
DB_PORT = '5432'

migration_sql = '''
CREATE TABLE IF NOT EXISTS loan_repayments (
    id SERIAL PRIMARY KEY,
    loan_id INTEGER REFERENCES loan_requests(id) ON DELETE CASCADE,
    user_id VARCHAR(128) REFERENCES users(firebase_uid) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

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
        cur.execute(migration_sql)
        conn.commit()
        cur.close()
        conn.close()
        print('loan_repayments table migration applied successfully!')
    except Exception as e:
        print(f'Error applying migration: {e}')

if __name__ == '__main__':
    main() 