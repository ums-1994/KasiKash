from support import db_connection

def fix_payout_typos():
    print("=== Fixing Payout Description Typos ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Fix "monthly payou" -> "monthly payout"
                cur.execute("""
                    UPDATE transactions 
                    SET description = 'monthly payout'
                    WHERE id = 11 AND type = 'payout' AND description = 'monthly payou';
                """)
                
                # Fix "mothly payout" -> "monthly payout"
                cur.execute("""
                    UPDATE transactions 
                    SET description = 'monthly payout'
                    WHERE id = 6 AND type = 'payout' AND description = 'mothly payout';
                """)
                
                conn.commit()
                print("✅ Successfully fixed payout description typos")
                
    except Exception as e:
        print(f"❌ Error fixing typos: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    fix_payout_typos() 