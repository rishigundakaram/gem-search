"""
Test module for the improved scraper functionality with Trafilatura.
"""

import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path so we can import the scraper module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.scraper import discover_links, fetch_and_parse, scrape_links_to_database  # noqa: E402


class TestTrafilaturaIntegration:
    """Test the Trafilatura integration for improved text extraction."""

    def test_fetch_and_parse_with_valid_html(self) -> None:
        """Test that fetch_and_parse works with valid HTML content."""
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <main>
                    <h1>Main Article Title</h1>
                    <p>This is the main content of the article. It should be extracted properly by Trafilatura.</p>
                    <p>Additional paragraph with more meaningful content.</p>
                </main>
                <footer>This is footer content that should be filtered out.</footer>
            </body>
        </html>
        """

        with (
            patch("trafilatura.fetch_url") as mock_fetch,
            patch("trafilatura.extract") as mock_extract,
            patch("trafilatura.extract_metadata") as mock_metadata,
        ):

            mock_fetch.return_value = mock_html
            mock_extract.return_value = "Main Article Title\nThis is the main content of the article. It should be extracted properly by Trafilatura.\nAdditional paragraph with more meaningful content."

            # Mock metadata response
            mock_meta = MagicMock()
            mock_meta.title = "Test Article"
            mock_meta.sitename = "Test Site"
            mock_metadata.return_value = mock_meta

            title, content = fetch_and_parse("https://example.com/test")

            assert title == "Test Article"
            assert content is not None
            assert "main content of the article" in content
            assert "footer content" not in content
            assert len(content) > 50

    def test_fetch_and_parse_fallback_to_newspaper(self) -> None:
        """Test that the function falls back to newspaper3k when Trafilatura fails."""
        with (
            patch("trafilatura.fetch_url") as mock_fetch,
            patch("app.scraper.Article") as mock_article_class,
        ):

            # Make Trafilatura fail
            mock_fetch.side_effect = Exception("Trafilatura failed")

            # Mock newspaper3k Article
            mock_article = MagicMock()
            mock_article.title = "Newspaper Article"
            mock_article.text = "This is content extracted by newspaper3k fallback mechanism."
            mock_article_class.return_value = mock_article

            title, content = fetch_and_parse("https://example.com/test")

            assert title == "Newspaper Article"
            assert content == "This is content extracted by newspaper3k fallback mechanism."

    def test_fetch_and_parse_plain_text_fallback(self) -> None:
        """Test that the function handles plain text files as final fallback."""
        with (
            patch("trafilatura.fetch_url") as mock_trafilatura_fetch,
            patch("app.scraper.Article") as mock_article_class,
            patch("requests.get") as mock_requests,
        ):

            # Make Trafilatura and newspaper3k fail
            mock_trafilatura_fetch.side_effect = Exception("Trafilatura failed")
            mock_article_class.side_effect = Exception("Newspaper failed")

            # Mock requests response for plain text
            mock_response = MagicMock()
            mock_response.headers = {"content-type": "text/plain"}
            mock_response.text = (
                "This is plain text content that should be extracted directly from the response."
            )
            mock_response.raise_for_status.return_value = None
            mock_requests.return_value = mock_response

            title, content = fetch_and_parse("https://example.com/document.txt")

            assert title == "document.txt"
            assert (
                content
                == "This is plain text content that should be extracted directly from the response."
            )

    def test_fetch_and_parse_invalid_content(self) -> None:
        """Test that the function returns None for invalid or empty content."""
        with (
            patch("trafilatura.fetch_url") as mock_fetch,
            patch("trafilatura.extract") as mock_extract,
        ):

            mock_fetch.return_value = "<html><body></body></html>"
            mock_extract.return_value = ""  # Empty content

            title, content = fetch_and_parse("https://example.com/empty")

            assert title is None
            assert content is None

    def test_fetch_and_parse_content_too_short(self) -> None:
        """Test that content shorter than 50 characters is rejected."""
        with (
            patch("trafilatura.fetch_url") as mock_fetch,
            patch("trafilatura.extract") as mock_extract,
        ):

            mock_fetch.return_value = "<html><body>Short</body></html>"
            mock_extract.return_value = "Short"  # Too short

            title, content = fetch_and_parse("https://example.com/short")

            assert title is None
            assert content is None


class TestScrapingWorkflow:
    """Test the complete scraping workflow with database integration."""

    def setup_method(self) -> None:
        """Set up a temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Initialize the database with proper schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create documents table
        cursor.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT
            )
        """
        )

        # Create FTS5 virtual table
        cursor.execute(
            """
            CREATE VIRTUAL TABLE document_content USING fts5(
                content,
                document_id UNINDEXED,
                tokenize='porter unicode61'
            )
        """
        )

        conn.commit()
        conn.close()

    def teardown_method(self) -> None:
        """Clean up the temporary database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_scrape_links_to_database_success(self) -> None:
        """Test successful scraping and storage to database."""
        # Create a temporary links file
        temp_links = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        temp_links.write('["https://example.com/test1", "https://example.com/test2"]')
        temp_links.close()

        try:
            with patch("app.scraper.fetch_and_parse") as mock_fetch:
                mock_fetch.side_effect = [
                    (
                        "Test Article 1",
                        "This is the content of test article 1 with sufficient length to pass validation.",
                    ),
                    (
                        "Test Article 2",
                        "This is the content of test article 2 with sufficient length to pass validation.",
                    ),
                ]

                result = scrape_links_to_database(temp_links.name, self.db_path)

                assert result == 2  # Two new documents added

                # Verify database contents
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                assert count == 2

                cursor.execute("SELECT title, content FROM documents ORDER BY id")
                results = cursor.fetchall()
                assert results[0][0] == "Test Article 1"
                assert "test article 1" in results[0][1]
                assert results[1][0] == "Test Article 2"
                assert "test article 2" in results[1][1]

                conn.close()

        finally:
            os.unlink(temp_links.name)

    def test_scrape_links_duplicate_handling(self) -> None:
        """Test that duplicate URLs are not added to the database."""
        # First, add a document
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (url, title, content) VALUES (?, ?, ?)",
            ("https://example.com/test1", "Existing Article", "Existing content"),
        )
        conn.commit()
        conn.close()

        # Create a temporary links file with the same URL
        temp_links = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        temp_links.write('["https://example.com/test1", "https://example.com/test2"]')
        temp_links.close()

        try:
            with patch("app.scraper.fetch_and_parse") as mock_fetch:
                mock_fetch.return_value = ("New Article", "New content with sufficient length")

                result = scrape_links_to_database(temp_links.name, self.db_path)

                assert result == 1  # Only one new document (the duplicate was skipped)

                # Verify database contents
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                assert count == 2  # Original + 1 new
                conn.close()

        finally:
            os.unlink(temp_links.name)


