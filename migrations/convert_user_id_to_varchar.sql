ALTER TABLE stokvel_members
    ALTER COLUMN user_id TYPE VARCHAR(128) USING user_id::text; 