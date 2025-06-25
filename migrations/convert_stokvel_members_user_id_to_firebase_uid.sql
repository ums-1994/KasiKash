-- 1. Add a temporary column for the Firebase UID
ALTER TABLE stokvel_members ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

-- 2. Copy the Firebase UID from users into the new column
UPDATE stokvel_members sm
SET temp_user_id = u.firebase_uid
FROM users u
WHERE sm.user_id::text = u.id::text;

-- 3. Drop the old foreign key constraint if it exists
ALTER TABLE stokvel_members DROP CONSTRAINT IF EXISTS stokvel_members_user_id_fkey;

-- 4. Drop the old user_id column
ALTER TABLE stokvel_members DROP COLUMN user_id;

-- 5. Rename the temp_user_id column to user_id
ALTER TABLE stokvel_members RENAME COLUMN temp_user_id TO user_id;

-- 6. Add the new foreign key constraint
ALTER TABLE stokvel_members
    ADD CONSTRAINT stokvel_members_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(firebase_uid)
    ON DELETE CASCADE; 