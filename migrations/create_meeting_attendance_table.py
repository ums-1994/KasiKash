import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from support import db_connection

def create_meeting_attendance_table():
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS meeting_attendance (
        id SERIAL PRIMARY KEY,
        meeting_name VARCHAR(255),
        meeting_date DATE,
        present_count INTEGER,
        absent_count INTEGER
    );
    '''
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
        print("Successfully created meeting_attendance table.")
    except Exception as e:
        print(f"Error creating meeting_attendance table: {str(e)}")

if __name__ == "__main__":
    create_meeting_attendance_table() 