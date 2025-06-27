import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def fix_payout_descriptions():
    """
    Corrects historical payout records where the description was incorrectly
    saved in the status field.
    """
    print("=== Fix Payout Descriptions Migration ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Identify and update incorrect payout transactions
                sql_update = """
                    UPDATE transactions
                    SET 
                        description = status,
                        status = 'completed'
                    WHERE 
                        type = 'payout' 
                        AND status NOT IN ('pending', 'approved', 'declined', 'completed');
                """
                cur.execute(sql_update)
                updated_rows = cur.rowcount
                conn.commit()
                
                if updated_rows > 0:
                    print(f"✅ Successfully corrected {updated_rows} historical payout records.")
                else:
                    print("✅ No incorrect payout records found to fix.")

                print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    fix_payout_descriptions() 