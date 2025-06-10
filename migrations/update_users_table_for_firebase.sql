-- Update users table for Firebase authentication
ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(128) UNIQUE;

-- Create temporary columns for the conversion
ALTER TABLE stokvels
    ADD COLUMN IF NOT EXISTS temp_created_by VARCHAR(128);

-- Update the temporary column with the firebase_uid from users
UPDATE stokvels s
SET temp_created_by = u.firebase_uid
FROM users u
WHERE s.created_by = u.id;

-- Drop the old foreign key constraints
ALTER TABLE stokvels
    DROP CONSTRAINT IF EXISTS stokvels_created_by_fkey;

-- Drop the old column and rename the temporary one
ALTER TABLE stokvels
    DROP COLUMN created_by;
ALTER TABLE stokvels
    ALTER COLUMN temp_created_by SET NOT NULL;
ALTER TABLE stokvels
    RENAME COLUMN temp_created_by TO created_by;

-- Add the new foreign key constraint
ALTER TABLE stokvels
    ADD CONSTRAINT stokvels_created_by_fkey 
    FOREIGN KEY (created_by) 
    REFERENCES users(firebase_uid) 
    ON DELETE SET NULL;

-- Similar process for other tables
-- For stokvel_members
ALTER TABLE stokvel_members
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE stokvel_members sm
SET temp_user_id = u.firebase_uid
FROM users u
WHERE sm.user_id = u.id;

ALTER TABLE stokvel_members
    DROP CONSTRAINT IF EXISTS stokvel_members_user_id_fkey;

ALTER TABLE stokvel_members
    DROP COLUMN user_id;
ALTER TABLE stokvel_members
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE stokvel_members
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE stokvel_members
    ADD CONSTRAINT stokvel_members_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- For transactions
ALTER TABLE transactions
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE transactions t
SET temp_user_id = u.firebase_uid
FROM users u
WHERE t.user_id = u.id;

ALTER TABLE transactions
    DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;

ALTER TABLE transactions
    DROP COLUMN user_id;
ALTER TABLE transactions
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE transactions
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE transactions
    ADD CONSTRAINT transactions_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- For savings_goals
ALTER TABLE savings_goals
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE savings_goals sg
SET temp_user_id = u.firebase_uid
FROM users u
WHERE sg.user_id = u.id;

ALTER TABLE savings_goals
    DROP CONSTRAINT IF EXISTS savings_goals_user_id_fkey;

ALTER TABLE savings_goals
    DROP COLUMN user_id;
ALTER TABLE savings_goals
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE savings_goals
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE savings_goals
    ADD CONSTRAINT savings_goals_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- For payment_methods
ALTER TABLE payment_methods
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE payment_methods pm
SET temp_user_id = u.firebase_uid
FROM users u
WHERE pm.user_id = u.id;

ALTER TABLE payment_methods
    DROP CONSTRAINT IF EXISTS payment_methods_user_id_fkey;

ALTER TABLE payment_methods
    DROP COLUMN user_id;
ALTER TABLE payment_methods
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE payment_methods
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE payment_methods
    ADD CONSTRAINT payment_methods_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- For chat_history
ALTER TABLE chat_history
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE chat_history ch
SET temp_user_id = u.firebase_uid
FROM users u
WHERE ch.user_id = u.id;

ALTER TABLE chat_history
    DROP CONSTRAINT IF EXISTS chat_history_user_id_fkey;

ALTER TABLE chat_history
    DROP COLUMN user_id;
ALTER TABLE chat_history
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE chat_history
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE chat_history
    ADD CONSTRAINT chat_history_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- For chatbot_preferences
ALTER TABLE chatbot_preferences
    ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);

UPDATE chatbot_preferences cp
SET temp_user_id = u.firebase_uid
FROM users u
WHERE cp.user_id = u.id;

ALTER TABLE chatbot_preferences
    DROP CONSTRAINT IF EXISTS chatbot_preferences_user_id_fkey;

ALTER TABLE chatbot_preferences
    DROP COLUMN user_id;
ALTER TABLE chatbot_preferences
    ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE chatbot_preferences
    RENAME COLUMN temp_user_id TO user_id;

ALTER TABLE chatbot_preferences
    ADD CONSTRAINT chatbot_preferences_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES users(firebase_uid) 
    ON DELETE CASCADE;

-- Finally, remove the old columns from users table
ALTER TABLE users 
    DROP COLUMN IF EXISTS password,
    DROP COLUMN IF EXISTS verification_token,
    DROP COLUMN IF EXISTS is_verified; 