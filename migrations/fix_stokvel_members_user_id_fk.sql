-- Drop the old foreign key constraint if it exists
ALTER TABLE stokvel_members DROP CONSTRAINT IF EXISTS stokvel_members_user_id_fkey;

-- Add a new foreign key constraint referencing users.firebase_uid
ALTER TABLE stokvel_members
    ADD CONSTRAINT stokvel_members_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(firebase_uid)
    ON DELETE CASCADE; 