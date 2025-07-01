CREATE TABLE IF NOT EXISTS gamification (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    exp INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    badges TEXT[], -- Array of badge names or IDs
    level_progress FLOAT DEFAULT 0.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 