class TestLinkDiscovery:
    """Test the link discovery functionality."""

    def test_discover_links_same_domain(self) -> None:
        """Test link discovery within the same domain."""
        mock_html = """
        <html>
            <body>
                <a href="/page1">Internal Link 1</a>
                <a href="/page2">Internal Link 2</a>
                <a href="https://example.com/page3">Internal Link 3</a>
                <a href="https://other-site.com/page">External Link</a>
                <a href="mailto:test@example.com">Email Link</a>
                <a href="/image.jpg">Image Link</a>
            </body>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_html
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            discovered = discover_links("https://example.com/start", same_domain_only=True)

            # Should discover internal links but not external ones
            expected_urls = {
                "https://example.com/page1",
                "https://example.com/page2",
                "https://example.com/page3",
            }

            assert discovered == expected_urls

    def test_discover_links_cross_domain(self) -> None:
        """Test link discovery across domains."""
        mock_html = """
        <html>
            <body>
                <a href="https://example.com/page1">Internal Link</a>
                <a href="https://other-site.com/page">External Link</a>
            </body>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = mock_html
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            discovered = discover_links("https://example.com/start", same_domain_only=False)

            # Should discover both internal and external links
            expected_urls = {"https://example.com/page1", "https://other-site.com/page"}

            assert discovered == expected_urls


@pytest.mark.integration
class TestRealWebsiteExtraction:
    """Integration tests with real websites (can be skipped in CI)."""

    @pytest.mark.skip(reason="Integration test - requires internet connection")
    def test_extract_from_real_website(self) -> None:
        """Test extraction from a real website."""
        # Test with a stable, simple website
        title, content = fetch_and_parse("https://httpbin.org/html")

        assert title is not None
        assert content is not None
        assert len(content) > 50
        assert "Herman Melville" in content  # httpbin.org/html contains Moby Dick excerpt


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
