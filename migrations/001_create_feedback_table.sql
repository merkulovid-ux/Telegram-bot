CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    feedback_text TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
