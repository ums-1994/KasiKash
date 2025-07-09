import psycopg2
import os

DB_NAME = os.getenv('DB_NAME', 'your_db_name')
DB_USER = os.getenv('DB_USER', 'your_db_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_db_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def print_db_schema_info():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        with conn:
            with conn.cursor() as cur:
                print('All tables:')
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' ORDER BY table_name
                """)
                for row in cur.fetchall():
                    print(' -', row[0])
                print('\nForeign keys for chat_members:')
                cur.execute("""
                    SELECT
                        tc.constraint_name, kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.table_name = 'chat_members' AND tc.constraint_type = 'FOREIGN KEY';
                """)
                for row in cur.fetchall():
                    print(f" - Constraint: {row[0]}, Column: {row[1]}, References: {row[2]}({row[3]})")
    finally:
        conn.close()

if __name__ == '__main__':
    print_db_schema_info() 