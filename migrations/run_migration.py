import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def run_migration():
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
        # Read and execute the migration file
        with open('migrations/create_loan_requests_table.sql', 'r') as f:
            migration_sql = f.read()
            cursor.execute(migration_sql)
        
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error running migration: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration() 