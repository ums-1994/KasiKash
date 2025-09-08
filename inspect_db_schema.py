import sys
from support import db_connection

def inspect_users_table():
    """Connects to the database and prints the schema of the users table."""
    print("=== Inspecting 'users' table schema ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'users'
                    ORDER BY ordinal_position;
                """
                cur.execute(query)
                columns = cur.fetchall()
                
                if not columns:
                    print("Could not find the 'users' table.")
                    return

                print("\nColumns in 'users' table:")
                print("-" * 40)
                print(f"{'Column Name':<25} {'Data Type':<15} {'Nullable'}")
                print("-" * 40)
                for col in columns:
                    print(f"{col[0]:<25} {col[1]:<15} {col[2]}")
                print("-" * 40)

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn and not conn.closed:
            conn.rollback()

if __name__ == "__main__":
    inspect_users_table() 