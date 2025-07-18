import psycopg2

def create_test_user():
    # Connect to the database
    conn = psycopg2.connect(
        dbname='kasikash',
        user='postgres',
        password='12345',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()

    try:
        # Create a test user
        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
            RETURNING id
        """, ('testuser', 'test@example.com', 'password123'))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Test user created successfully with ID: {user_id}")
        print("Username: testuser")
        print("Email: test@example.com")
        print("Password: password123")
            
    except Exception as e:
        print(f"Error creating test user: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_test_user() 