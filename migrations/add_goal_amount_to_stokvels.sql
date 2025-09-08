-- Add goal_amount column to stokvels table if it does not exist
ALTER TABLE stokvels ADD COLUMN IF NOT EXISTS goal_amount DECIMAL(10,2); 