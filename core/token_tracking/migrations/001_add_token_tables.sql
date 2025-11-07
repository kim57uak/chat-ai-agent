-- Token Tracking Enhancement Migration
-- Version: 001
-- Description: Add comprehensive token tracking tables

-- 1. Token Usage Table (detailed per-message tracking)
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    message_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Tracking dimensions
    chat_mode TEXT NOT NULL,           -- 'simple', 'tool', 'rag'
    model_name TEXT NOT NULL,          -- 'gemini-2.0-flash', 'gpt-4', etc.
    agent_name TEXT,                   -- 'RAGAgent', 'MCPAgent', NULL for non-RAG
    
    -- Token counts
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    
    -- Cost
    cost_usd REAL NOT NULL,
    
    -- Metadata
    duration_ms REAL,
    tool_calls TEXT,                   -- JSON array of tool names
    additional_info TEXT,              -- JSON for extra data
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_token_usage_session ON token_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_mode ON token_usage(chat_mode);
CREATE INDEX IF NOT EXISTS idx_token_usage_model ON token_usage(model_name);
CREATE INDEX IF NOT EXISTS idx_token_usage_agent ON token_usage(agent_name);

-- 2. Session Token Summary (aggregated per-session)
CREATE TABLE IF NOT EXISTS session_token_summary (
    session_id INTEGER PRIMARY KEY,
    
    -- Totals
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    
    -- Breakdowns (JSON)
    mode_breakdown TEXT,               -- {"simple": 100, "tool": 200, "rag": 300}
    model_breakdown TEXT,              -- {"gpt-4": 100, "gemini": 200}
    agent_breakdown TEXT,              -- {"RAGAgent": 100, "MCPAgent": 200}
    
    -- Timestamps
    first_message_at DATETIME,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- 3. Global Token Stats (daily aggregation)
CREATE TABLE IF NOT EXISTS global_token_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE UNIQUE NOT NULL,
    
    -- Daily totals
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    
    -- Breakdowns (JSON)
    mode_breakdown TEXT,
    model_breakdown TEXT,
    agent_breakdown TEXT,
    
    -- Metadata
    session_count INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_global_stats_date ON global_token_stats(stat_date);

-- Migration metadata
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO migration_history (version, description) 
VALUES ('001', 'Add comprehensive token tracking tables');
