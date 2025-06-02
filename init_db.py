import support
from dotenv import load_dotenv
import os

load_dotenv()

def init_db():
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Create users table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(30) NOT NULL,
                        email VARCHAR(30) NOT NULL UNIQUE,
                        password VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create expenses table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        date DATE NOT NULL,
                        expense VARCHAR(10) NOT NULL,
                        amount DECIMAL(10,2) NOT NULL,
                        note VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    );
                """)
                
                conn.commit()
                print("Database tables created successfully!")
                
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db() 