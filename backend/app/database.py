"""
Database module for Gem Search.
Handles SQLite database setup, sessions, and FTS5 initialization.
"""

import os
import sqlite3

import sqlite_vec
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///search.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Needed for SQLite

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database(db_path="search.db"):
    """Initialize the complete database with tables, FTS5, and vector support."""
    conn = sqlite3.connect(db_path)
    
    # Enable sqlite-vec extension
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    
    cursor = conn.cursor()

    # Create documents table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT
    )
    """
    )

    # Create FTS5 virtual table
    try:
        cursor.execute(
            """
        CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        """
        )
        print("Database initialized successfully with FTS5 support")
    except sqlite3.Error as e:
        error_msg = f"FTS5 extension is required but not available: {e}"
        print(error_msg)
        conn.close()
        raise RuntimeError(error_msg) from e

    # Create embeddings table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS document_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        embedding_model TEXT NOT NULL DEFAULT 'embedding-model-1024d',
        embedding BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """
    )

    # Create unique index for embeddings
    cursor.execute(
        """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_document_embeddings_doc_model 
    ON document_embeddings(document_id, embedding_model)
    """
    )

    # Create vector index for similarity search
    try:
        cursor.execute(
            """
        CREATE VIRTUAL TABLE IF NOT EXISTS document_vectors USING vec0(
            embedding float[1024],
            document_id INTEGER
        )
        """
        )
        print("Database initialized successfully with vector support")
    except sqlite3.Error as e:
        error_msg = f"sqlite-vec extension is required but not available: {e}"
        print(error_msg)
        conn.close()
        raise RuntimeError(error_msg) from e

    conn.commit()
    return conn
