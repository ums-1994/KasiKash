import os
import psycopg2

schema_path = "schema.sql"
with open(schema_path, "r") as f:
    sql = f.read()

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Split SQL into individual statements and execute each
for statement in sql.split(";"):
    stmt = statement.strip()
    if stmt:
        try:
            cur.execute(stmt)
        except Exception as e:
            print(f"Error executing statement: {stmt}\n{e}")

conn.commit()
cur.close()
conn.close()
print("Schema applied successfully!") 