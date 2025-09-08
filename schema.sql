-- SQL script to create all necessary tables for the KasiKash application in PostgreSQL

-- Create the users table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    firebase_uid VARCHAR(128) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    profile_picture VARCHAR(255),
    phone VARCHAR(50),
    date_of_birth DATE,
    bio TEXT,
    full_name VARCHAR(255),
    id_number VARCHAR(100),
    address VARCHAR(255),
    id_document VARCHAR(255),
    proof_of_address VARCHAR(255),
    last_login TIMESTAMP
);

-- Create the stokvels table
CREATE TABLE IF NOT EXISTS stokvels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    monthly_contribution DECIMAL(10, 2),
    total_pool DECIMAL(10, 2),
    target_amount DECIMAL(10, 2),
    target_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Create the stokvel_members table (linking users to stokvels)
CREATE TABLE IF NOT EXISTS stokvel_members (
    id SERIAL PRIMARY KEY,
    stokvel_id INTEGER NOT NULL REFERENCES stokvels(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    status VARCHAR(20) DEFAULT 'pending',
    UNIQUE (stokvel_id, user_id)
);

-- Create the transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stokvel_id INTEGER REFERENCES stokvels(id) ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date DATE NOT NULL DEFAULT CURRENT_DATE,
    description VARCHAR(255),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create the savings_goals table
CREATE TABLE IF NOT EXISTS savings_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(10, 2) NOT NULL,
    current_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    target_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create the payment_methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    details TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create the chat_history table
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create the chatbot_preferences table
CREATE TABLE IF NOT EXISTS chatbot_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language VARCHAR(10) DEFAULT 'en',
    notification_enabled BOOLEAN DEFAULT TRUE,
    quick_tips_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Create the quick_tips table
CREATE TABLE IF NOT EXISTS quick_tips (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    tip_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX IF NOT EXISTS idx_quick_tips_category ON quick_tips(category);

-- Add initial quick tips
INSERT INTO quick_tips (category, tip_text) VALUES
    ('savings', 'Start with small, regular contributions to build your savings habit.'),
    ('savings', 'Set up automatic transfers to your savings account on payday.'),
    ('stokvel', 'Regular contributions help build trust and grow the stokvel pool faster.'),
    ('stokvel', 'Keep clear records of all stokvel transactions and meetings.'),
    ('budgeting', 'Track your expenses for a month to understand your spending patterns.'),
    ('budgeting', 'Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings.'),
    ('investment', 'Diversify your investments to spread risk.'),
    ('investment', 'Start with low-risk investments while learning about the market.');

-- You might also want to add indexes for performance on frequently queried columns,
-- and potentially sequences if not using SERIAL for primary keys, but SERIAL handles this.
-- Add any other constraints or relationships as needed based on your application logic.

-- Add missing column to users table
DO $$ BEGIN
    ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column created_at already exists in users.';
END $$;

-- Add missing columns to stokvels table
DO $$ BEGIN
    ALTER TABLE stokvels ADD COLUMN description TEXT;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column description already exists in stokvels.';
END $$;

DO $$ BEGIN
    ALTER TABLE stokvels ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column created_at already exists in stokvels.';
END $$;

DO $$ BEGIN
    ALTER TABLE stokvels ADD COLUMN created_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column created_by already exists in stokvels.';
END $$;

-- Add missing column to stokvel_members table
DO $$ BEGIN
    ALTER TABLE stokvel_members ADD COLUMN email VARCHAR(255);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column email already exists in stokvel_members.';
END $$;

DO $$ BEGIN
    ALTER TABLE stokvel_members ADD COLUMN status VARCHAR(20) DEFAULT 'pending';
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column status already exists in stokvel_members.';
END $$;

-- Add missing columns to transactions table
DO $$ BEGIN
    ALTER TABLE transactions ADD COLUMN transaction_date DATE NOT NULL DEFAULT CURRENT_DATE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column transaction_date already exists in transactions.';
END $$;

DO $$ BEGIN
    ALTER TABLE transactions ADD COLUMN description VARCHAR(255);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column description already exists in transactions.';
END $$;

DO $$ BEGIN
    ALTER TABLE transactions ADD COLUMN type VARCHAR(50) NOT NULL;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column type already exists in transactions.';
END $$;

DO $$ BEGIN
    ALTER TABLE transactions ADD COLUMN status VARCHAR(50);
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column status already exists in transactions.';
END $$;

DO $$ BEGIN
    ALTER TABLE transactions ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column created_at already exists in transactions.';
END $$;

-- Note: savings_goals and payment_methods were likely created correctly by running schema.sql,
-- or should be added if missing.

-- Add firebase_uid column to users table if it doesn't exist
DO $$ BEGIN
    ALTER TABLE users ADD COLUMN firebase_uid VARCHAR(128) UNIQUE;
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column firebase_uid already exists in users.';
END $$;

-- Gamification tables (updated for Firebase UID)
CREATE TABLE IF NOT EXISTS user_points (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    points INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS user_badges (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    badge_id INT REFERENCES badges(id),
    earned_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS streaks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    current_streak INT DEFAULT 0,
    last_contribution_date DATE
);

CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL REFERENCES users(firebase_uid),
    achievement_type VARCHAR(50) NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_levels (
    user_id VARCHAR(128) PRIMARY KEY REFERENCES users(firebase_uid),
    level INT DEFAULT 1,
    experience INT DEFAULT 0,
    last_level_up TIMESTAMP
);

CREATE TABLE IF NOT EXISTS challenges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    reward_type VARCHAR(20) NOT NULL,
    reward_value VARCHAR(50) NOT NULL,
    criteria_type VARCHAR(20) NOT NULL,
    criteria_value DECIMAL(12,2) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS user_challenges (
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    challenge_id INT REFERENCES challenges(id),
    progress DECIMAL(12,2) DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP,
    PRIMARY KEY (user_id, challenge_id)
);

-- Chatbot and advisor chat tables (updated for Firebase UID)
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chatbot_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(128) REFERENCES users(firebase_uid),
    language VARCHAR(10) DEFAULT 'en',
    notification_enabled BOOLEAN DEFAULT TRUE,
    quick_tips_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Add savings_goal_id to transactions if not already present
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS savings_goal_id INT REFERENCES savings_goals(id);

-- Seed badges (run separately in psql or admin tool)
-- INSERT INTO badges (name, description, icon) VALUES
-- ('Goal Getter', 'Completed a savings goal', 'icons/goal-getter.svg'),
-- ('Halfway There', 'Reached 50% of a goal', 'icons/halfway-there.svg'),
-- ('First Goal', 'Created your first savings goal', 'icons/first-goal.svg'),
-- ('Streak Starter', '3-day contribution streak', 'icons/streak-starter.svg'),
-- ('Consistent Saver', '7-day contribution streak', 'icons/consistent-saver.svg'),
-- ('Savings Champion', '30-day contribution streak', 'icons/savings-champion.svg');

-- Seed challenges (run separately)
-- INSERT INTO challenges (name, description, reward_type, reward_value, criteria_type, criteria_value) VALUES
-- ('First R100', 'Save your first R100 towards any goal', 'badge', 'Starter Saver', 'savings', 100),
-- ('Weekly Saver', 'Make contributions for 7 consecutive days', 'points', '500', 'consistency', 7),
-- ('Goal Getter', 'Complete your first savings goal', 'badge', 'Goal Champion', 'savings', 1),
-- ('R500 Club', 'Save R500 towards a single goal', 'points', '250', 'savings', 500),
-- ('Early Bird', 'Complete a goal 30 days ahead of schedule', 'bonus', '5% bonus', 'speed', 1);

-- Add missing tables found in the codebase

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS membership_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    features TEXT, -- Comma-separated list of features
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    link_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    -- Add any user-specific settings here, for example:
    email_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    theme VARCHAR(20) DEFAULT 'light'
);

-- Table to store uploaded statement text and AI analysis for each user
CREATE TABLE IF NOT EXISTS financial_statement_analysis (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    statement_text TEXT,
    ai_analysis TEXT,
    transactions_json JSONB,
    file_name VARCHAR(255)
    -- Optionally, add FOREIGN KEY (user_id) REFERENCES users(firebase_uid)
);

-- Table to store chat history for the financial advisor assistant
CREATE TABLE IF NOT EXISTS financial_advisor_chat (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    statement_analysis_id INTEGER REFERENCES financial_statement_analysis(id),
    message TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 

ALTER TABLE financial_statement_analysis ADD COLUMN IF NOT EXISTS ai_budget_plan TEXT; 

-- Optional/legacy tables (uncomment if needed)
-- CREATE TABLE IF NOT EXISTS expenses (...);
-- CREATE TABLE IF NOT EXISTS user_expenses (...);
-- CREATE TABLE IF NOT EXISTS payouts (...);
-- CREATE TABLE IF NOT EXISTS loan_requests (...);
-- CREATE TABLE IF NOT EXISTS loan_repayments (...); 
