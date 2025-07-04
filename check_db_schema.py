import support

def check_db_connection():
    print("Checking database connection...")
    try:
        if support.verify_db_connection():
            print("Database connection successful!")
        else:
            print("Database connection failed.")
    except Exception as e:
        print(f"Database connection error: {e}")

def check_transactions_table():
    try:
        with support.db_connection() as conn:
            with conn.cursor() as cur:
                # Check if table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'transactions'
                    );
                """)
                exists = cur.fetchone()[0]
                if not exists:
                    print("Table 'transactions' does NOT exist.")
                    return
                print("Table 'transactions' exists.")
                # Get columns and types
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'transactions'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print("Columns in 'transactions':")
                for col, dtype in columns:
                    print(f"  - {col}: {dtype}")
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == '__main__':
    check_db_connection()
    check_transactions_table() 