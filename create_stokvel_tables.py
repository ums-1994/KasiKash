import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_stokvel_tables():
    # Connect to the database
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Create stokvels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stokvels (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                monthly_contribution DECIMAL(10,2),
                total_pool DECIMAL(10,2) DEFAULT 0,
                target_amount DECIMAL(10,2),
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER REFERENCES users(id)
            )
        """)

        # Create stokvel_members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stokvel_members (
                id SERIAL PRIMARY KEY,
                stokvel_id INTEGER REFERENCES stokvels(id),
                user_id INTEGER REFERENCES users(id),
                role VARCHAR(20) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stokvel_id, user_id)
            )
        """)

        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                stokvel_id INTEGER REFERENCES stokvels(id),
                user_id INTEGER REFERENCES users(id),
                type VARCHAR(20) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        print("Stokvel tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_stokvel_tables() 