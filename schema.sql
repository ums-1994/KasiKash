-- SQL script to create all necessary tables for the KasiKash application in PostgreSQL

-- Create the users table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(30) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
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
    ALTER TABLE stokvel_members ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'member';
EXCEPTION
    WHEN duplicate_column THEN RAISE NOTICE 'column role already exists in stokvel_members.';
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
-- as they did not exist before. So ALTER TABLE is probably not needed for them. 