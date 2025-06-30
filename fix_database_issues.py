import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_issues():
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
        print("🔧 Fixing database issues...")
        
        # 1. Add missing kyc_approved_at column
        print("1. Adding kyc_approved_at column...")
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS kyc_approved_at TIMESTAMP;
        """)
        print("   ✅ kyc_approved_at column added")
        
        # 2. Create missing events table
        print("2. Creating events table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                event_date TIMESTAMP NOT NULL,
                location VARCHAR(200),
                stokvel_id INTEGER REFERENCES stokvels(id),
                created_by VARCHAR(128),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        print("   ✅ events table created")
        
        # 3. Create missing user_levels table if it doesn't exist
        print("3. Checking user_levels table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_levels (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(128) REFERENCES users(firebase_uid),
                level INTEGER DEFAULT 1,
                experience_points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ user_levels table verified")
        
        # 4. Create missing challenges table if it doesn't exist
        print("4. Checking challenges table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS challenges (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                challenge_type VARCHAR(50),
                target_value DECIMAL(10,2),
                reward_points INTEGER DEFAULT 0,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ challenges table verified")
        
        # 5. Create missing user_challenges table if it doesn't exist
        print("5. Checking user_challenges table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_challenges (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(128) REFERENCES users(firebase_uid),
                challenge_id INTEGER REFERENCES challenges(id),
                progress DECIMAL(10,2) DEFAULT 0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ user_challenges table verified")
        
        # 6. Create missing streaks table if it doesn't exist
        print("6. Checking streaks table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(128) REFERENCES users(firebase_uid),
                streak_type VARCHAR(50),
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_activity_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ streaks table verified")
        
        # 7. Add missing columns to users table
        print("7. Adding missing user columns...")
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user',
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
            ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) DEFAULT 'en',
            ADD COLUMN IF NOT EXISTS id_document VARCHAR(255),
            ADD COLUMN IF NOT EXISTS proof_of_address VARCHAR(255),
            ADD COLUMN IF NOT EXISTS kyc_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS kyc_id_status VARCHAR(20) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS kyc_verified_at TIMESTAMP,
            ADD COLUMN IF NOT EXISTS kyc_verified_by VARCHAR(128),
            ADD COLUMN IF NOT EXISTS kyc_rejection_reason TEXT;
        """)
        print("   ✅ missing user columns added")
        
        # 8. Add missing columns to transactions table
        print("8. Adding missing transaction columns...")
        cur.execute("""
            ALTER TABLE transactions 
            ADD COLUMN IF NOT EXISTS savings_goal_id INTEGER REFERENCES savings_goals(id),
            ADD COLUMN IF NOT EXISTS user_id VARCHAR(128) REFERENCES users(firebase_uid);
        """)
        print("   ✅ missing transaction columns added")
        
        # 9. Add missing columns to notifications table
        print("9. Adding missing notification columns...")
        cur.execute("""
            ALTER TABLE notifications 
            ADD COLUMN IF NOT EXISTS link_url TEXT,
            ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'general';
        """)
        print("   ✅ missing notification columns added")
        
        print("\n🎉 All database issues have been fixed!")
        print("\n📊 Summary of fixes:")
        print("   • Added kyc_approved_at column to users table")
        print("   • Created events table for admin events management")
        print("   • Verified/created gamification tables (user_levels, challenges, etc.)")
        print("   • Added missing columns to users, transactions, and notifications tables")
        
    except Exception as e:
        print(f"❌ Error fixing database issues: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_database_issues() 