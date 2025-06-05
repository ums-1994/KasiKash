import psycopg2

def create_tables():
    # Connect to the database
    conn = psycopg2.connect(
        dbname='kasikash',
        user='postgres',
        password='12345',
        host='localhost',
        port='5432'
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        # Read and execute the schema.sql file
        with open('schema.sql', 'r') as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)
        
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_tables() 