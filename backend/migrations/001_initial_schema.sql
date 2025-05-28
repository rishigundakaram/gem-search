-- Initial schema for gem-search database
-- Create documents table and FTS5 virtual table

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    title TEXT,
    content TEXT
);

-- Create FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
    content,
    document_id UNINDEXED,
    tokenize='porter unicode61'
);

-- Create index on url for faster lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_url ON documents(url);

-- step: 001_initial_schema