-- Step 1: Rename old column for backup
ALTER TABLE user_settings RENAME COLUMN user_id TO old_user_id;

-- Step 2: Add new column for firebase_uid
ALTER TABLE user_settings ADD COLUMN user_id VARCHAR(64);

-- Step 3: Migrate existing data (if any)
UPDATE user_settings us
SET user_id = u.firebase_uid
FROM users u
WHERE us.old_user_id = u.id;

-- Step 4: Drop the old column
ALTER TABLE user_settings DROP COLUMN old_user_id;

-- Step 5: Add unique constraint (if needed)
ALTER TABLE user_settings ADD CONSTRAINT user_settings_user_id_key UNIQUE (user_id); 