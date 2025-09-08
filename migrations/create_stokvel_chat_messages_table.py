from support import db_connection

def run_migration():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS stokvel_chat_messages (
                    id SERIAL PRIMARY KEY,
                    stokvel_id INTEGER NOT NULL REFERENCES stokvels(id) ON DELETE CASCADE,
                    user_id VARCHAR(128) NOT NULL REFERENCES users(firebase_uid) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            conn.commit()

if __name__ == "__main__":
    run_migration() 