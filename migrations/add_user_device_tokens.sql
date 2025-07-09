CREATE TABLE IF NOT EXISTS user_device_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_token TEXT NOT NULL,
    platform VARCHAR(20), -- e.g., 'web', 'android', 'ios'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, device_token)
); 