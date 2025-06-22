import sqlite3
import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

def get_sqlite_connection():
    """Connect to the SQLite database"""
    return sqlite3.connect("expense.db")

def get_postgres_connection():
    """Connect to the PostgreSQL database"""
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'kasikash_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'dev_password'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )

def migrate_users(sqlite_conn, pg_conn):
    """Migrate users from SQLite to PostgreSQL"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all users from SQLite
    sqlite_cur.execute("SELECT username, email, password FROM user_login")
    users = sqlite_cur.fetchall()
    
    # Insert users into PostgreSQL
    for user in users:
        try:
            pg_cur.execute(
                "INSERT INTO users (username, email, password, created_at) VALUES (%s, %s, %s, %s)",
                (user[0], user[1], user[2], datetime.now())
            )
        except psycopg2.IntegrityError as e:
            print(f"Error inserting user {user[1]}: {e}")
            continue
    
    pg_conn.commit()
    print(f"Migrated {len(users)} users")

def migrate_expenses(sqlite_conn, pg_conn):
    """Migrate expenses from SQLite to PostgreSQL"""
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()
    
    # Get all expenses from SQLite
    sqlite_cur.execute("""
        SELECT ue.user_id, ue.pdate, ue.expense, ue.amount, ue.pdescription, ul.email 
        FROM user_expenses ue 
        JOIN user_login ul ON ue.user_id = ul.user_id
    """)
    expenses = sqlite_cur.fetchall()
    
    # Insert expenses into PostgreSQL
    for expense in expenses:
        try:
            # Get the new user_id from PostgreSQL
            pg_cur.execute("SELECT id FROM users WHERE email = %s", (expense[5],))
            new_user_id = pg_cur.fetchone()
            
            if new_user_id:
                pg_cur.execute(
                    """
                    INSERT INTO expenses 
                    (user_id, date, category, amount, notes, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (new_user_id[0], expense[1], expense[2], float(expense[3]), expense[4], datetime.now())
                )
        except Exception as e:
            print(f"Error inserting expense for user {expense[5]}: {e}")
            continue
    
    pg_conn.commit()
    print(f"Migrated {len(expenses)} expenses")

def main():
    try:
        # Connect to both databases
        sqlite_conn = get_sqlite_connection()
        pg_conn = get_postgres_connection()
        
        print("Starting migration...")
        
        # Migrate users first
        migrate_users(sqlite_conn, pg_conn)
        
        # Then migrate expenses
        migrate_expenses(sqlite_conn, pg_conn)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        # Close connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main() 