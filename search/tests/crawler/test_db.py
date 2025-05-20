"""Tests for the database module."""

import pytest
from datetime import datetime
from sqlalchemy import text

from db.models import Source, Link, Document
from crawler.db import DatabaseHandler

class TestDatabaseHandler:
    """Tests for DatabaseHandler class."""

    def test_get_or_create_source(self, db_handler, test_db_session):
        """Test creating and retrieving a source."""
        # Create a new source
        url = "https://blog.example.com"
        source_id = db_handler.get_or_create_source(url, "Example Blog", "A test blog")
        
        # Check that source was created
        assert source_id is not None
        assert source_id > 0
        
        # Check that source exists in database
        source = test_db_session.query(Source).filter_by(id=source_id).first()
        assert source is not None
        assert source.base_url == url
        assert source.name == "Example Blog"
        assert source.description == "A test blog"
        
        # Get the same source
        same_id = db_handler.get_or_create_source(url)
        assert same_id == source_id
        
        # Check auto naming
        source_id2 = db_handler.get_or_create_source("https://another-blog.example.com")
        source2 = test_db_session.query(Source).filter_by(id=source_id2).first()
        assert source2.name == "another-blog.example.com"

    def test_add_link(self, db_handler, test_db_session):
        """Test adding links."""
        # Create a source first
        source_id = db_handler.get_or_create_source("https://blog.example.com")
        
        # Add a new link
        url = "https://blog.example.com/article1"
        link_id, is_new = db_handler.add_link(url, source_id)
        
        # Check that link was created
        assert link_id is not None
        assert is_new
        
        # Check that link exists in database
        link = test_db_session.query(Link).filter_by(id=link_id).first()
        assert link is not None
        assert link.url == url
        assert link.source_id == source_id
        assert link.status == "pending"
        assert not link.is_deleted
        
        # Add the same link again
        same_id, is_new = db_handler.add_link(url, source_id)
        assert same_id == link_id
        assert not is_new
        
        # Test undeleting
        link.is_deleted = True
        test_db_session.commit()
        
        undelete_id, is_new = db_handler.add_link(url, source_id)
        assert undelete_id == link_id
        assert not is_new
        
        link = test_db_session.query(Link).filter_by(id=link_id).first()
        assert not link.is_deleted

    def test_add_document(self, db_handler, test_db_session):
        """Test adding documents."""
        # Create a source and link first
        source_id = db_handler.get_or_create_source("https://blog.example.com")
        link_id, _ = db_handler.add_link("https://blog.example.com/article1", source_id)
        
        # Add a document
        title = "Test Article"
        content = "This is test content for the article."
        doc_id = db_handler.add_document(link_id, title, content)
        
        # Check that document was created
        assert doc_id is not None
        
        # Check that document exists in database
        doc = test_db_session.query(Document).filter_by(id=doc_id).first()
        assert doc is not None
        assert doc.link_id == link_id
        assert doc.title == title
        assert doc.content == content
        
        # Check FTS index
        result = test_db_session.execute(text(
            "SELECT * FROM document_content WHERE document_id = :doc_id"
        ), {"doc_id": doc_id}).fetchone()
        assert result is not None
        
        # Check link status
        link = test_db_session.query(Link).filter_by(id=link_id).first()
        assert link.status == "processed"
        assert link.last_processed_at is not None
        
        # Update document
        new_content = "Updated content for the test article."
        db_handler.add_document(link_id, title, new_content)
        
        # Check that document was updated
        doc = test_db_session.query(Document).filter_by(id=doc_id).first()
        assert doc.content == new_content

    def test_get_pending_links(self, db_handler, test_db_session):
        """Test retrieving pending links."""
        # Create a source
        source_id = db_handler.get_or_create_source("https://blog.example.com")
        
        # Add some links with different statuses
        link1_id, _ = db_handler.add_link("https://blog.example.com/article1", source_id)
        link2_id, _ = db_handler.add_link("https://blog.example.com/article2", source_id)
        link3_id, _ = db_handler.add_link("https://blog.example.com/article3", source_id)
        
        # Mark one as processed
        link = test_db_session.query(Link).filter_by(id=link1_id).first()
        link.status = "processed"
        test_db_session.commit()
        
        # Mark one as deleted
        link = test_db_session.query(Link).filter_by(id=link3_id).first()
        link.is_deleted = True
        test_db_session.commit()
        
        # Get pending links
        pending_links = db_handler.get_pending_links()
        
        # Should only include link2
        assert len(pending_links) == 1
        assert pending_links[0][0] == link2_id

    def test_mark_link_failed(self, db_handler, test_db_session):
        """Test marking a link as failed."""
        # Create a source and link
        source_id = db_handler.get_or_create_source("https://blog.example.com")
        link_id, _ = db_handler.add_link("https://blog.example.com/article1", source_id)
        
        # Mark as failed
        success = db_handler.mark_link_failed(link_id, "Test error")
        
        # Check success
        assert success
        
        # Check link status
        link = test_db_session.query(Link).filter_by(id=link_id).first()
        assert link.status == "failed"
        assert link.last_processed_at is not None
        
        # Test non-existent link
        success = db_handler.mark_link_failed(9999)
        assert not success