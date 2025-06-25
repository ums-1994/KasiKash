-- 1. Add a temporary column for the Firebase UID
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

-- 2. Copy the Firebase UID from users into the new column
UPDATE payment_methods pm
SET temp_user_id = u.firebase_uid
FROM users u
WHERE pm.user_id::text = u.id::text;

-- 3. Drop the old foreign key constraint if it exists
ALTER TABLE payment_methods DROP CONSTRAINT IF EXISTS payment_methods_user_id_fkey;

-- 4. Drop the old user_id column
ALTER TABLE payment_methods DROP COLUMN user_id;

-- 5. Rename the temp_user_id column to user_id
ALTER TABLE payment_methods RENAME COLUMN temp_user_id TO user_id;

-- 6. Add the new foreign key constraint
ALTER TABLE payment_methods
    ADD CONSTRAINT payment_methods_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(firebase_uid)
    ON DELETE CASCADE; 