#!/usr/bin/env python3
"""
Improved scraper with SQLAlchemy integration
Works with the existing database schema and migrations
"""

import json
import logging
import os
import sys
from datetime import datetime
from newspaper import Article
from sqlalchemy.sql import text
import argparse

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from db.database import SessionLocal
from db.models import Link, Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('alembic_scraper')

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

def add_link(db, url):
    """Add a link to the database if it doesn't exist"""
    # Check if link already exists
    existing = db.query(Link).filter(Link.url == url).first()
    
    if existing:
        if existing.is_deleted:
            # Undelete it
            existing.is_deleted = False
            existing.deleted_at = None
            existing.status = 'pending'
            db.commit()
            logger.info(f"Un-deleted link: {url}")
        else:
            logger.info(f"Link already exists: {url}")
        
        return existing.id
    
    # Add new link
    new_link = Link(
        url=url,
        status='pending',
        discovered_at=datetime.utcnow()
    )
    
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    
    logger.info(f"Added new link: {url} with ID {new_link.id}")
    return new_link.id

def process_link(db, link_id):
    """Process a link and store its content"""
    # Get the link
    link = db.query(Link).filter(Link.id == link_id).first()
    
    if not link:
        logger.error(f"Link ID {link_id} not found")
        return False
    
    # Skip if already processed or deleted
    if link.status == 'processed':
        logger.info(f"Link {link.url} already processed")
        return True
    
    if link.is_deleted:
        logger.info(f"Link {link.url} is deleted, skipping")
        return False
    
    # Fetch and parse
    title, content = fetch_and_parse(link.url)
    if not title or not content:
        link.status = 'failed'
        db.commit()
        return False
    
    # Check if document already exists
    existing_doc = db.query(Document).filter(Document.link_id == link_id).first()
    
    now = datetime.utcnow()
    
    if existing_doc:
        # Update existing document
        existing_doc.title = title
        existing_doc.content = content
        existing_doc.updated_at = now
        doc_id = existing_doc.id
        logger.info(f"Updated document for link {link.url}")
    else:
        # Create new document
        new_doc = Document(
            link_id=link_id,
            title=title,
            content=content,
            processed_at=now,
            updated_at=now
        )
        db.add(new_doc)
        db.flush()  # Generate ID
        doc_id = new_doc.id
        logger.info(f"Created document for link {link.url}")
    
    # Update FTS index
    # First, delete any existing entries
    db.execute(text(
        "DELETE FROM document_content WHERE document_id = :doc_id"
    ), {"doc_id": doc_id})
    
    # Insert new content
    db.execute(text(
        "INSERT INTO document_content (document_id, content) VALUES (:doc_id, :content)"
    ), {"doc_id": doc_id, "content": content})
    
    # Update link status
    link.status = 'processed'
    link.last_processed_at = now
    
    db.commit()
    logger.info(f"Successfully processed link {link.url}")
    return True

def process_links_from_json(json_file):
    """Process all links from a JSON file"""
    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return False
    
    try:
        # Read links from JSON
        with open(json_file, 'r') as f:
            links = json.load(f)
        
        logger.info(f"Found {len(links)} links in {json_file}")
        
        # Initialize database session
        db = SessionLocal()
        
        try:
            # Add and process each link
            success_count = 0
            for url in links:
                link_id = add_link(db, url)
                if process_link(db, link_id):
                    success_count += 1
            
            logger.info(f"Successfully processed {success_count} out of {len(links)} links")
            return True
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error processing links from {json_file}: {e}")
        return False

def process_pending_links(limit=10):
    """Process pending links from the database"""
    db = SessionLocal()
    
    try:
        # Get pending links
        pending_links = db.query(Link).filter(
            Link.status == 'pending',
            Link.is_deleted == False
        ).limit(limit).all()
        
        logger.info(f"Found {len(pending_links)} pending links to process")
        
        # Process each link
        success_count = 0
        for link in pending_links:
            logger.info(f"Processing pending link: {link.url}")
            if process_link(db, link.id):
                success_count += 1
        
        logger.info(f"Successfully processed {success_count} out of {len(pending_links)} links")
        return True
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SQLAlchemy-integrated scraper for gem-search')
    parser.add_argument('--links_file', type=str, help='JSON file containing links to scrape')
    parser.add_argument('--process_pending', action='store_true', help='Process pending links in the database')
    parser.add_argument('--limit', type=int, default=10, help='Limit for pending links to process')
    
    args = parser.parse_args()
    
    if args.links_file:
        process_links_from_json(args.links_file)
    elif args.process_pending:
        process_pending_links(args.limit)
    else:
        parser.print_help()