import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_voucher_columns():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'kasikash_db'),
            user=os.getenv('DB_USER', 'kasikash_user'),
            password=os.getenv('DB_PASSWORD', 'test123'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        cur = conn.cursor()
        # Add voucher_type column
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vouchers' AND column_name='voucher_type') THEN
                    ALTER TABLE vouchers ADD COLUMN voucher_type VARCHAR(50);
                END IF;
            END $$;
        """)
        # Add voucher_code column
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vouchers' AND column_name='voucher_code') THEN
                    ALTER TABLE vouchers ADD COLUMN voucher_code VARCHAR(100);
                END IF;
            END $$;
        """)
        # Add status column
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vouchers' AND column_name='status') THEN
                    ALTER TABLE vouchers ADD COLUMN status VARCHAR(20) DEFAULT 'active';
                END IF;
            END $$;
        """)
        # Add used_at column
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='vouchers' AND column_name='used_at') THEN
                    ALTER TABLE vouchers ADD COLUMN used_at TIMESTAMP;
                END IF;
            END $$;
        """)
        # Migrate data from code to voucher_code if needed
        cur.execute("""
            UPDATE vouchers SET voucher_code = code WHERE voucher_code IS NULL AND code IS NOT NULL;
        """)
        # Migrate data from redeemed_at to used_at if needed
        cur.execute("""
            UPDATE vouchers SET used_at = redeemed_at WHERE used_at IS NULL AND redeemed_at IS NOT NULL;
        """)
        # Set status based on is_redeemed
        cur.execute("""
            UPDATE vouchers SET status = CASE WHEN is_redeemed THEN 'used' ELSE 'active' END;
        """)
        conn.commit()
        cur.close()
        print("✅ voucher_type, voucher_code, status, and used_at columns added and data migrated.")
    except Exception as e:
        print(f"❌ Error updating vouchers table: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_voucher_columns() 