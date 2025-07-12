import psycopg2

FIREBASE_UID = 'Zs3IdijgugbiImwW1Tu7VdU5Rdy1'  # Replace with your actual Firebase UID
ROLE = 'member'  # or 'admin' if you want

conn = psycopg2.connect(
    dbname="kasikash_db",
    user="kasikash_user",
    password="test123",
    host="localhost"
)
cur = conn.cursor()

# Find all stokvels the user has contributed to
cur.execute("""
    SELECT DISTINCT stokvel_id FROM transactions
    WHERE user_id = %s AND stokvel_id IS NOT NULL
""", (FIREBASE_UID,))
contributed_stokvels = set(row[0] for row in cur.fetchall())

# Find all stokvels the user is already a member of
cur.execute("""
    SELECT stokvel_id FROM stokvel_members
    WHERE user_id = %s
""", (FIREBASE_UID,))
member_stokvels = set(row[0] for row in cur.fetchall())

# Find missing memberships
missing = contributed_stokvels - member_stokvels
print(f"Adding memberships for stokvels: {missing}")

for stokvel_id in missing:
    cur.execute(
        "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
        (stokvel_id, FIREBASE_UID, ROLE)
    )

# Update role to 'admin' for stokvels where the user is the creator
cur.execute("""
    UPDATE stokvel_members
    SET role = 'admin'
    WHERE user_id = %s AND stokvel_id IN (
        SELECT id FROM stokvels WHERE created_by = %s
    )
""", (FIREBASE_UID, FIREBASE_UID))

conn.commit()
cur.close()
conn.close()
print("Added missing memberships and updated admin roles!")