-- Migration: Add 'role' column to users table for admin support
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

-- Ensure all existing users have a role
UPDATE users SET role = 'user' WHERE role IS NULL;

-- (Optional) Add a unique constraint for (email, role) for future-proofing
-- ALTER TABLE users ADD CONSTRAINT unique_email_role UNIQUE (email, role); 