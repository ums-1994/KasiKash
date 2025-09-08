import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def create_diary_table():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS diary (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                event_name VARCHAR(255) NOT NULL,
                event_date DATE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            );
        ''')
        conn.commit()
        print("Diary table created or already exists.")
        cur.close()
    except Exception as e:
        print(f"Error creating diary table: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_diary_table() 