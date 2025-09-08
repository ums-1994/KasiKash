import psycopg2
import os

# Update these with your actual database connection details
DB_NAME = os.getenv('DB_NAME', 'your_db_name')
DB_USER = os.getenv('DB_USER', 'your_db_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_db_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    "user" VARCHAR(255) NOT NULL,
    target VARCHAR(255),
    amount NUMERIC,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def create_audit_logs_table():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
        cur.close()
        conn.close()
        print('audit_logs table created or already exists.')
    except Exception as e:
        print('Error creating audit_logs table:', e)

if __name__ == '__main__':
    create_audit_logs_table() 