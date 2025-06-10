import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('DB_NAME', 'kasikash_db')
DB_USER = os.getenv('DB_USER', 'kasikash_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'kasikash_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def init_database():
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    try:
        # Create database if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"Database {DB_NAME} created successfully")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        cur.close()
        conn.close()

    # Connect to the new database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()

    try:
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(30) NOT NULL UNIQUE,
                email VARCHAR(30) NOT NULL UNIQUE,
                password VARCHAR(100) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create stokvels table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stokvels (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                monthly_contribution DECIMAL(10,2) NOT NULL,
                total_pool DECIMAL(10,2) DEFAULT 0,
                target_amount DECIMAL(10,2),
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create stokvel_members table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stokvel_members (
                id SERIAL PRIMARY KEY,
                stokvel_id INTEGER REFERENCES stokvels(id),
                user_id INTEGER REFERENCES users(id),
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stokvel_id, user_id)
            )
        """)

        # Create savings_goals table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                name VARCHAR(100) NOT NULL,
                target_amount DECIMAL(10,2) NOT NULL,
                current_amount DECIMAL(10,2) DEFAULT 0,
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create transactions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                stokvel_id INTEGER REFERENCES stokvels(id),
                amount DECIMAL(10,2) NOT NULL,
                type VARCHAR(20) NOT NULL,
                description TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'completed'
            )
        """)

        # Create payment_methods table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payment_methods (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                type VARCHAR(50) NOT NULL,
                details JSONB,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("Tables created successfully")

    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_database() 