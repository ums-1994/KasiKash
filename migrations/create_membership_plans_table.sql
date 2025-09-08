CREATE TABLE IF NOT EXISTS membership_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    monthly_contribution DECIMAL(10, 2) NOT NULL,
    target_amount DECIMAL(10, 2) NOT NULL,
    total_pool DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
); 