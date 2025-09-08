import sys
import os
import psycopg2
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from support import db_connection

def fix_payout_descriptions_v2():
    """
    Corrects historical payout records where the description was incorrectly
    saved in the status field. This version includes diagnostics.
    """
    print("=== Fix Payout Descriptions Migration (v2) ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Diagnostic SELECT to see what we are about to update
                print("\n🔍 Finding incorrect payout records to fix...")
                sql_select = """
                    SELECT id, description, status FROM transactions
                    WHERE type = 'payout' AND status NOT IN ('pending', 'approved', 'declined', 'completed');
                """
                cur.execute(sql_select)
                incorrect_records = cur.fetchall()

                if not incorrect_records:
                    print("✅ No incorrect payout records were found. Your data seems correct already.")
                    return

                print(f"Found {len(incorrect_records)} records to fix:")
                for record in incorrect_records:
                    print(f"  - ID: {record[0]}, Current Description: '{record[1]}', Current Status: '{record[2]}'")

                # Perform the update
                print("\n⚙️ Correcting records...")
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
                    print("⚠️ The update command ran but did not modify any rows, which is unexpected.")

                print("\n🎉 Migration completed successfully!")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    fix_payout_descriptions_v2() 