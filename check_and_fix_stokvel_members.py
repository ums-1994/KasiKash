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

def check_stokvel_members():
    """Check stokvel_members table for issues"""
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
                print("=== CHECKING STOKVEL MEMBERS ===")
                
                # Check table structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'stokvel_members' 
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()
                print("stokvel_members table structure:")
                for col_name, data_type, nullable in columns:
                    print(f"  - {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
                
                # Count total members
                cur.execute("SELECT COUNT(*) FROM stokvel_members")
                total_members = cur.fetchone()[0]
                print(f"\nTotal stokvel members: {total_members}")
                
                # Check for null user_id values
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE user_id IS NULL")
                null_users = cur.fetchone()[0]
                print(f"Members with null user_id: {null_users}")
                
                if null_users > 0:
                    print("\nMembers with null user_id:")
                    cur.execute("""
                        SELECT sm.id, sm.stokvel_id, s.name, sm.user_id, sm.joined_at
                        FROM stokvel_members sm
                        JOIN stokvels s ON sm.stokvel_id = s.id
                        WHERE sm.user_id IS NULL
                    """)
                    null_members = cur.fetchall()
                    for member_id, stokvel_id, stokvel_name, user_id, joined_at in null_members:
                        print(f"  - Member ID: {member_id}, Stokvel: {stokvel_name} (ID: {stokvel_id}), Joined: {joined_at}")
                
                # Check for valid user_id values
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE user_id IS NOT NULL")
                valid_users = cur.fetchone()[0]
                print(f"Members with valid user_id: {valid_users}")
                
                if valid_users > 0:
                    print("\nSample valid members:")
                    cur.execute("""
                        SELECT sm.id, sm.stokvel_id, s.name, sm.user_id, sm.joined_at
                        FROM stokvel_members sm
                        JOIN stokvels s ON sm.stokvel_id = s.id
                        WHERE sm.user_id IS NOT NULL
                        LIMIT 5
                    """)
                    valid_members = cur.fetchall()
                    for member_id, stokvel_id, stokvel_name, user_id, joined_at in valid_members:
                        print(f"  - Member ID: {member_id}, Stokvel: {stokvel_name} (ID: {stokvel_id}), User: {user_id}, Joined: {joined_at}")
                
    finally:
        conn.close()

def fix_stokvel_members():
    """Fix stokvel_members table by removing null user_id entries"""
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
                print("\n=== FIXING STOKVEL MEMBERS ===")
                
                # Delete members with null user_id
                cur.execute("DELETE FROM stokvel_members WHERE user_id IS NULL")
                deleted_count = cur.rowcount
                print(f"✓ Deleted {deleted_count} members with null user_id")
                
                # Verify fix
                cur.execute("SELECT COUNT(*) FROM stokvel_members WHERE user_id IS NULL")
                remaining_null = cur.fetchone()[0]
                print(f"Remaining members with null user_id: {remaining_null}")
                
                conn.commit()
                print("✓ Stokvel members fixed successfully!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    check_stokvel_members()
    fix_stokvel_members()

if __name__ == '__main__':
    main() 