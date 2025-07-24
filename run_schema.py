import os
import psycopg2

schema_path = "schema.sql"
with open(schema_path, "r") as f:
    sql = f.read()

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print("Schema applied successfully!") 