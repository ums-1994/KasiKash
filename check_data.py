#!/usr/bin/env python3
import support
import psycopg2.extras

def check_data():
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Check stokvel_members data
                print("=== stokvel_members data ===")
                cur.execute("SELECT COUNT(*) as total FROM stokvel_members")
                total = cur.fetchone()['total']
                print(f"Total stokvel_members: {total}")
                
                cur.execute("SELECT COUNT(*) as with_user_id FROM stokvel_members WHERE user_id IS NOT NULL")
                with_user_id = cur.fetchone()['with_user_id']
                print(f"stokvel_members with user_id: {with_user_id}")
                
                cur.execute("SELECT user_id FROM stokvel_members WHERE user_id IS NOT NULL LIMIT 5")
                sample_user_ids = cur.fetchall()
                print(f"Sample user_ids: {[row['user_id'] for row in sample_user_ids]}")
                
                # Check users data
                print("\n=== users data ===")
                cur.execute("SELECT COUNT(*) as total FROM users")
                total_users = cur.fetchone()['total']
                print(f"Total users: {total_users}")
                
                cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid IS NOT NULL LIMIT 5")
                sample_firebase_uids = cur.fetchall()
                print(f"Sample firebase_uids: {[row['firebase_uid'] for row in sample_firebase_uids]}")
                
                # Check transactions data
                print("\n=== transactions data ===")
                cur.execute("SELECT COUNT(*) as total FROM transactions")
                total_transactions = cur.fetchone()['total']
                print(f"Total transactions: {total_transactions}")
                
                cur.execute("SELECT type, COUNT(*) as count FROM transactions GROUP BY type")
                transaction_types = cur.fetchall()
                print("Transaction types:")
                for row in transaction_types:
                    print(f"  {row['type']}: {row['count']}")
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE type = 'deposit'")
                total_deposits = cur.fetchone()['total']
                print(f"Total deposit amount: {total_deposits}")
                
                # Check KYC data
                print("\n=== KYC data ===")
                cur.execute("SELECT COUNT(*) as with_id_doc FROM users WHERE id_document IS NOT NULL AND id_document != ''")
                with_id_doc = cur.fetchone()['with_id_doc']
                print(f"Users with ID document: {with_id_doc}")
                
                cur.execute("SELECT COUNT(*) as with_address FROM users WHERE proof_of_address IS NOT NULL AND proof_of_address != ''")
                with_address = cur.fetchone()['with_address']
                print(f"Users with proof of address: {with_address}")
                
                cur.execute("SELECT COUNT(*) as kyc_pending FROM users WHERE (id_document IS NOT NULL AND id_document != '') AND (proof_of_address IS NOT NULL AND proof_of_address != '') AND kyc_approved_at IS NULL")
                kyc_pending = cur.fetchone()['kyc_pending']
                print(f"KYC pending: {kyc_pending}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data() 