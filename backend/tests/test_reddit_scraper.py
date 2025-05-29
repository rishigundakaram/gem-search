"""
Test module for the Reddit scraper functionality.
"""

import os
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ruff: noqa: E402
from app.reddit_scraper import (
    extract_urls_from_text,
    filter_reddit_urls,
    get_random_sort_and_time,
    get_random_time_filter,
    get_reddit_posts,
    scrape_reddit_batch,
)


class TestRedditAPI:
    """Test Reddit API interaction functions."""

    def test_get_random_sort_and_time(self) -> None:
        """Test that random sort and time selection works."""
        sort_method, time_filter = get_random_sort_and_time()

        # Should return valid sort methods
        assert sort_method in ["hot", "new", "top", "rising"]

        # If top is selected, should have a time filter
        if sort_method == "top":
            assert time_filter in ["day", "week", "month", "year", "all"]
        else:
            assert time_filter is None

    def test_get_random_time_filter(self) -> None:
        """Test random time filter generation."""
        time_filter = get_random_time_filter()
        assert time_filter in ["day", "week", "month", "year", "all"]

    @patch("requests.get")
    def test_get_reddit_posts_success(self, mock_get: MagicMock) -> None:
        """Test successful Reddit API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "Test Post 1",
                            "url": "https://example.com/post1",
                            "selftext": "This is test content",
                            "score": 100,
                            "created_utc": 1640995200,
                            "permalink": "/r/test/comments/123/test_post_1",
                        }
                    },
                    {
                        "data": {
                            "title": "Test Post 2",
                            "url": "https://example.com/post2",
                            "selftext": "",
                            "score": 50,
                            "created_utc": 1640995300,
                            "permalink": "/r/test/comments/124/test_post_2",
                        }
                    },
                ],
                "after": "test_token",
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        posts, next_after = get_reddit_posts("InternetIsBeautiful", limit=25)

        assert len(posts) == 2
        assert posts[0]["title"] == "Test Post 1"
        assert posts[0]["url"] == "https://example.com/post1"
        assert posts[1]["title"] == "Test Post 2"
        assert next_after == "test_token"

    @patch("requests.get")
    def test_get_reddit_posts_failure(self, mock_get: MagicMock) -> None:
        """Test Reddit API failure handling."""
        mock_get.side_effect = Exception("API Error")

        posts, next_after = get_reddit_posts("InternetIsBeautiful")

        assert posts == []
        assert next_after is None


class TestURLExtraction:
    """Test URL extraction and filtering functions."""

    def test_extract_urls_from_text(self) -> None:
        """Test URL extraction from text."""
        text = """
        Check out these sites:
        https://example.com/page1 and http://test.org/page2
        Also visit https://cool-site.net/article?id=123&ref=reddit
        Email me at test@example.com (not a URL)
        """

        urls = extract_urls_from_text(text)

        expected_urls = {
            "https://example.com/page1",
            "http://test.org/page2",
            "https://cool-site.net/article?id=123&ref=reddit",
        }

        assert urls == expected_urls

    def test_extract_urls_with_trailing_punctuation(self) -> None:
        """Test URL extraction handles trailing punctuation."""
        text = "Visit https://example.com/page, or https://test.org/page!"

        urls = extract_urls_from_text(text)

        expected_urls = {"https://example.com/page", "https://test.org/page"}

        assert urls == expected_urls

    def test_filter_reddit_urls(self) -> None:
        """Test filtering out Reddit and social media URLs."""
        urls = {
            "https://example.com/article",
            "https://reddit.com/r/test",
            "https://www.reddit.com/r/test/comments/123",
            "https://imgur.com/gallery/abc",
            "https://youtube.com/watch?v=123",
            "https://twitter.com/user/status/123",
            "https://cool-site.net/article",
        }

        filtered = filter_reddit_urls(urls)

        expected_filtered = {"https://example.com/article", "https://cool-site.net/article"}

        assert filtered == expected_filtered

    def test_filter_reddit_urls_edge_cases(self) -> None:
        """Test filtering handles edge cases."""
        urls = {
            "https://reddit-like.com/page",  # Should not be filtered
            "https://old.reddit.com/r/test",  # Should be filtered
            "https://m.reddit.com/r/test",  # Should be filtered
            "invalid-url",  # Should be filtered out due to parsing error
        }

        filtered = filter_reddit_urls(urls)

        # Should only keep the valid non-Reddit URL
        # invalid-url gets skipped due to urlparse exception
        expected_filtered = {"https://reddit-like.com/page"}

        assert filtered == expected_filtered


class TestRedditScraper:
    """Test the main Reddit scraper functionality."""

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

    @patch("app.reddit_scraper.get_reddit_posts")
    @patch("asyncio.run")
    def test_scrape_reddit_batch_success(
        self, mock_asyncio_run: MagicMock, mock_get_posts: MagicMock
    ) -> None:
        """Test successful Reddit batch scraping."""
        # Mock Reddit API response
        mock_posts = [
            {
                "title": "Cool Website",
                "url": "https://example.com/cool",
                "selftext": "Check out https://test.org/article",
                "score": 100,
                "created_utc": 1640995200,
                "permalink": "/r/test/comments/123/cool_website",
            }
        ]
        mock_get_posts.return_value = (mock_posts, "next_token")

        # Mock the async scraper to return some results
        mock_asyncio_run.return_value = (1, 2)  # 1 new doc, 2 total discovered

        reddit_urls, new_docs, next_after = scrape_reddit_batch("InternetIsBeautiful", self.db_path)

        # Should have found URLs from both post URL and selftext
        assert reddit_urls == 2  # example.com/cool and test.org/article
        assert new_docs == 1
        assert next_after == "next_token"

        # Verify async scraper was called
        mock_asyncio_run.assert_called_once()

    @patch("app.reddit_scraper.get_reddit_posts")
    def test_scrape_reddit_batch_no_posts(self, mock_get_posts: MagicMock) -> None:
        """Test handling when no Reddit posts are found."""
        mock_get_posts.return_value = ([], None)

        reddit_urls, new_docs, next_after = scrape_reddit_batch("InternetIsBeautiful", self.db_path)

        assert reddit_urls == 0
        assert new_docs == 0
        assert next_after is None

    @patch("app.reddit_scraper.get_reddit_posts")
    @patch("asyncio.run")
    def test_scrape_reddit_batch_filters_reddit_urls(
        self, mock_asyncio_run: MagicMock, mock_get_posts: MagicMock
    ) -> None:
        """Test that Reddit URLs are properly filtered out."""
        # Mock Reddit API response with Reddit URLs
        mock_posts = [
            {
                "title": "Reddit Discussion",
                "url": "https://www.reddit.com/r/programming/comments/123",
                "selftext": "Discussion about https://example.com/article",
                "score": 50,
                "created_utc": 1640995200,
                "permalink": "/r/test/comments/123/reddit_discussion",
            }
        ]
        mock_get_posts.return_value = (mock_posts, None)
        mock_asyncio_run.return_value = (1, 1)

        reddit_urls, new_docs, next_after = scrape_reddit_batch("InternetIsBeautiful", self.db_path)

        # Should only count the non-Reddit URL
        assert reddit_urls == 1  # Only example.com/article
        assert new_docs == 1


class TestConcurrentFeatures:
    """Test concurrent/async features."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db_path = self.temp_db.name

        # Initialize database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
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
        """Clean up."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_concurrent_configuration_constants(self) -> None:
        """Test that concurrent configuration constants are set correctly."""
        from app.reddit_scraper import DEFAULT_DELAY, DEFAULT_PAGES, DISCOVER_DEPTH, MAX_CONCURRENT

        assert MAX_CONCURRENT == 30
        assert DISCOVER_DEPTH == 2
        assert DEFAULT_DELAY == 2
        assert DEFAULT_PAGES == 20


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
