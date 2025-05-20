#!/usr/bin/env python3
"""
Initialize the SQLite database with the required schema
"""

import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('init_db')

# Paths
DB_PATH = 'search.db'

def init_db():
    """Initialize the SQLite database with required tables"""
    
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create links table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        status TEXT DEFAULT 'pending',
        discovered_at TIMESTAMP,
        last_processed_at TIMESTAMP NULL,
        is_deleted BOOLEAN DEFAULT 0
    )
    ''')
    
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link_id INTEGER UNIQUE,
        title TEXT,
        content TEXT,
        processed_at TIMESTAMP,
        FOREIGN KEY (link_id) REFERENCES links (id)
    )
    ''')
    
    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # Create FTS5 virtual table for content search
    try:
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        ''')
        logger.info("FTS5 extension is enabled and virtual table created")
    except sqlite3.Error as e:
        # Raise error if FTS5 is not available
        error_msg = f"FTS5 extension is required but not available: {e}"
        logger.error(error_msg)
        conn.close()
        raise RuntimeError(error_msg)
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized at {DB_PATH}")
    return True

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH}")
    print("You can now add content using the scraper:")
    print("  python scrapers/simple_scraper.py --links_file scrapers/links.json")