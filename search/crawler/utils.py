"""
Utility functions for the crawler.
"""

import json
import logging
import time
import random
from urllib.parse import urlparse, urljoin
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler.utils')

def load_urls_from_json(json_path):
    """Load URLs from a JSON file.
    
    Args:
        json_path: Path to the JSON file
        
    Returns:
        list: List of URLs
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Handle different formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'urls' in data:
            return data['urls']
        else:
            logger.warning(f"Unknown JSON format in {json_path}")
            return []
            
    except Exception as e:
        logger.error(f"Error loading URLs from {json_path}: {e}")
        return []

def save_urls_to_json(urls, json_path):
    """Save URLs to a JSON file.
    
    Args:
        urls: List of URLs
        json_path: Path to the JSON file
    """
    try:
        with open(json_path, 'w') as f:
            json.dump(urls, f, indent=2)
        
        logger.info(f"Saved {len(urls)} URLs to {json_path}")
            
    except Exception as e:
        logger.error(f"Error saving URLs to {json_path}: {e}")

def add_scheme_if_missing(url):
    """Add https:// scheme if missing.
    
    Args:
        url: URL to check
        
    Returns:
        str: URL with scheme
    """
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def clean_url(url):
    """Clean a URL by removing fragments and some query parameters.
    
    Args:
        url: URL to clean
        
    Returns:
        str: Cleaned URL
    """
    # Parse the URL
    parsed = urlparse(url)
    
    # Remove fragment
    cleaned = parsed._replace(fragment='')
    
    # TODO: Optionally remove certain query parameters
    
    # Return the cleaned URL
    return cleaned.geturl()

def should_throttle(last_request_times, domain, min_delay=2.0):
    """Check if requests to a domain should be throttled.
    
    Args:
        last_request_times: Dict of domain -> last request time
        domain: The domain to check
        min_delay: Minimum delay between requests in seconds
        
    Returns:
        float: Time to wait in seconds (0 if no need to wait)
    """
    now = time.time()
    last_time = last_request_times.get(domain, 0)
    
    elapsed = now - last_time
    if elapsed < min_delay:
        return min_delay - elapsed
    
    return 0

def is_same_domain(url1, url2):
    """Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        bool: True if same domain
    """
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    
    # Remove 'www.' prefix for comparison
    domain1 = domain1.replace('www.', '')
    domain2 = domain2.replace('www.', '')
    
    return domain1 == domain2

def get_domain(url):
    """Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        str: Domain name
    """
    return urlparse(url).netloc.replace('www.', '')

def get_random_delay(min_delay=1.0, max_delay=5.0):
    """Get a random delay between requests.
    
    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        float: Random delay in seconds
    """
    return random.uniform(min_delay, max_delay)


# Simple usage example
if __name__ == "__main__":
    # Test URL cleaning
    test_url = "https://www.example.com/blog/post?utm_source=test#section1"
    clean = clean_url(test_url)
    print(f"Original: {test_url}")
    print(f"Cleaned: {clean}")
    
    # Test domain extraction
    print(f"Domain: {get_domain(test_url)}")
    
    # Test URL comparison
    url1 = "https://www.example.com/page1"
    url2 = "https://example.com/page2"
    print(f"Same domain: {is_same_domain(url1, url2)}")