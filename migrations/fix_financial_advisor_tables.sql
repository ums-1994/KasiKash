-- Migration to fix financial advisor database tables
-- Run this script to improve the database structure

-- 1. Add proper foreign key constraints
ALTER TABLE financial_statement_analysis 
ADD CONSTRAINT fk_financial_analysis_user_id 
FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

ALTER TABLE financial_advisor_chat 
ADD CONSTRAINT fk_advisor_chat_user_id 
FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- 2. Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_financial_analysis_user_id ON financial_statement_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_financial_analysis_uploaded_at ON financial_statement_analysis(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_advisor_chat_user_id ON financial_advisor_chat(user_id);
CREATE INDEX IF NOT EXISTS idx_advisor_chat_created_at ON financial_advisor_chat(created_at);
CREATE INDEX IF NOT EXISTS idx_advisor_chat_analysis_id ON financial_advisor_chat(statement_analysis_id);

-- 3. Add constraints to ensure data integrity
ALTER TABLE financial_statement_analysis 
ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE financial_advisor_chat 
ALTER COLUMN user_id SET NOT NULL;

-- 4. Add comments for documentation
COMMENT ON TABLE financial_statement_analysis IS 'Stores uploaded bank statements and AI analysis results';
COMMENT ON TABLE financial_advisor_chat IS 'Stores chat history between users and AI financial advisor';

COMMENT ON COLUMN financial_statement_analysis.statement_text IS 'Raw OCR text extracted from uploaded bank statement';
COMMENT ON COLUMN financial_statement_analysis.ai_analysis IS 'AI-generated financial analysis and insights';
COMMENT ON COLUMN financial_statement_analysis.transactions_json IS 'Parsed transactions in JSON format';
COMMENT ON COLUMN financial_statement_analysis.ai_budget_plan IS 'AI-generated budget recommendations';

COMMENT ON COLUMN financial_advisor_chat.message IS 'User question or request to the financial advisor';
COMMENT ON COLUMN financial_advisor_chat.response IS 'AI advisor response to user question'; 