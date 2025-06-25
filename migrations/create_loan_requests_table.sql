CREATE TABLE IF NOT EXISTS loan_requests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid) ON DELETE CASCADE,
    stokvel_id INTEGER REFERENCES stokvels(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 