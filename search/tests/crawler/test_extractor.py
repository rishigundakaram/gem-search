"""Tests for the content extractor module."""

import pytest
import responses
import newspaper

from crawler.extractor import ContentExtractor

@pytest.fixture
def extractor():
    """Create a ContentExtractor instance."""
    return ContentExtractor()

# Mock Article.download and Article.parse methods to not make real HTTP requests
@pytest.fixture(autouse=True)
def mock_newspaper(monkeypatch, test_html_article):
    """Mock newspaper3k Article class for testing."""
    
    original_init = newspaper.Article.__init__
    original_download = newspaper.Article.download
    original_parse = newspaper.Article.parse
    
    def mock_init(self, url, *args, **kwargs):
        original_init(self, url, *args, **kwargs)
        self._mock_html = test_html_article
    
    def mock_download(self):
        self.html = self._mock_html
        self.download_state = 2  # Downloaded
    
    def mock_parse(self):
        original_parse(self)
        self.title = "Test Article Heading"
        self.text = "This is the first paragraph of test content. This is the second paragraph with more detailed information. This is the third paragraph concluding the article."
        self.authors = ["John Doe"]
        self.publish_date = "2023-05-20"
        self.top_image = "https://example.com/image.jpg"
        self.meta_lang = "en"
    
    monkeypatch.setattr(newspaper.Article, "__init__", mock_init)
    monkeypatch.setattr(newspaper.Article, "download", mock_download)
    monkeypatch.setattr(newspaper.Article, "parse", mock_parse)

class TestContentExtractor:
    """Tests for ContentExtractor class."""

    @responses.activate
    def test_extract_with_newspaper(self, extractor, test_urls):
        """Test extracting content using newspaper3k."""
        url = test_urls["article"]
        
        # Test extraction
        title, content, metadata = extractor.extract_with_newspaper(url)
        
        # Check results
        assert title == "Test Article Heading"
        assert "first paragraph" in content
        assert "third paragraph" in content
        assert metadata["authors"] == ["John Doe"]
        assert metadata["publish_date"] == "2023-05-20"
        assert metadata["top_image"] == "https://example.com/image.jpg"
        assert metadata["language"] == "en"

    @responses.activate
    def test_extract_with_custom(self, extractor, test_html_article, test_urls):
        """Test extracting content using custom method."""
        url = test_urls["article"]
        
        # Mock the response
        responses.add(
            responses.GET,
            url,
            body=test_html_article,
            status=200,
            content_type="text/html"
        )
        
        # Test extraction
        title, content, metadata = extractor.extract_with_custom(url)
        
        # Check results
        assert "Test Article" in title
        assert "first paragraph" in content
        assert "third paragraph" in content
        assert len(metadata["authors"]) > 0
        assert "John Doe" in metadata["authors"][0]
        assert "2023-05-20" in str(metadata["publish_date"])
        assert "example.com/image.jpg" in str(metadata["top_image"])

    @responses.activate
    def test_extract(self, extractor, test_html_article, test_urls):
        """Test the main extract method which combines approaches."""
        url = test_urls["article"]
        
        # Mock the response
        responses.add(
            responses.GET,
            url,
            body=test_html_article,
            status=200,
            content_type="text/html"
        )
        
        # Test extraction
        title, content, metadata = extractor.extract(url)
        
        # Check results
        assert title is not None
        assert len(title) > 0
        assert content is not None
        assert len(content) > 0
        assert "first paragraph" in content
        assert "third paragraph" in content
        assert "stats" in metadata
        assert metadata["stats"]["content_length"] > 0
        assert metadata["stats"]["title_length"] > 0
        assert metadata["stats"]["has_author"]
        assert metadata["stats"]["has_date"]
        assert metadata["stats"]["has_image"]

    @responses.activate
    def test_error_handling(self, extractor):
        """Test error handling in content extraction."""
        # Mock a request that fails
        bad_url = "https://nonexistent.example.com"
        responses.add(
            responses.GET,
            bad_url,
            status=404
        )
        
        # Custom extraction should handle error
        title, content, metadata = extractor.extract_with_custom(bad_url)
        assert title is None
        assert content is None
        assert metadata == {}
        
        # The main extract method should still try both and handle errors
        title, content, metadata = extractor.extract(bad_url)
        assert metadata["stats"]["content_length"] == 0