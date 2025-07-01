-- This script populates the user_id in stokvel_members with the corresponding firebase_uid from the users table.
-- It assumes there's a temporary integer-based user_id column (e.g., user_id_old) that needs mapping.

-- Step 1: Add a temporary integer column to store the old user_id if it doesn't exist
ALTER TABLE stokvel_members ADD COLUMN IF NOT EXISTS user_id_old INTEGER;

-- Step 2: Copy existing user_id values to the temporary column
-- This should be run before user_id is converted to VARCHAR
-- UPDATE stokvel_members SET user_id_old = user_id::integer; (run this manually if needed)

-- Step 3: Update the user_id (now VARCHAR) with the Firebase UID from the users table
UPDATE stokvel_members sm
SET user_id = u.firebase_uid
FROM users u
WHERE sm.user_id_old = u.id;

-- Step 4: (Optional) Drop the temporary column after verification
-- ALTER TABLE stokvel_members DROP COLUMN user_id_old; 