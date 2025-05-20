"""Tests for the link discovery module."""

import pytest
import responses
from urllib.parse import urljoin

from crawler.discovery import LinkDiscoverer

@pytest.fixture
def discoverer():
    """Create a LinkDiscoverer instance."""
    return LinkDiscoverer()

@pytest.fixture
def mock_blog_html():
    """Return mock HTML for a blog homepage."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Blog</title>
    </head>
    <body>
        <div class="header">
            <h1>Test Blog</h1>
        </div>
        <div class="posts">
            <div class="post">
                <h2><a href="/blog/2023/05/20/article1">Article 1</a></h2>
            </div>
            <div class="post">
                <h2><a href="/blog/2023/05/19/article2">Article 2</a></h2>
            </div>
            <div class="post">
                <h2><a href="/blog/2023/05/18/article3">Article 3</a></h2>
            </div>
        </div>
        <div class="sidebar">
            <ul>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
                <li><a href="https://twitter.com/testblog">Twitter</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

class TestLinkDiscoverer:
    """Tests for LinkDiscoverer class."""

    @responses.activate
    def test_get_links_from_url(self, discoverer, mock_blog_html, test_urls):
        """Test getting links from a URL."""
        blog_url = test_urls["blog_home"]
        
        # Mock the response
        responses.add(
            responses.GET,
            blog_url,
            body=mock_blog_html,
            status=200,
            content_type="text/html"
        )
        
        # Test the method
        links = discoverer.get_links_from_url(blog_url)
        
        # Check results
        assert len(links) > 0
        assert any("/blog/" in link for link in links)
        
        # Check that all links have the base domain
        base_domain = blog_url.split("//")[1].split("/")[0]
        for link in links:
            assert base_domain in link

    @responses.activate
    def test_discover_blog_links(self, discoverer, mock_blog_html, test_urls):
        """Test discovering blog links from a source URL."""
        blog_url = test_urls["blog_home"]
        
        # Mock the response
        responses.add(
            responses.GET,
            blog_url,
            body=mock_blog_html,
            status=200,
            content_type="text/html"
        )
        
        # Test the method
        blog_links = discoverer.discover_blog_links(blog_url)
        
        # Check results
        assert len(blog_links) > 0
        
        # All returned links should have blog indicators or date patterns
        for link in blog_links:
            assert "/blog/" in link or "/2023/" in link
            
        # About and contact pages should be filtered out
        about_url = urljoin(blog_url, "/about")
        contact_url = urljoin(blog_url, "/contact")
        assert about_url not in blog_links
        assert contact_url not in blog_links

    @responses.activate
    def test_error_handling(self, discoverer):
        """Test error handling in link discovery."""
        # Mock a request that fails
        bad_url = "https://nonexistent.example.com"
        responses.add(
            responses.GET,
            bad_url,
            status=404
        )
        
        # Should return empty list on error
        links = discoverer.get_links_from_url(bad_url)
        assert isinstance(links, list)
        assert len(links) == 0