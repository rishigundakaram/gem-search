-- Rollback embeddings migration
-- Remove vector embeddings tables and indexes

-- Drop vector index first
DROP TABLE IF EXISTS document_vectors;

-- Drop indexes
DROP INDEX IF EXISTS idx_document_embeddings_doc_model;

-- Drop embeddings table
DROP TABLE IF EXISTS document_embeddings;

-- step: 002_add_embeddings_rollback