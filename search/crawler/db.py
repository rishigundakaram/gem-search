"""
Database module for the crawler.
Handles database operations related to sources, links, and documents.
"""

from datetime import datetime
import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Source, Link, Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler.db')

class DatabaseHandler:
    def __init__(self):
        """Initialize the database handler."""
        pass
    
    def get_session(self):
        """Get a database session."""
        return SessionLocal()
    
    def get_or_create_source(self, url, name=None, description=None):
        """Get or create a source record for a base URL.
        
        Args:
            url: The base URL of the source
            name: The name of the source (optional)
            description: A description of the source (optional)
            
        Returns:
            int: The source ID
        """
        session = self.get_session()
        try:
            # Extract domain as default name if none provided
            if not name:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                name = domain.replace('www.', '')
            
            # Check if source already exists
            existing = session.query(Source).filter_by(base_url=url).first()
            
            if existing:
                logger.info(f"Source already exists for {url}: {existing.id}")
                return existing.id
            
            # Create new source
            now = datetime.utcnow()
            new_source = Source(
                name=name,
                base_url=url,
                description=description or f"Content from {name}",
                created_at=now,
                updated_at=now
            )
            
            session.add(new_source)
            session.commit()
            session.refresh(new_source)
            
            logger.info(f"Created new source for {url}: {new_source.id}")
            return new_source.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating source for {url}: {e}")
            raise
        finally:
            session.close()
    
    def add_link(self, url, source_id):
        """Add a new link if it doesn't exist.
        
        Args:
            url: The URL to add
            source_id: The ID of the source
            
        Returns:
            tuple: (link_id, is_new)
        """
        session = self.get_session()
        try:
            # Check if link already exists
            existing = session.query(Link).filter_by(url=url).first()
            
            if existing:
                if existing.is_deleted:
                    # Undelete it
                    existing.is_deleted = False
                    existing.deleted_at = None
                    session.commit()
                    logger.info(f"Undeleted link: {url}")
                    return existing.id, False
                
                logger.info(f"Link already exists: {url}")
                return existing.id, False
            
            # Create new link
            now = datetime.utcnow()
            new_link = Link(
                url=url,
                source_id=source_id,
                status='pending',
                discovered_at=now,
                is_deleted=False
            )
            
            session.add(new_link)
            session.commit()
            session.refresh(new_link)
            
            logger.info(f"Added new link: {url} with ID {new_link.id}")
            return new_link.id, True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding link {url}: {e}")
            raise
        finally:
            session.close()
    
    def add_document(self, link_id, title, content, metadata=None):
        """Add a document for a link.
        
        Args:
            link_id: The ID of the link
            title: The document title
            content: The document content
            metadata: Additional metadata (optional)
            
        Returns:
            int: The document ID
        """
        session = self.get_session()
        try:
            # Check if document already exists for this link
            existing = session.query(Document).filter_by(link_id=link_id).first()
            
            now = datetime.utcnow()
            
            if existing:
                # Update existing document
                existing.title = title
                existing.content = content
                existing.updated_at = now
                
                # Update link status
                link = session.query(Link).filter_by(id=link_id).first()
                if link:
                    link.status = 'processed'
                    link.last_processed_at = now
                
                session.commit()
                
                # Update FTS index
                self._update_fts_index(session, existing.id, content)
                
                logger.info(f"Updated document for link ID {link_id}")
                return existing.id
            
            # Create new document
            new_doc = Document(
                link_id=link_id,
                title=title,
                content=content,
                processed_at=now,
                updated_at=now
            )
            
            session.add(new_doc)
            session.flush()  # Get the ID before committing
            
            # Update link status
            link = session.query(Link).filter_by(id=link_id).first()
            if link:
                link.status = 'processed'
                link.last_processed_at = now
            
            session.commit()
            session.refresh(new_doc)
            
            # Update FTS index
            self._update_fts_index(session, new_doc.id, content)
            
            logger.info(f"Added document for link ID {link_id}: {new_doc.id}")
            return new_doc.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding document for link ID {link_id}: {e}")
            raise
        finally:
            session.close()
    
    def _update_fts_index(self, session, doc_id, content):
        """Update the FTS index for a document.
        
        Args:
            session: An active database session
            doc_id: The document ID
            content: The document content
        """
        try:
            # Delete existing entries
            session.execute(text(
                "DELETE FROM document_content WHERE document_id = :doc_id"
            ), {"doc_id": doc_id})
            
            # Insert new content
            session.execute(text(
                "INSERT INTO document_content (document_id, content) VALUES (:doc_id, :content)"
            ), {"doc_id": doc_id, "content": content})
            
            session.commit()
            logger.info(f"Updated FTS index for document ID {doc_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating FTS index for document ID {doc_id}: {e}")
            raise
    
    def get_pending_links(self, limit=50):
        """Get pending links to process.
        
        Args:
            limit: Maximum number of links to return
            
        Returns:
            list: List of (link_id, url) tuples
        """
        session = self.get_session()
        try:
            links = session.query(Link).filter_by(
                status='pending',
                is_deleted=False
            ).limit(limit).all()
            
            return [(link.id, link.url) for link in links]
            
        except Exception as e:
            logger.error(f"Error getting pending links: {e}")
            return []
        finally:
            session.close()
    
    def mark_link_failed(self, link_id, error=None):
        """Mark a link as failed.
        
        Args:
            link_id: The ID of the link
            error: Optional error message
            
        Returns:
            bool: True if successful
        """
        session = self.get_session()
        try:
            link = session.query(Link).filter_by(id=link_id).first()
            
            if not link:
                logger.warning(f"Link ID {link_id} not found")
                return False
            
            link.status = 'failed'
            link.last_processed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Marked link ID {link_id} as failed")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking link ID {link_id} as failed: {e}")
            return False
        finally:
            session.close()


# Simple usage example
if __name__ == "__main__":
    db_handler = DatabaseHandler()
    
    # Create a source
    source_id = db_handler.get_or_create_source(
        "https://engineering.fb.com",
        "Meta Engineering",
        "Technical blog from Meta"
    )
    
    print(f"Source ID: {source_id}")
    
    # Add a link
    link_id, is_new = db_handler.add_link(
        "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/",
        source_id
    )
    
    print(f"Link ID: {link_id} (New: {is_new})")
    
    # Add a document (only for testing)
    if is_new:
        doc_id = db_handler.add_document(
            link_id,
            "How Meta Moved Masses of Data",
            "This is a test document content for the Meta Engineering blog post about moving data."
        )
        print(f"Document ID: {doc_id}")