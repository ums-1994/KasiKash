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

-- 3. Add additional performance indexes
CREATE INDEX IF NOT EXISTS idx_financial_analysis_user_uploaded ON financial_statement_analysis(user_id, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_advisor_chat_user_created ON financial_advisor_chat(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_financial_analysis_file_name ON financial_statement_analysis(file_name) WHERE file_name IS NOT NULL;

-- 4. Add constraints to ensure data integrity
ALTER TABLE financial_statement_analysis 
ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE financial_advisor_chat 
ALTER COLUMN user_id SET NOT NULL;

-- 5. Add check constraints for data validation
ALTER TABLE financial_statement_analysis 
ADD CONSTRAINT chk_statement_text_not_empty 
CHECK (statement_text IS NOT NULL AND LENGTH(TRIM(statement_text)) > 0);

ALTER TABLE financial_advisor_chat 
ADD CONSTRAINT chk_message_not_empty 
CHECK (message IS NOT NULL AND LENGTH(TRIM(message)) > 0);

ALTER TABLE financial_advisor_chat 
ADD CONSTRAINT chk_response_not_empty 
CHECK (response IS NOT NULL AND LENGTH(TRIM(response)) > 0);

-- 6. Add comments for documentation
COMMENT ON TABLE financial_statement_analysis IS 'Stores uploaded bank statements and AI analysis results';
COMMENT ON TABLE financial_advisor_chat IS 'Stores chat history between users and AI financial advisor';

COMMENT ON COLUMN financial_statement_analysis.statement_text IS 'Raw OCR text extracted from uploaded bank statement';
COMMENT ON COLUMN financial_statement_analysis.ai_analysis IS 'AI-generated financial analysis and insights';
COMMENT ON COLUMN financial_statement_analysis.transactions_json IS 'Parsed transactions in JSON format';
COMMENT ON COLUMN financial_statement_analysis.ai_budget_plan IS 'AI-generated budget recommendations';
COMMENT ON COLUMN financial_statement_analysis.file_name IS 'Original uploaded file name for reference';
COMMENT ON COLUMN financial_statement_analysis.uploaded_at IS 'Timestamp when the statement was uploaded and processed';

COMMENT ON COLUMN financial_advisor_chat.message IS 'User question or request to the financial advisor';
COMMENT ON COLUMN financial_advisor_chat.response IS 'AI advisor response to user question';
COMMENT ON COLUMN financial_advisor_chat.statement_analysis_id IS 'Reference to the financial analysis this chat relates to';
COMMENT ON COLUMN financial_advisor_chat.created_at IS 'Timestamp when the chat message was created';

-- 7. Add performance optimizations
-- Enable row-level security for multi-tenant data isolation
ALTER TABLE financial_statement_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_advisor_chat ENABLE ROW LEVEL SECURITY;

-- Create policies for row-level security
CREATE POLICY financial_analysis_user_policy ON financial_statement_analysis
    FOR ALL USING (user_id = current_setting('app.current_user_id', true)::varchar);

CREATE POLICY advisor_chat_user_policy ON financial_advisor_chat
    FOR ALL USING (user_id = current_setting('app.current_user_id', true)::varchar);

-- 8. Add statistics for query optimization
ANALYZE financial_statement_analysis;
ANALYZE financial_advisor_chat; 