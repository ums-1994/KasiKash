import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def update_database_schema():
    """
    Connects to the PostgreSQL database and applies the SQL schema.
    """
    conn = None
    try:
        # Get database connection parameters from environment variables
        dbname = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT')

        # Establish the connection
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print("Successfully connected to the database.")

        # Create a cursor
        cur = conn.cursor()

        # Read the SQL schema file
        with open('schema.sql', 'r') as f:
            sql_script = f.read()

        # Execute the SQL script
        cur.execute(sql_script)
        print("Successfully executed the schema script.")

        # Commit the changes
        conn.commit()
        print("Database schema updated successfully.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error while connecting to or updating PostgreSQL: {error}")
    finally:
        # Close the connection
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    update_database_schema() 