-- Rollback for initial schema migration

-- Drop FTS5 virtual table
DROP TABLE IF EXISTS document_content;

-- Drop index
DROP INDEX IF EXISTS idx_documents_url;

-- Drop documents table
DROP TABLE IF EXISTS documents;

-- step: 001_initial_schema