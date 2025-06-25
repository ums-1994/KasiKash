CREATE TABLE IF NOT EXISTS user_expenses (
    id SERIAL PRIMARY KEY,
    firebase_uid VARCHAR(128) REFERENCES users(firebase_uid) ON DELETE CASCADE,
    pdate DATE NOT NULL,
    expense VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    pdescription VARCHAR(255)
); 