import os
import json
import logging
from newspaper import Article
import sqlite3
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_scraper')

def init_db(db_path):
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(db_path)
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
    
    # Create FTS5 virtual table for content search
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
        content,
        document_id UNINDEXED,
        tokenize='porter unicode61'
    )
    ''')
    
    conn.commit()
    return conn

def fetch_and_parse(url):
    """Fetch and parse a URL using newspaper3k"""
    try:
        logger.info(f"Processing URL: {url}")
        article = Article(url)
        article.download()
        article.parse()
        
        title = article.title
        content = article.text
        
        if not title or not content:
            logger.warning(f"Empty title or content for URL: {url}")
            return None, None
        
        return title, content
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        return None, None

def add_link(conn, url):
    """Add a link to the database if it doesn't exist"""
    cursor = conn.cursor()
    
    # Check if link already exists
    cursor.execute("SELECT id, is_deleted FROM links WHERE url = ?", (url,))
    existing = cursor.fetchone()
    
    if existing:
        link_id = existing[0]
        is_deleted = existing[1]
        
        if is_deleted:
            # Undelete the link
            cursor.execute(
                "UPDATE links SET is_deleted = 0, status = 'pending' WHERE id = ?", 
                (link_id,)
            )
            conn.commit()
            logger.info(f"Un-deleted link: {url}")
        else:
            logger.info(f"Link already exists: {url}")
        
        return link_id
    
    # Add new link
    cursor.execute(
        "INSERT INTO links (url, status, discovered_at) VALUES (?, ?, ?)",
        (url, 'pending', datetime.utcnow())
    )
    conn.commit()
    link_id = cursor.lastrowid
    logger.info(f"Added new link: {url} with ID {link_id}")
    
    return link_id

def process_link(conn, link_id):
    """Process a link and store its content"""
    cursor = conn.cursor()
    
    # Get the link
    cursor.execute("SELECT url, status, is_deleted FROM links WHERE id = ?", (link_id,))
    link = cursor.fetchone()
    
    if not link:
        logger.error(f"Link ID {link_id} not found")
        return False
    
    url, status, is_deleted = link
    
    # Skip if already processed or deleted
    if status == 'processed':
        logger.info(f"Link {url} already processed")
        return True
    
    if is_deleted:
        logger.info(f"Link {url} is deleted, skipping")
        return False
    
    # Fetch and parse
    title, content = fetch_and_parse(url)
    if not title or not content:
        cursor.execute(
            "UPDATE links SET status = 'failed' WHERE id = ?", 
            (link_id,)
        )
        conn.commit()
        return False
    
    # Check if document already exists
    cursor.execute("SELECT id FROM documents WHERE link_id = ?", (link_id,))
    existing_doc = cursor.fetchone()
    
    timestamp = datetime.utcnow()
    
    if existing_doc:
        # Update existing document
        doc_id = existing_doc[0]
        cursor.execute(
            "UPDATE documents SET title = ?, content = ? WHERE id = ?",
            (title, content, doc_id)
        )
        logger.info(f"Updated document for link {url}")
    else:
        # Create new document
        cursor.execute(
            "INSERT INTO documents (link_id, title, content, processed_at) VALUES (?, ?, ?, ?)",
            (link_id, title, content, timestamp)
        )
        doc_id = cursor.lastrowid
        logger.info(f"Created document for link {url}")
    
    # Update FTS index
    # First, delete any existing entries
    cursor.execute("DELETE FROM document_content WHERE document_id = ?", (doc_id,))
    
    # Insert new content
    cursor.execute(
        "INSERT INTO document_content (document_id, content) VALUES (?, ?)",
        (doc_id, content)
    )
    
    # Update link status
    cursor.execute(
        "UPDATE links SET status = 'processed', last_processed_at = ? WHERE id = ?",
        (timestamp, link_id)
    )
    
    conn.commit()
    logger.info(f"Successfully processed link {url}")
    return True

def process_links_from_json(db_path, json_file):
    """Process all links from a JSON file"""
    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return False
    
    try:
        # Read links from JSON
        with open(json_file, 'r') as f:
            links = json.load(f)
        
        logger.info(f"Found {len(links)} links in {json_file}")
        
        # Initialize database
        conn = init_db(db_path)
        
        # Add and process each link
        success_count = 0
        for url in links:
            link_id = add_link(conn, url)
            if process_link(conn, link_id):
                success_count += 1
        
        logger.info(f"Successfully processed {success_count} out of {len(links)} links")
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Error processing links from {json_file}: {e}")
        return False

def process_pending_links(db_path, limit=10):
    """Process pending links from the database"""
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, url FROM links WHERE status = 'pending' AND is_deleted = 0 LIMIT ?", 
        (limit,)
    )
    
    pending_links = cursor.fetchall()
    logger.info(f"Found {len(pending_links)} pending links to process")
    
    success_count = 0
    for link_id, url in pending_links:
        logger.info(f"Processing pending link: {url}")
        if process_link(conn, link_id):
            success_count += 1
    
    logger.info(f"Successfully processed {success_count} out of {len(pending_links)} links")
    conn.close()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple web scraper for gem-search')
    parser.add_argument('--db_path', type=str, default='../search.db', help='SQLite database path')
    parser.add_argument('--links_file', type=str, help='JSON file containing links to scrape')
    parser.add_argument('--process_pending', action='store_true', help='Process pending links in the database')
    parser.add_argument('--limit', type=int, default=10, help='Limit for pending links to process')
    
    args = parser.parse_args()
    
    if args.links_file:
        process_links_from_json(args.db_path, args.links_file)
    elif args.process_pending:
        process_pending_links(args.db_path, args.limit)
    else:
        parser.print_help()