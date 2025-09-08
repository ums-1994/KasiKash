-- Migration: Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(255) NOT NULL,
    "user" VARCHAR(255) NOT NULL,
    target VARCHAR(255),
    amount NUMERIC,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 