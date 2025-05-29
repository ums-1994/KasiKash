import sqlite3
from support import db_connection
import os
from dotenv import load_dotenv
import datetime

load_dotenv() # Load environment variables from .env file

def migrate():
    print("Starting database migration...")

    # SQLite connection
    sqlite_conn = sqlite3.connect('expense.db')
    sqlite_cur = sqlite_conn.cursor()

    # Migrate users
    print("Migrating users...")
    sqlite_cur.execute("SELECT email, password FROM user_login") # Corrected table name
    users = sqlite_cur.fetchall()

    with db_connection() as conn:
        with conn.cursor() as cursor:
            # Note: We don't insert the old SQLite 'id' since PostgreSQL SERIAL will generate a new one
            cursor.executemany(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                users
            )
            print(f"Migrated {len(users)} users")
        conn.commit() # Commit after inserting users

    # Migrate expenses
    print("Migrating expenses...")
    # Fetch user_id mapping from SQLite to PostgreSQL
    sqlite_cur.execute("SELECT user_id, email FROM user_login") # Assuming email can be used to map
    user_email_map = {email: user_id for user_id, email in sqlite_cur.fetchall()}

    sqlite_cur.execute("SELECT user_id, pdate, expense, amount, pdescription FROM user_expenses")
    expenses = sqlite_cur.fetchall()

    migrated_count = 0
    with db_connection() as conn:
        with conn.cursor() as cursor:
            for user_id_sqlite, pdate, expense, amount, pdescription in expenses:
                # Find the new user_id in PostgreSQL using email
                sqlite_cur.execute("SELECT email FROM user_login WHERE user_id = ?", (user_id_sqlite,))
                email = sqlite_cur.fetchone()[0]
                user_id_postgres = None
                # Look up the user_id in the PostgreSQL database based on email
                pg_user = support.execute_query("SELECT id FROM users WHERE email = %s", params=(email,), fetch=True)
                if pg_user:
                    user_id_postgres = pg_user[0][0]
                else:
                    print(f"Warning: Could not find PostgreSQL user for SQLite user_id {user_id_sqlite} with email {email}. Skipping expense.")
                    continue # Skip this expense if user not found

                # Use the current date and time for created_at
                created_at = datetime.datetime.now()

                cursor.execute(
                    "INSERT INTO expenses (user_id, date, category, amount, notes, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id_postgres, pdate, expense, amount, pdescription, created_at)
                )
                migrated_count += 1
        conn.commit() # Commit after inserting expenses
    print(f"Migrated {migrated_count} expenses")

    sqlite_conn.close()
    print("Database migration finished.")

if __name__ == "__main__":
    migrate() 