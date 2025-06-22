import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_kyc_status_columns():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    conn.autocommit = True
    cur = conn.cursor()
    try:
        print("Adding KYC status columns to users table...")
        
        # Add KYC status columns
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS id_document_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS proof_of_address_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS kyc_verified_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS kyc_verified_by VARCHAR(128),
            ADD COLUMN IF NOT EXISTS kyc_rejection_reason TEXT;
        """)
        
        print("KYC status columns added successfully!")
        
        # Update existing records to have 'pending' status if they have documents
        cur.execute("""
            UPDATE users 
            SET id_document_status = 'pending' 
            WHERE id_document IS NOT NULL AND id_document_status IS NULL
        """)
        
        cur.execute("""
            UPDATE users 
            SET proof_of_address_status = 'pending' 
            WHERE proof_of_address IS NOT NULL AND proof_of_address_status IS NULL
        """)
        
        print("Existing KYC documents marked as pending for verification.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_kyc_status_columns() 