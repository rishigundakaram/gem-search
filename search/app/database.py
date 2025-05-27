"""
Database module for Gem Search.
Handles SQLite database setup, sessions, and FTS5 initialization.
"""
import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///search.db')

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

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
    """Initialize the complete database with tables and FTS5."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT
    )
    ''')
    
    # Create FTS5 virtual table
    try:
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        ''')
        print("Database initialized successfully with FTS5 support")
    except sqlite3.Error as e:
        error_msg = f"FTS5 extension is required but not available: {e}"
        print(error_msg)
        conn.close()
        raise RuntimeError(error_msg)
    
    conn.commit()
    return conn