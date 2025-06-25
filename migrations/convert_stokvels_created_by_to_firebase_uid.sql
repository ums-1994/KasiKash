-- 1. Add a temporary column for the Firebase UID
ALTER TABLE stokvels ADD COLUMN IF NOT EXISTS temp_created_by VARCHAR(128);

-- 2. Copy the Firebase UID from users into the new column
UPDATE stokvels s
SET temp_created_by = u.firebase_uid
FROM users u
WHERE s.created_by::text = u.id::text;

-- 3. Drop the old foreign key constraint if it exists
ALTER TABLE stokvels DROP CONSTRAINT IF EXISTS stokvels_created_by_fkey;

-- 4. Drop the old created_by column
ALTER TABLE stokvels DROP COLUMN created_by;

-- 5. Rename the temp_created_by column to created_by
ALTER TABLE stokvels RENAME COLUMN temp_created_by TO created_by;

-- 6. Add the new foreign key constraint
ALTER TABLE stokvels
    ADD CONSTRAINT stokvels_created_by_fkey
    FOREIGN KEY (created_by)
    REFERENCES users(firebase_uid)
    ON DELETE SET NULL; 