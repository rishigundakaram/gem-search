-- Add vector embeddings support
-- Create embeddings table and vector index using sqlite-vec

-- Load sqlite-vec extension
.load sqlite_vec

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

-- Create vector index for similarity search using sqlite-vec
-- Using 1024 dimensions for future embedding model
CREATE VIRTUAL TABLE IF NOT EXISTS document_vectors USING vec0(
    embedding float[1024],
    document_id INTEGER
);

-- step: 002_add_embeddings