-- Migration: Change user_id in stokvel_members to reference users.firebase_uid

-- 1. Drop old foreign key constraint (if exists)
ALTER TABLE stokvel_members DROP CONSTRAINT IF EXISTS stokvel_members_user_id_fkey;

-- 2. Alter user_id column type to VARCHAR(128)
ALTER TABLE stokvel_members ALTER COLUMN user_id TYPE VARCHAR(128);

-- 3. Add new foreign key constraint referencing users.firebase_uid
ALTER TABLE stokvel_members
    ADD CONSTRAINT stokvel_members_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES users(firebase_uid)
    ON DELETE CASCADE; 