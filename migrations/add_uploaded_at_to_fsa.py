import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME', 'kasikash_db'),
    user=os.getenv('DB_USER', 'kasikash_user'),
    password=os.getenv('DB_PASSWORD', 'test123'),
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432')
)
cur = conn.cursor()
cur.execute("""
    ALTER TABLE financial_statement_analysis
    ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
""")
conn.commit()
cur.close()
conn.close()
print('✅ uploaded_at column added to financial_statement_analysis') 