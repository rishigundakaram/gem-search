import os
import json
import logging
from datetime import datetime
from newspaper import Article
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.models import Source, Link, Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scraper')

class Scraper:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
    
    def fetch_and_parse(self, url):
        """Fetch and parse a URL using newspaper3k."""
        try:
            logger.info(f"Processing URL: {url}")
            article = Article(url)
            article.download()
            article.parse()
            
            title = article.title
            full_text = article.text
            
            if not title or not full_text:
                logger.warning(f"Empty title or content for URL: {url}")
                return None, None
            
            return title, full_text
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return None, None
    
    def add_source(self, name, base_url, description=""):
        """Add a new source to the database."""
        session = self.Session()
        try:
            # Check if source already exists
            existing = session.query(Source).filter_by(base_url=base_url).first()
            if existing:
                logger.info(f"Source {name} already exists with ID {existing.id}")
                session.close()
                return existing.id
            
            # Create new source
            source = Source(
                name=name,
                base_url=base_url,
                description=description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(source)
            session.commit()
            logger.info(f"Added new source: {name} with ID {source.id}")
            return source.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding source {name}: {e}")
            return None
        finally:
            session.close()
    
    def add_link(self, url, source_id=None):
        """Add a new link to the database."""
        session = self.Session()
        try:
            # Check if link already exists
            existing = session.query(Link).filter_by(url=url).first()
            if existing:
                # If link exists but is marked as deleted, undelete it
                if existing.is_deleted:
                    existing.is_deleted = False
                    existing.deleted_at = None
                    session.commit()
                    logger.info(f"Un-deleted link: {url}")
                else:
                    logger.info(f"Link already exists: {url}")
                session.close()
                return existing.id
            
            # Create new link
            link = Link(
                url=url,
                source_id=source_id,
                status='pending',
                discovered_at=datetime.utcnow(),
                is_deleted=False
            )
            session.add(link)
            session.commit()
            logger.info(f"Added new link: {url} with ID {link.id}")
            return link.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding link {url}: {e}")
            return None
        finally:
            session.close()
    
    def process_link(self, link_id):
        """Process a link and store its content."""
        session = self.Session()
        try:
            # Get the link
            link = session.query(Link).filter_by(id=link_id).first()
            if not link:
                logger.error(f"Link ID {link_id} not found")
                return False
            
            # Skip if already processed
            if link.status == 'processed':
                logger.info(f"Link {link.url} already processed")
                return True
            
            # Skip if deleted
            if link.is_deleted:
                logger.info(f"Link {link.url} is deleted, skipping")
                return False
            
            # Fetch and parse
            title, content = self.fetch_and_parse(link.url)
            if not title or not content:
                link.status = 'failed'
                session.commit()
                return False
            
            # Check if document already exists
            existing_doc = session.query(Document).filter_by(link_id=link_id).first()
            if existing_doc:
                # Update existing document
                existing_doc.title = title
                existing_doc.content = content
                existing_doc.updated_at = datetime.utcnow()
                doc_id = existing_doc.id
                logger.info(f"Updated document for link {link.url}")
            else:
                # Create new document
                document = Document(
                    link_id=link_id,
                    title=title,
                    content=content,
                    processed_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(document)
                session.flush()  # Generate ID
                doc_id = document.id
                logger.info(f"Created document for link {link.url}")
            
            # Update FTS index
            # First, delete any existing entries
            session.execute(text(
                "DELETE FROM document_content WHERE document_id = :doc_id"
            ), {"doc_id": doc_id})
            
            # Insert new content
            session.execute(text(
                "INSERT INTO document_content (document_id, content) VALUES (:doc_id, :content)"
            ), {"doc_id": doc_id, "content": content})
            
            # Update link status
            link.status = 'processed'
            link.last_processed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Successfully processed link {link.url}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing link ID {link_id}: {e}")
            return False
        finally:
            session.close()
    
    def delete_link(self, url):
        """Soft delete a link."""
        session = self.Session()
        try:
            link = session.query(Link).filter_by(url=url).first()
            if not link:
                logger.warning(f"Link not found for deletion: {url}")
                return False
            
            link.is_deleted = True
            link.deleted_at = datetime.utcnow()
            session.commit()
            logger.info(f"Soft deleted link: {url}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error soft deleting link {url}: {e}")
            return False
        finally:
            session.close()
    
    def process_links_from_json(self, json_file, source_name=None, source_url=None):
        """Process all links from a JSON file."""
        if not os.path.exists(json_file):
            logger.error(f"JSON file not found: {json_file}")
            return False
        
        try:
            with open(json_file, 'r') as f:
                links = json.load(f)
            
            logger.info(f"Found {len(links)} links in {json_file}")
            
            # Add source if provided
            source_id = None
            if source_name and source_url:
                source_id = self.add_source(source_name, source_url)
            
            # Add all links first
            link_ids = []
            for url in links:
                link_id = self.add_link(url, source_id)
                if link_id:
                    link_ids.append(link_id)
            
            # Then process all links
            success_count = 0
            for link_id in link_ids:
                if self.process_link(link_id):
                    success_count += 1
            
            logger.info(f"Processed {success_count} out of {len(links)} links")
            return True
        except Exception as e:
            logger.error(f"Error processing links from {json_file}: {e}")
            return False
    
    def get_pending_links(self, limit=10):
        """Get a list of pending links."""
        session = self.Session()
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process links and store in SQLite database.')
    parser.add_argument('--links_file', type=str, help='JSON file containing links')
    parser.add_argument('--db_path', type=str, default='../search.db', help='SQLite database path')
    parser.add_argument('--source_name', type=str, help='Source name')
    parser.add_argument('--source_url', type=str, help='Source base URL')
    parser.add_argument('--delete', type=str, help='URL to soft delete')
    parser.add_argument('--process_pending', action='store_true', help='Process pending links')
    
    args = parser.parse_args()
    
    scraper = Scraper(args.db_path)
    
    if args.delete:
        scraper.delete_link(args.delete)
    elif args.process_pending:
        pending_links = scraper.get_pending_links()
        for link_id, url in pending_links:
            logger.info(f"Processing pending link: {url}")
            scraper.process_link(link_id)
    elif args.links_file:
        scraper.process_links_from_json(
            args.links_file,
            args.source_name,
            args.source_url
        )
    else:
        parser.print_help()