"""Tests for the crawler utility functions."""

import os
import json
import tempfile
import time
import pytest

from crawler import utils

class TestUtils:
    """Tests for the utils module."""

    def test_load_urls_from_json(self):
        """Test loading URLs from a JSON file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as f:
            test_urls = [
                "https://example.com/1",
                "https://example.com/2",
                "https://example.com/3"
            ]
            json.dump(test_urls, f)
            temp_path = f.name
        
        try:
            # Test loading URLs
            urls = utils.load_urls_from_json(temp_path)
            assert urls == test_urls
            
            # Test handling different format
            with open(temp_path, "w") as f:
                json.dump({"urls": test_urls}, f)
            
            urls = utils.load_urls_from_json(temp_path)
            assert urls == test_urls
            
            # Test error handling with invalid JSON
            with open(temp_path, "w") as f:
                f.write("Not valid JSON")
            
            urls = utils.load_urls_from_json(temp_path)
            assert isinstance(urls, list)
            assert len(urls) == 0
            
            # Test nonexistent file
            urls = utils.load_urls_from_json("/nonexistent/file.json")
            assert isinstance(urls, list)
            assert len(urls) == 0
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_urls_to_json(self):
        """Test saving URLs to a JSON file."""
        # Create a temporary path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name
        
        try:
            # Test saving URLs
            test_urls = [
                "https://example.com/1",
                "https://example.com/2",
                "https://example.com/3"
            ]
            utils.save_urls_to_json(test_urls, temp_path)
            
            # Verify saved correctly
            with open(temp_path, "r") as f:
                loaded_urls = json.load(f)
            
            assert loaded_urls == test_urls
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_add_scheme_if_missing(self):
        """Test adding scheme to URLs."""
        # URL with scheme
        url = "https://example.com"
        assert utils.add_scheme_if_missing(url) == url
        
        # URL with http scheme
        url = "http://example.com"
        assert utils.add_scheme_if_missing(url) == url
        
        # URL without scheme
        url = "example.com"
        assert utils.add_scheme_if_missing(url) == "https://" + url

    def test_clean_url(self):
        """Test cleaning URLs."""
        # URL with fragment
        url = "https://example.com/page#section"
        assert utils.clean_url(url) == "https://example.com/page"
        
        # URL with query and fragment
        url = "https://example.com/page?param=value#section"
        clean = utils.clean_url(url)
        assert "#section" not in clean
        assert "param=value" in clean

    def test_should_throttle(self):
        """Test request throttling."""
        # Empty history
        wait_time = utils.should_throttle({}, "example.com")
        assert wait_time == 0
        
        # Recent request
        last_times = {"example.com": time.time()}
        wait_time = utils.should_throttle(last_times, "example.com", 2.0)
        assert wait_time > 0
        assert wait_time <= 2.0
        
        # Old request
        last_times = {"example.com": time.time() - 5.0}
        wait_time = utils.should_throttle(last_times, "example.com", 2.0)
        assert wait_time == 0
        
        # Different domain
        last_times = {"example.com": time.time()}
        wait_time = utils.should_throttle(last_times, "different.com", 2.0)
        assert wait_time == 0

    def test_is_same_domain(self):
        """Test domain comparison."""
        # Same domain
        assert utils.is_same_domain("https://example.com/page1", "https://example.com/page2")
        
        # Same domain with www
        assert utils.is_same_domain("https://www.example.com", "https://example.com")
        
        # Different domains
        assert not utils.is_same_domain("https://example.com", "https://different.com")
        
        # Subdomains (considered different)
        assert not utils.is_same_domain("https://sub.example.com", "https://example.com")

    def test_get_domain(self):
        """Test domain extraction."""
        # Basic domain
        assert utils.get_domain("https://example.com/page") == "example.com"
        
        # Domain with www
        assert utils.get_domain("https://www.example.com") == "example.com"
        
        # Subdomain
        assert utils.get_domain("https://blog.example.com") == "blog.example.com"

    def test_get_random_delay(self):
        """Test random delay generation."""
        # Default range
        delay = utils.get_random_delay()
        assert delay >= 1.0
        assert delay <= 5.0
        
        # Custom range
        delay = utils.get_random_delay(2.0, 3.0)
        assert delay >= 2.0
        assert delay <= 3.0