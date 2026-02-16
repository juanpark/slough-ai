-- Slough.ai Database Initialization Script
-- This runs automatically when the PostgreSQL container starts

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "vector";

-- Workspaces table (stores installed workspace info)
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slack_team_id VARCHAR(20) UNIQUE NOT NULL,
    slack_team_name VARCHAR(255),
    admin_id VARCHAR(20) NOT NULL,
    decision_maker_id VARCHAR(20) NOT NULL,
    bot_token TEXT NOT NULL,
    user_token TEXT DEFAULT '',
    installed_at TIMESTAMP DEFAULT NOW(),
    uninstalled_at TIMESTAMP,
    data_deletion_at TIMESTAMP,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rules table (decision-maker-declared rules)
CREATE TABLE IF NOT EXISTS rules (
    id SERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    rule_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for active rules lookup
CREATE INDEX IF NOT EXISTS rules_workspace_active_idx
ON rules(workspace_id, is_active);

-- QA History table (stores all Q&A interactions)
CREATE TABLE IF NOT EXISTS qa_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    asker_user_id VARCHAR(20) NOT NULL,
    asker_user_name VARCHAR(255),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    message_ts VARCHAR(20),
    channel_id VARCHAR(20),

    -- Review tracking
    review_status VARCHAR(20) DEFAULT 'none',  -- none, requested, completed
    review_requested_at TIMESTAMP,

    -- Decision-maker feedback
    feedback_type VARCHAR(20),  -- approved, rejected, corrected, caution
    corrected_answer TEXT,
    feedback_at TIMESTAMP,
    is_reflected BOOLEAN DEFAULT FALSE,  -- feedback → KB sync tracking

    -- Metadata
    is_high_risk BOOLEAN DEFAULT FALSE,
    matched_rule_id INT REFERENCES rules(id),

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for QA history
CREATE INDEX IF NOT EXISTS qa_history_workspace_idx ON qa_history(workspace_id);
CREATE INDEX IF NOT EXISTS qa_history_review_status_idx ON qa_history(workspace_id, review_status);
CREATE INDEX IF NOT EXISTS qa_history_created_at_idx ON qa_history(workspace_id, created_at);

-- Weekly stats table (aggregated statistics)
CREATE TABLE IF NOT EXISTS weekly_stats (
    id SERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    total_questions INT DEFAULT 0,
    review_requests INT DEFAULT 0,
    feedback_completed INT DEFAULT 0,
    feedback_approved INT DEFAULT 0,
    feedback_rejected INT DEFAULT 0,
    feedback_corrected INT DEFAULT 0,
    feedback_caution INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workspace_id, week_start)
);

-- Ingestion jobs table (tracks data ingestion progress)
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed
    total_channels INT DEFAULT 0,
    processed_channels INT DEFAULT 0,
    total_messages INT DEFAULT 0,
    processed_messages INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rules_updated_at
    BEFORE UPDATE ON rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Embeddings table (pgvector — stores vectorized message chunks)
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    channel_id VARCHAR(64),
    message_ts VARCHAR(64),
    thread_ts VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for workspace lookup
CREATE INDEX IF NOT EXISTS embeddings_workspace_idx ON embeddings(workspace_id);

-- IVFFlat index for fast similarity search
CREATE INDEX IF NOT EXISTS embeddings_ivfflat_idx
ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

DO $$
BEGIN
    RAISE NOTICE 'Slough.ai database initialized successfully!';
END $$;
