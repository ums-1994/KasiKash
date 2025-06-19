ALTER TABLE stokvel_members ADD COLUMN email VARCHAR(255);
ALTER TABLE stokvel_members ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE stokvel_members ADD COLUMN status VARCHAR(20) DEFAULT 'pending'; 