ALTER TABLE stokvel_members ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'member';

UPDATE stokvel_members sm SET role = 'admin' FROM stokvels s WHERE sm.stokvel_id = s.id AND sm.user_id = s.created_by; 