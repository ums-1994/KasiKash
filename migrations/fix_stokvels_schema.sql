-- Migration: Fix stokvels schema for Firebase UID and missing columns

-- 1. Add goal_amount column if missing
ALTER TABLE stokvels ADD COLUMN IF NOT EXISTS goal_amount DECIMAL(10,2);

-- 2. Convert created_by in stokvels to Firebase UID (VARCHAR)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='stokvels' AND column_name='created_by' AND data_type='integer'
    ) THEN
        -- Add a temp column for Firebase UID
        ALTER TABLE stokvels ADD COLUMN IF NOT EXISTS temp_created_by VARCHAR(128);
        -- Copy UIDs from users
        UPDATE stokvels s SET temp_created_by = u.firebase_uid FROM users u WHERE s.created_by::text = u.id::text;
        -- Drop old FK and column, rename temp
        ALTER TABLE stokvels DROP CONSTRAINT IF EXISTS stokvels_created_by_fkey;
        ALTER TABLE stokvels DROP COLUMN created_by;
        ALTER TABLE stokvels RENAME COLUMN temp_created_by TO created_by;
        -- Add new FK
        ALTER TABLE stokvels ADD CONSTRAINT stokvels_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(firebase_uid) ON DELETE SET NULL;
    END IF;
END $$;

-- 3. Convert user_id in stokvel_members to Firebase UID (VARCHAR)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='stokvel_members' AND column_name='user_id' AND data_type='integer'
    ) THEN
        ALTER TABLE stokvel_members ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
        UPDATE stokvel_members sm SET temp_user_id = u.firebase_uid FROM users u WHERE sm.user_id = u.id;
        ALTER TABLE stokvel_members DROP CONSTRAINT IF EXISTS stokvel_members_user_id_fkey;
        ALTER TABLE stokvel_members DROP COLUMN user_id;
        ALTER TABLE stokvel_members RENAME COLUMN temp_user_id TO user_id;
        ALTER TABLE stokvel_members ADD CONSTRAINT stokvel_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;
    END IF;
END $$; 