import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_stokvel_members_user_ids():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    print('Fixing stokvel_members.user_id for all members with matching email in users table...')
    # Find all stokvel_members with user_id NULL but email present
    cur.execute("""
        SELECT sm.id, sm.email, u.id as user_id
        FROM stokvel_members sm
        JOIN users u ON sm.email = u.email
        WHERE sm.user_id IS NULL
    """)
    updates = cur.fetchall()
    count = 0
    for row in updates:
        stokvel_member_id = row[0]
        email = row[1]
        user_id = row[2]
        cur.execute("UPDATE stokvel_members SET user_id = %s WHERE id = %s", (user_id, stokvel_member_id))
        print(f"Updated stokvel_member id {stokvel_member_id} ({email}) to user_id {user_id}")
        count += 1
    conn.commit()
    print(f"Done. Updated {count} stokvel_members rows.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_stokvel_members_user_ids() 