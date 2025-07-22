import psycopg2

conn = psycopg2.connect(
    dbname="kasikash_db",
    user="kasikash_user",
    password="test123",
    host="localhost"
)
cur = conn.cursor()
cur.execute("ALTER TABLE stokvel_members ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'member';")
conn.commit()
cur.close()
conn.close()
print("Added 'role' column to stokvel_members.") 