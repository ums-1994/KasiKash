#!/usr/bin/env python3
import support
import psycopg2.extras

def check_table_structure():
    try:
        with support.db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Check stokvel_members table
                print("=== stokvel_members table structure ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'stokvel_members' 
                    ORDER BY ordinal_position
                """)
                for row in cur.fetchall():
                    print(f"{row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
                
                print("\n=== users table structure ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position
                """)
                for row in cur.fetchall():
                    print(f"{row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
                
                print("\n=== transactions table structure ===")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'transactions' 
                    ORDER BY ordinal_position
                """)
                for row in cur.fetchall():
                    print(f"{row['column_name']}: {row['data_type']} (nullable: {row['is_nullable']})")
                
                # Check some sample data
                print("\n=== Sample data ===")
                cur.execute("SELECT COUNT(*) as total_users FROM users")
                total_users = cur.fetchone()['total_users']
                print(f"Total users: {total_users}")
                
                cur.execute("SELECT COUNT(*) as total_members FROM stokvel_members WHERE user_id IS NOT NULL")
                total_members = cur.fetchone()['total_members']
                print(f"Total stokvel members with user_id: {total_members}")
                
                cur.execute("SELECT COUNT(*) as total_deposits FROM transactions WHERE type = 'deposit'")
                total_deposits = cur.fetchone()['total_deposits']
                print(f"Total deposit transactions: {total_deposits}")
                
                cur.execute("SELECT COALESCE(SUM(amount), 0) as total_amount FROM transactions WHERE type = 'deposit'")
                total_amount = cur.fetchone()['total_amount']
                print(f"Total deposit amount: {total_amount}")
                
                cur.execute("SELECT COUNT(*) as kyc_pending FROM users WHERE (id_document IS NOT NULL AND id_document != '') AND (proof_of_address IS NOT NULL AND proof_of_address != '') AND kyc_approved_at IS NULL")
                kyc_pending = cur.fetchone()['kyc_pending']
                print(f"KYC pending: {kyc_pending}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_table_structure() 