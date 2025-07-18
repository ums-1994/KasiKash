import psycopg2

# Database connection parameters (edit as needed)
DB_NAME = 'kasikash_db'
DB_USER = 'kasikash_user'
DB_PASSWORD = 'test123'
DB_HOST = 'localhost'

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

# 1. Get all stokvels with their creator's firebase_uid
cur.execute("""
    SELECT id, created_by FROM stokvels WHERE created_by IS NOT NULL
""")
stokvels = cur.fetchall()

added = 0
for stokvel_id, creator_uid in stokvels:
    # 2. Check if creator is already a member
    cur.execute(
        "SELECT 1 FROM stokvel_members WHERE stokvel_id = %s AND user_id = %s",
        (stokvel_id, creator_uid)
    )
    if not cur.fetchone():
        # 3. Add creator as admin member
        cur.execute(
            "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, 'admin')",
            (stokvel_id, creator_uid)
        )
        added += 1
        print(f"Added creator {creator_uid} as admin to stokvel {stokvel_id}")

conn.commit()
cur.close()
conn.close()
print(f"Done. Added {added} stokvel creator(s) as admin members.") 