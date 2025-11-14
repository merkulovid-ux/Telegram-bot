

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    source TEXT,
    loc TEXT,
    content TEXT,
    embedding vector(256)
);

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    command TEXT,
    full_text TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);



CREATE TABLE knowledge_base_topics (
    id SERIAL PRIMARY KEY,
    category TEXT,
    topic TEXT
);