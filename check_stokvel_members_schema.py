import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)
cur = conn.cursor()

with open('stokvel_members_schema.txt', 'w') as f:
    f.write('stokvel_members table schema:\n')
    cur.execute("""
        SELECT column_name, is_nullable, data_type
        FROM information_schema.columns
        WHERE table_name = 'stokvel_members'
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        f.write(str(row) + '\n')
cur.close()
conn.close() 