-- Add vector embeddings support
-- Create embeddings table and vector index using sqlite-vec
-- Note: sqlite-vec extension must be loaded by the application

-- Create embeddings table to store document vectors
CREATE TABLE IF NOT EXISTS document_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    embedding_model TEXT NOT NULL DEFAULT 'embedding-model-1024d',
    embedding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Create unique index to prevent duplicate embeddings for same document/model
CREATE UNIQUE INDEX IF NOT EXISTS idx_document_embeddings_doc_model 
ON document_embeddings(document_id, embedding_model);

-- Vector table creation moved to 003_create_vector_table.py
-- This allows proper extension loading before table creation

-- step: 002_add_embeddings