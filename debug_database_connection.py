import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables (same as Flask app)
load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def debug_database():
    print(f"=== DATABASE CONNECTION DEBUG ===")
    print(f"DB_NAME: {DB_NAME}")
    print(f"DB_USER: {DB_USER}")
    print(f"DB_HOST: {DB_HOST}")
    print(f"DB_PORT: {DB_PORT}")
    
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print(f"✅ Successfully connected to database: {DB_NAME}")
        
        with conn:
            with conn.cursor() as cur:
                # Test the exact same query as Flask app
                print("\n=== TESTING EXACT FLASK QUERY ===")
                cur.execute("SELECT cr.id FROM chat_rooms cr WHERE cr.stokvel_id = %s", (7,))
                result = cur.fetchall()
                print(f"Query: SELECT cr.id FROM chat_rooms cr WHERE cr.stokvel_id = 7")
                print(f"Result: {result}")
                print(f"Result type: {type(result)}")
                print(f"Result length: {len(result) if result else 0}")
                
                # Check all chat rooms
                print("\n=== ALL CHAT ROOMS ===")
                cur.execute("SELECT id, stokvel_id, admin_user_id FROM chat_rooms ORDER BY id")
                chat_rooms = cur.fetchall()
                print(f"Total chat rooms: {len(chat_rooms)}")
                for room in chat_rooms:
                    print(f"  - ChatRoom ID: {room[0]}, Stokvel ID: {room[1]}, Admin: {room[2]}")
                
                # Check stokvels table
                print("\n=== ALL STOKVELS ===")
                cur.execute("SELECT id, name FROM stokvels ORDER BY id")
                stokvels = cur.fetchall()
                print(f"Total stokvels: {len(stokvels)}")
                for stokvel in stokvels:
                    print(f"  - Stokvel ID: {stokvel[0]}, Name: {stokvel[1]}")
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")

if __name__ == '__main__':
    debug_database() 