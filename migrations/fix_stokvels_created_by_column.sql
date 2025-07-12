-- First, add a new temporary column to store the Firebase UID
ALTER TABLE stokvels ADD COLUMN created_by_firebase_uid VARCHAR(255);

-- Update the new column with the Firebase UID by joining with the users table
-- This assumes the old `created_by` was an integer ID corresponding to `users.id`
UPDATE stokvels s
SET created_by_firebase_uid = u.firebase_uid
FROM users u
WHERE s.created_by::int = u.id;

-- Now, drop the old `created_by` column
ALTER TABLE stokvels DROP COLUMN created_by;

-- Finally, rename the new column to `created_by`
ALTER TABLE stokvels RENAME COLUMN created_by_firebase_uid TO created_by; 