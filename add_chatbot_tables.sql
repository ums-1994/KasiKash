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