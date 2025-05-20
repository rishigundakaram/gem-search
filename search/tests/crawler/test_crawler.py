"""Tests for the main crawler module."""

import os
import json
import tempfile
import pytest
import responses
from unittest.mock import patch, MagicMock

# Import the GemCrawler class - we need to mock some of its dependencies
from crawler.crawler import GemCrawler

@pytest.fixture
def mock_components():
    """Create mock components for the crawler."""
    discoverer = MagicMock()
    classifier = MagicMock()
    extractor = MagicMock()
    db_handler = MagicMock()
    
    return {
        'discoverer': discoverer,
        'classifier': classifier,
        'extractor': extractor,
        'db': db_handler
    }

@pytest.fixture
def crawler(mock_components):
    """Create a GemCrawler with mock components."""
    crawler = GemCrawler(config={'max_links_per_source': 5, 'max_workers': 2})
    
    # Replace components with mocks
    crawler.discoverer = mock_components['discoverer']
    crawler.classifier = mock_components['classifier']
    crawler.extractor = mock_components['extractor']
    crawler.db = mock_components['db']
    
    return crawler

@pytest.fixture
def test_json_file():
    """Create a temporary JSON file with test URLs."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
        test_urls = [
            "https://blog.example.com",
            "https://another.example.com"
        ]
        json.dump(test_urls, f)
        temp_path = f.name
    
    yield temp_path
    
    # Clean up
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestGemCrawler:
    """Tests for GemCrawler class."""

    def test_process_source(self, crawler, mock_components, test_urls):
        """Test processing a single source."""
        source_url = test_urls["blog_home"]
        
        # Configure mocks
        mock_components['db'].get_or_create_source.return_value = 1
        mock_components['discoverer'].discover_blog_links.return_value = [
            "https://blog.example.com/article1",
            "https://blog.example.com/article2"
        ]
        mock_components['classifier'].is_likely_article.return_value = (True, 0.8)
        mock_components['db'].add_link.return_value = (1, True)
        mock_components['extractor'].extract.return_value = (
            "Test Title", "Test Content", {"authors": ["Test Author"]}
        )
        mock_components['db'].add_document.return_value = 1
        
        # Process the source
        stats = crawler.process_source(source_url)
        
        # Check stats
        assert stats["source_url"] == source_url
        assert stats["links_discovered"] == 2
        assert stats["links_processed"] == 2
        assert stats["articles_found"] == 2
        assert stats["errors"] == 0
        
        # Verify mock calls
        mock_components['db'].get_or_create_source.assert_called_once()
        mock_components['discoverer'].discover_blog_links.assert_called_once_with(source_url)
        assert mock_components['classifier'].is_likely_article.call_count == 2
        assert mock_components['db'].add_link.call_count == 2
        assert mock_components['extractor'].extract.call_count == 2
        assert mock_components['db'].add_document.call_count == 2

    def test_process_source_with_errors(self, crawler, mock_components, test_urls):
        """Test processing a source with errors."""
        source_url = test_urls["blog_home"]
        
        # Configure mocks
        mock_components['db'].get_or_create_source.return_value = 1
        mock_components['discoverer'].discover_blog_links.return_value = [
            "https://blog.example.com/article1",
            "https://blog.example.com/article2"
        ]
        
        # First link is an article but extraction fails
        mock_components['classifier'].is_likely_article.side_effect = [
            (True, 0.8),  # First link is article
            (False, 0.3)  # Second link is not article
        ]
        mock_components['db'].add_link.return_value = (1, True)
        mock_components['extractor'].extract.side_effect = Exception("Test error")
        
        # Process the source
        stats = crawler.process_source(source_url)
        
        # Check stats
        assert stats["source_url"] == source_url
        assert stats["links_discovered"] == 2
        assert stats["links_processed"] == 2
        assert stats["articles_found"] == 0
        assert stats["errors"] == 1
        
        # Verify mock calls
        mock_components['db'].get_or_create_source.assert_called_once()
        mock_components['discoverer'].discover_blog_links.assert_called_once_with(source_url)
        assert mock_components['classifier'].is_likely_article.call_count == 2
        assert mock_components['db'].add_link.call_count == 1
        assert mock_components['extractor'].extract.call_count == 1
        assert mock_components['db'].add_document.call_count == 0

    def test_process_sources_from_json(self, crawler, mock_components, test_json_file):
        """Test processing sources from a JSON file."""
        # Configure mocks
        mock_components['db'].get_or_create_source.return_value = 1
        mock_components['discoverer'].discover_blog_links.return_value = [
            "https://blog.example.com/article1"
        ]
        mock_components['classifier'].is_likely_article.return_value = (True, 0.8)
        mock_components['db'].add_link.return_value = (1, True)
        mock_components['extractor'].extract.return_value = (
            "Test Title", "Test Content", {"authors": ["Test Author"]}
        )
        
        # Process sources
        all_stats = crawler.process_sources_from_json(test_json_file)
        
        # Check stats
        assert len(all_stats) == 2  # Two sources in the test file
        for stats in all_stats:
            assert stats["links_discovered"] == 1
            assert stats["articles_found"] == 1
        
        # Verify mock calls
        assert mock_components['db'].get_or_create_source.call_count == 2
        assert mock_components['discoverer'].discover_blog_links.call_count == 2

    def test_process_pending_links(self, crawler, mock_components):
        """Test processing pending links."""
        # Configure mocks
        mock_components['db'].get_pending_links.return_value = [
            (1, "https://blog.example.com/article1"),
            (2, "https://blog.example.com/article2")
        ]
        mock_components['extractor'].extract.return_value = (
            "Test Title", "Test Content", {"authors": ["Test Author"]}
        )
        
        # Process pending links
        stats = crawler.process_pending_links(limit=10)
        
        # Check stats
        assert stats["links_processed"] == 2
        assert stats["articles_found"] == 2
        assert stats["errors"] == 0
        
        # Verify mock calls
        mock_components['db'].get_pending_links.assert_called_once_with(10)
        assert mock_components['extractor'].extract.call_count == 2
        assert mock_components['db'].add_document.call_count == 2

    def test_process_pending_links_with_errors(self, crawler, mock_components):
        """Test processing pending links with errors."""
        # Configure mocks
        mock_components['db'].get_pending_links.return_value = [
            (1, "https://blog.example.com/article1"),
            (2, "https://blog.example.com/article2")
        ]
        
        # First extraction succeeds, second fails
        mock_components['extractor'].extract.side_effect = [
            ("Test Title", "Test Content", {"authors": ["Test Author"]}),
            Exception("Test error")
        ]
        
        # Process pending links
        stats = crawler.process_pending_links(limit=10)
        
        # Check stats
        assert stats["links_processed"] == 2
        assert stats["articles_found"] == 1
        assert stats["errors"] == 1
        
        # Verify mock calls
        mock_components['db'].get_pending_links.assert_called_once_with(10)
        assert mock_components['extractor'].extract.call_count == 2
        assert mock_components['db'].add_document.call_count == 1
        assert mock_components['db'].mark_link_failed.call_count == 1