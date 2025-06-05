import psycopg2

def check_users():
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
        # Query all users
        cursor.execute("SELECT id, username, email FROM users ORDER BY id")
        users = cursor.fetchall()
        
        print("\nExisting users in the database:")
        print("ID | Username | Email")
        print("-" * 50)
        for user in users:
            print(f"{user[0]} | {user[1]} | {user[2]}")
            
    except Exception as e:
        print(f"Error checking users: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_users() 