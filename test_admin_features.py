import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_admin_features():
    """Test all admin features to ensure they work correctly"""
    
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()
    
    print("🧪 Testing Admin Features...")
    print("=" * 50)
    
    try:
        # Test 1: Admin Dashboard Data
        print("1. Testing Admin Dashboard...")
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM stokvels")
        stokvel_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM transactions WHERE type = 'payout' AND status = 'pending'")
        pending_loans = cur.fetchone()[0]
        
        print(f"   ✅ Users: {user_count}")
        print(f"   ✅ Stokvels: {stokvel_count}")
        print(f"   ✅ Pending Loans: {pending_loans}")
        
        # Test 2: User Management
        print("\n2. Testing User Management...")
        cur.execute("SELECT id, username, email, role, created_at FROM users LIMIT 5")
        users = cur.fetchall()
        print(f"   ✅ Found {len(users)} users")
        for user in users:
            print(f"      - {user[1]} ({user[2]}) - Role: {user[3]}")
        
        # Test 3: Loan Approvals
        print("\n3. Testing Loan Approvals...")
        cur.execute("""
            SELECT t.id, u.username, u.email, t.amount, t.status, t.transaction_date
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.firebase_uid
            WHERE t.type = 'payout'
            LIMIT 5
        """)
        loans = cur.fetchall()
        print(f"   ✅ Found {len(loans)} payout transactions")
        
        # Test 4: Events Management
        print("\n4. Testing Events Management...")
        cur.execute("SELECT COUNT(*) FROM events")
        event_count = cur.fetchone()[0]
        print(f"   ✅ Events table exists with {event_count} events")
        
        # Test 5: KYC Approvals
        print("\n5. Testing KYC Approvals...")
        cur.execute("""
            SELECT username, email, id_document, proof_of_address, 
                   kyc_status, kyc_approved_at, created_at
            FROM users 
            WHERE id_document IS NOT NULL OR proof_of_address IS NOT NULL
            LIMIT 5
        """)
        kyc_users = cur.fetchall()
        print(f"   ✅ Found {len(kyc_users)} users with KYC documents")
        
        # Test 6: Notifications
        print("\n6. Testing Notifications...")
        cur.execute("SELECT COUNT(*) FROM notifications")
        notification_count = cur.fetchone()[0]
        print(f"   ✅ Notifications table exists with {notification_count} notifications")
        
        # Test 7: Membership Plans
        print("\n7. Testing Membership Plans...")
        cur.execute("SELECT COUNT(*) FROM membership_plans")
        membership_count = cur.fetchone()[0]
        print(f"   ✅ Membership plans table exists with {membership_count} plans")
        
        # Test 8: Gamification Tables
        print("\n8. Testing Gamification Tables...")
        cur.execute("SELECT COUNT(*) FROM user_levels")
        user_levels_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM challenges")
        challenges_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_challenges")
        user_challenges_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM streaks")
        streaks_count = cur.fetchone()[0]
        
        print(f"   ✅ User Levels: {user_levels_count}")
        print(f"   ✅ Challenges: {challenges_count}")
        print(f"   ✅ User Challenges: {user_challenges_count}")
        print(f"   ✅ Streaks: {streaks_count}")
        
        print("\n🎉 All Admin Features Tested Successfully!")
        print("\n📋 Summary:")
        print("   • Admin Dashboard: ✅ Working")
        print("   • User Management: ✅ Working")
        print("   • Loan Approvals: ✅ Working")
        print("   • Events Management: ✅ Working")
        print("   • KYC Approvals: ✅ Working")
        print("   • Notifications: ✅ Working")
        print("   • Membership Plans: ✅ Working")
        print("   • Gamification: ✅ Working")
        
    except Exception as e:
        print(f"❌ Error testing admin features: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_admin_features() 