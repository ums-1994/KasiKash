-- 1. Add a temporary column for the Firebase UID
ALTER TABLE payouts ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

-- 2. Copy the Firebase UID from users into the new column
UPDATE payouts p
SET temp_user_id = u.firebase_uid
FROM users u
WHERE p.user_id::text = u.id::text;

-- 3. Drop the old foreign key constraint if it exists
ALTER TABLE payouts DROP CONSTRAINT IF EXISTS payouts_user_id_fkey;

-- 4. Drop the old user_id column
ALTER TABLE payouts DROP COLUMN user_id;

-- 5. Rename the temp_user_id column to user_id
ALTER TABLE payouts RENAME COLUMN temp_user_id TO user_id;

-- 6. Add the new foreign key constraint
ALTER TABLE payouts
    ADD CONSTRAINT payouts_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(firebase_uid)
    ON DELETE CASCADE; 