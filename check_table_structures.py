import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'kasikash_db')
DB_USER = os.getenv('DB_USER', 'kasikash_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'kasikash_password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def check_table_structures():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    
    try:
        with conn:
            with conn.cursor() as cur:
                # Check stokvels table structure
                print("=== STOKVELS TABLE STRUCTURE ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'stokvels' 
                    ORDER BY ordinal_position
                """)
                stokvel_columns = cur.fetchall()
                for col_name, data_type, nullable in stokvel_columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Check chats table structure
                print("\n=== CHATS TABLE STRUCTURE ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'chats' 
                    ORDER BY ordinal_position
                """)
                chat_columns = cur.fetchall()
                for col_name, data_type, nullable in chat_columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Check chat_members table structure
                print("\n=== CHAT_MEMBERS TABLE STRUCTURE ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_members' 
                    ORDER BY ordinal_position
                """)
                member_columns = cur.fetchall()
                for col_name, data_type, nullable in member_columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Check chat_messages table structure
                print("\n=== CHAT_MESSAGES TABLE STRUCTURE ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'chat_messages' 
                    ORDER BY ordinal_position
                """)
                message_columns = cur.fetchall()
                for col_name, data_type, nullable in message_columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
    finally:
        conn.close()

if __name__ == '__main__':
    check_table_structures() 