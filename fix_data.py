from support import db_connection
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_data():
    print("Fixing database data...")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Delete invalid payout
                print("\nDeleting invalid payout...")
                cur.execute("DELETE FROM payouts WHERE stokvel_id NOT IN (SELECT id FROM stokvels)")
                print(f"Deleted {cur.rowcount} invalid payouts")

                # Add stokvel memberships for existing users
                print("\nAdding stokvel memberships...")
                # Get all users
                cur.execute("SELECT id FROM users")
                users = cur.fetchall()
                print(f"Found {len(users)} users")

                # Get all stokvels
                cur.execute("SELECT id FROM stokvels")
                stokvels = cur.fetchall()
                print(f"Found {len(stokvels)} stokvels")

                # Add memberships
                for user in users:
                    user_id = user[0]
                    for stokvel in stokvels:
                        stokvel_id = stokvel[0]
                        # Check if membership already exists
                        cur.execute("""
                            SELECT id FROM stokvel_members 
                            WHERE user_id = %s AND stokvel_id = %s
                        """, (user_id, stokvel_id))
                        if not cur.fetchone():
                            # Add membership
                            cur.execute("""
                                INSERT INTO stokvel_members (user_id, stokvel_id, role)
                                VALUES (%s, %s, 'member')
                            """, (user_id, stokvel_id))
                            print(f"Added membership: User {user_id} -> Stokvel {stokvel_id}")

                # Commit changes
                conn.commit()
                print("\nDatabase data fixed successfully!")

    except Exception as e:
        print(f"Error fixing database data: {str(e)}")
        import traceback
        print(f"Full error details:\n{traceback.format_exc()}")

def fix_stokvel_members_user_ids():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    print('Fixing stokvel_members.user_id values...')
    # Find all stokvel_members rows where user_id is not an integer (likely a firebase_uid)
    cur.execute("""
        SELECT id, user_id::text
        FROM stokvel_members
        WHERE user_id::text ~ '[A-Za-z]'
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} memberships to fix.")
    for sm_id, old_user_id in rows:
        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (old_user_id,))
        user_row = cur.fetchone()
        if user_row:
            correct_id = user_row[0]
            print(f"Updating stokvel_members.id={sm_id}: user_id {old_user_id} -> {correct_id}")
            cur.execute("UPDATE stokvel_members SET user_id = %s WHERE id = %s", (correct_id, sm_id))
        else:
            print(f"No matching user found for firebase_uid {old_user_id}, skipping stokvel_members.id={sm_id}")
    conn.commit()
    cur.close()
    conn.close()
    print('Done.')

if __name__ == "__main__":
    fix_database_data()
    fix_stokvel_members_user_ids() 