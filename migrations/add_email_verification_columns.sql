-- Add columns for custom email verification
ALTER TABLE users
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS verification_token_expiry TIMESTAMP WITH TIME ZONE; 