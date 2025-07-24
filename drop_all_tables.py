import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Drop all tables in the public schema
cur.execute("""
DO $$ DECLARE
    r RECORD;
BEGIN
    -- disable triggers
    EXECUTE 'SET session_replication_role = replica';
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS "' || r.tablename || '" CASCADE';
    END LOOP;
    -- enable triggers
    EXECUTE 'SET session_replication_role = DEFAULT';
END $$;
""")

conn.commit()
cur.close()
conn.close()
print("All tables dropped successfully!") 