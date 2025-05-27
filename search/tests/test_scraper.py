import pytest
import sqlite3
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.scraper import fetch_and_parse, scrape_links_to_database
from app.database import init_database


class TestScraper:
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def temp_links_file(self):
        """Create a temporary links JSON file for testing."""
        test_links = [
            "https://example.com/article1",
            "https://example.com/article2"
        ]
        fd, links_path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(test_links, f)
        yield links_path
        os.unlink(links_path)
    
    def test_init_database_creates_tables(self, temp_db):
        """Test that init_database creates the required tables."""
        conn = init_database(temp_db)
        cursor = conn.cursor()
        
        # Check that documents table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        assert cursor.fetchone() is not None
        
        # Check that FTS5 table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_content'")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_init_database_table_schema(self, temp_db):
        """Test that the documents table has the correct schema."""
        conn = init_database(temp_db)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(documents)")
        columns = cursor.fetchall()
        
        # Check expected columns exist
        column_names = [col[1] for col in columns]
        expected_columns = ['id', 'url', 'title', 'content']
        
        for col in expected_columns:
            assert col in column_names
        
        conn.close()
    
    @patch('app.scraper.Article')
    def test_fetch_and_parse_success(self, mock_article_class):
        """Test successful article fetching and parsing."""
        # Mock the Article class
        mock_article = MagicMock()
        mock_article.title = "Test Article"
        mock_article.text = "This is test content for the article."
        mock_article_class.return_value = mock_article
        
        title, content = fetch_and_parse("https://example.com/test")
        
        assert title == "Test Article"
        assert content == "This is test content for the article."
        mock_article.download.assert_called_once()
        mock_article.parse.assert_called_once()
    
    @patch('app.scraper.Article')
    def test_fetch_and_parse_failure(self, mock_article_class):
        """Test fetch_and_parse handles exceptions gracefully."""
        # Mock Article to raise an exception
        mock_article_class.side_effect = Exception("Network error")
        
        title, content = fetch_and_parse("https://example.com/test")
        
        assert title is None
        assert content is None
    
    @patch('app.scraper.fetch_and_parse')
    def test_scraper_processes_new_links(self, mock_fetch, temp_db, temp_links_file):
        """Test that scraper processes new links correctly."""
        # Initialize database first
        init_database(temp_db)
        
        # Mock successful fetch
        mock_fetch.return_value = ("Test Title", "Test content with enough length to be meaningful")
        
        # Run scraper
        count = scrape_links_to_database(temp_links_file, temp_db)
        
        assert count == 2  # Should have processed 2 links
        
        # Check that documents were inserted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        assert doc_count == 2
        
        # Check FTS5 table was populated
        cursor.execute("SELECT COUNT(*) FROM document_content")
        fts_count = cursor.fetchone()[0]
        assert fts_count == 2
        
        conn.close()
    
    @patch('app.scraper.fetch_and_parse')
    def test_scraper_skips_existing_urls(self, mock_fetch, temp_db, temp_links_file):
        """Test that scraper skips URLs that already exist in the database."""
        # Initialize database first
        init_database(temp_db)
        
        # Mock successful fetch
        mock_fetch.return_value = ("Test Title", "Test content")
        
        # Run scraper twice
        count1 = scrape_links_to_database(temp_links_file, temp_db)
        count2 = scrape_links_to_database(temp_links_file, temp_db)
        
        assert count1 == 2  # First run should process 2 links
        assert count2 == 0  # Second run should skip all links
        
        # Should still only have 2 documents (no duplicates)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        
        assert count == 2
        conn.close()
    
    @patch('app.scraper.fetch_and_parse')
    def test_scraper_skips_articles_with_insufficient_content(self, mock_fetch, temp_db, temp_links_file):
        """Test that scraper skips articles with no title or content."""
        # Initialize database first
        init_database(temp_db)
        
        # Mock fetch returning None or empty content
        mock_fetch.return_value = (None, None)
        
        count = scrape_links_to_database(temp_links_file, temp_db)
        
        assert count == 0  # Should have processed 0 links
        
        # Should have no documents
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        assert doc_count == 0
        conn.close()
    
    def test_scraper_with_nonexistent_file(self, temp_db):
        """Test that scraper handles nonexistent links file gracefully."""
        with pytest.raises(FileNotFoundError):
            scrape_links_to_database("nonexistent.json", temp_db)