import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def backfill_contributions_to_transactions():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    print('Backfilling old contributions into transactions table...')
    # Get all contributions
    cur.execute("""
        SELECT id, stokvel_id, user_id, amount, status, description, created_at
        FROM contributions
    """)
    contributions = cur.fetchall()
    print(f"Found {len(contributions)} contributions.")
    inserted = 0
    skipped = 0
    errors = 0
    for row in contributions:
        contrib_id, stokvel_id, user_id, amount, status, description, created_at = row
        try:
            # Get firebase_uid for this user_id
            cur.execute("SELECT firebase_uid FROM users WHERE id = %s", (user_id,))
            user_row = cur.fetchone()
            if not user_row or not user_row[0]:
                print(f"[SKIP] Contribution id={contrib_id}: user_id {user_id} has no firebase_uid.")
                skipped += 1
                continue
            firebase_uid = user_row[0]
            # Normalize status/description
            status = status if status is not None else ''
            description = description if description is not None else ''
            # Print debug info for duplicate check
            print(f"[DEBUG] Checking for duplicate: user_id={firebase_uid}, stokvel_id={stokvel_id}, amount={amount}, date={created_at.date()}, type='contribution'")
            # Special case: always insert for user_id=1 and stokvel_id=2
            if user_id == 1 and stokvel_id == 2:
                print(f"[FORCE INSERT] For user_id=1 and stokvel_id=2, skipping duplicate check.")
                cur.execute("""
                    INSERT INTO transactions (user_id, stokvel_id, amount, type, description, status, transaction_date, created_at, transaction_type)
                    VALUES (%s, %s, %s, 'contribution', %s, %s, %s, %s, %s)
                """, (firebase_uid, stokvel_id, amount, description, status, created_at, created_at, 'money'))
                print(f"[INSERT] Transaction for contribution id={contrib_id} (user_id={firebase_uid}, stokvel_id={stokvel_id}, amount={amount}, date={created_at})")
                inserted += 1
                continue
            # Relaxed duplicate check: ignore description, just check user, stokvel, amount, date
            cur.execute("""
                SELECT id FROM transactions WHERE user_id = %s AND stokvel_id = %s AND amount = %s AND transaction_date::date = %s AND type = 'contribution'
            """, (firebase_uid, stokvel_id, amount, created_at.date()))
            if cur.fetchone():
                print(f"[SKIP] Transaction already exists for contribution id={contrib_id} (relaxed check).")
                skipped += 1
                continue
            # Insert into transactions
            cur.execute("""
                INSERT INTO transactions (user_id, stokvel_id, amount, type, description, status, transaction_date, created_at, transaction_type)
                VALUES (%s, %s, %s, 'contribution', %s, %s, %s, %s, %s)
            """, (firebase_uid, stokvel_id, amount, description, status, created_at, created_at, 'money'))
            print(f"[INSERT] Transaction for contribution id={contrib_id} (user_id={firebase_uid}, stokvel_id={stokvel_id}, amount={amount}, date={created_at})")
            inserted += 1
        except Exception as e:
            print(f"[ERROR] Contribution id={contrib_id}: {e}")
            errors += 1
    conn.commit()
    print(f"\nDone. Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    backfill_contributions_to_transactions() 