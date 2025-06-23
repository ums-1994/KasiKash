-- Migration to add language_preference column to users table
-- Run this as postgres superuser

-- Check if column already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'language_preference'
    ) THEN
        -- Add the language_preference column
        ALTER TABLE users ADD COLUMN language_preference VARCHAR(10) DEFAULT 'en';
        RAISE NOTICE 'Successfully added language_preference column to users table';
    ELSE
        RAISE NOTICE 'Column language_preference already exists in users table';
    END IF;
END $$; 