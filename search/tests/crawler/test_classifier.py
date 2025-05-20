"""Tests for the article classifier module."""

import pytest
import responses

from crawler.classifier import ArticleClassifier

@pytest.fixture
def classifier():
    """Create an ArticleClassifier instance."""
    return ArticleClassifier()

class TestArticleClassifier:
    """Tests for ArticleClassifier class."""

    def test_is_article_url(self, classifier, test_urls):
        """Test URL-based article classification."""
        # Test article URL with date pattern
        score = classifier.is_article_url(test_urls["article"])
        assert score > 0.0
        
        # Test article URL with date in different format
        score = classifier.is_article_url(test_urls["article_with_date"])
        assert score > 0.0
        
        # Test article URL with blog path
        score = classifier.is_article_url(test_urls["article_with_path"])
        assert score > 0.0
        
        # Test non-article URL
        score = classifier.is_article_url(test_urls["about_page"])
        assert score < 0.3  # Should be a low score
        
        # Test blog home page
        score = classifier.is_article_url(test_urls["blog_home"])
        assert score < 0.3  # Should be a low score

    @responses.activate
    def test_is_article_content(self, classifier, test_html_article, test_html_non_article, test_urls):
        """Test content-based article classification."""
        # Mock article page
        responses.add(
            responses.GET,
            test_urls["article"],
            body=test_html_article,
            status=200,
            content_type="text/html"
        )
        
        # Mock non-article page
        responses.add(
            responses.GET,
            test_urls["about_page"],
            body=test_html_non_article,
            status=200,
            content_type="text/html"
        )
        
        # Test article page
        score = classifier.is_article_content(test_urls["article"])
        assert score > 0.3  # Should be a high score
        
        # Test non-article page
        score = classifier.is_article_content(test_urls["about_page"])
        assert score < 0.3  # Should be a low score

    @responses.activate
    def test_is_likely_article(self, classifier, test_html_article, test_html_non_article, test_urls):
        """Test combined article classification."""
        # Mock article page
        responses.add(
            responses.GET,
            test_urls["article"],
            body=test_html_article,
            status=200,
            content_type="text/html"
        )
        
        # Mock non-article page
        responses.add(
            responses.GET,
            test_urls["about_page"],
            body=test_html_non_article,
            status=200,
            content_type="text/html"
        )
        
        # Test article page
        is_article, score = classifier.is_likely_article(test_urls["article"], threshold=0.5)
        assert is_article
        assert score > 0.5
        
        # Test non-article page
        is_article, score = classifier.is_likely_article(test_urls["about_page"], threshold=0.5)
        assert not is_article
        assert score < 0.5

    @responses.activate
    def test_error_handling(self, classifier):
        """Test error handling in article classification."""
        # Mock a request that fails
        bad_url = "https://nonexistent.example.com"
        responses.add(
            responses.GET,
            bad_url,
            status=404
        )
        
        # Should return a low score on error
        score = classifier.is_article_content(bad_url)
        assert score == 0.0
        
        # Should classify as not article
        is_article, score = classifier.is_likely_article(bad_url)
        assert not is_article
        assert score < 0.5