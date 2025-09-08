-- Migration to add kyc_id_status column to users table
ALTER TABLE users ADD COLUMN kyc_id_status VARCHAR(32);
-- Optionally, set a default value or update existing rows as needed
-- UPDATE users SET kyc_id_status = 'pending' WHERE kyc_id_status IS NULL;
