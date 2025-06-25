from support import db_connection

def check_recent_payouts():
    print("=== Checking Recent Payouts ===")
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, amount, description, status, type, stokvel_id, transaction_date 
                    FROM transactions 
                    WHERE type = 'payout' 
                    ORDER BY transaction_date DESC 
                    LIMIT 5
                """)
                rows = cur.fetchall()
                
                if not rows:
                    print("No payout transactions found.")
                    return
                
                print("\nRecent payouts:")
                print("-" * 80)
                for row in rows:
                    print(f"ID: {row[0]}")
                    print(f"Amount: R{row[1]}")
                    print(f"Description: {row[2]}")
                    print(f"Status: {row[3]}")
                    print(f"Type: {row[4]}")
                    print(f"Stokvel ID: {row[5]}")
                    print(f"Date: {row[6]}")
                    print("-" * 80)
                    
    except Exception as e:
        print(f"Error checking payouts: {e}")

if __name__ == "__main__":
    check_recent_payouts() 