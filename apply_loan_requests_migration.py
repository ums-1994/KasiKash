import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def apply_migration():
    """Applies the SQL migration to create the loan_requests table."""
    try:
        # Database connection details from environment variables
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Read the SQL command from the migration file
        with open('migrations/create_loan_requests_table.sql', 'r') as f:
            sql_command = f.read()

        # Execute the SQL command
        cur.execute(sql_command)
        conn.commit()

        print("Successfully applied loan_requests migration.")

    except Exception as e:
        print(f"Error during migration: {e}")

    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

if __name__ == "__main__":
    apply_migration() 