#!/usr/bin/env python3
"""
Crawler Test Script - Verifies the core functionality of the crawler

This script tests the most critical components of the crawler:
1. Link discovery
2. Article classification 
3. Content extraction

Usage:
    python test_crawler.py

Requirements:
    - newspaper3k
    - beautifulsoup4
    - requests
"""

import os
import sys
import logging
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_crawler')

# Define required packages
REQUIRED_PACKAGES = [
    'newspaper',
    'bs4',
    'requests',
]

def check_dependencies():
    """Check if all required packages are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        if importlib.util.find_spec(package) is None:
            missing.append(package)
    
    if missing:
        logger.error("Missing required packages: %s", ", ".join(missing))
        logger.error("Please install them with: pip install -r requirements.txt")
        return False
    return True

def test_discovery():
    """Test the discovery module."""
    try:
        # Add search directory to path
        search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
        if search_dir not in sys.path:
            sys.path.insert(0, search_dir)
        
        from crawler.discovery import LinkDiscoverer
        
        logger.info("Testing LinkDiscoverer...")
        discoverer = LinkDiscoverer()
        
        # Test URL
        test_url = "https://engineering.fb.com"  # Use a real URL for testing
        
        # Test get_links_from_url
        logger.info(f"Getting links from {test_url}")
        links = discoverer.get_links_from_url(test_url)
        logger.info(f"Found {len(links)} links")
        
        # Test discover_blog_links
        logger.info(f"Discovering blog links from {test_url}")
        blog_links = discoverer.discover_blog_links(test_url)
        logger.info(f"Found {len(blog_links)} potential blog links")
        
        # Print some example links
        if blog_links:
            logger.info("Example blog links:")
            for link in blog_links[:5]:
                logger.info(f"  - {link}")
        
        return True
    except Exception as e:
        logger.error(f"Error in discovery test: {e}")
        return False

def test_classifier():
    """Test the classifier module."""
    try:
        # Add search directory to path
        search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
        if search_dir not in sys.path:
            sys.path.insert(0, search_dir)
        
        from crawler.classifier import ArticleClassifier
        
        logger.info("Testing ArticleClassifier...")
        classifier = ArticleClassifier()
        
        # Test URLs
        test_urls = [
            "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/",
            "https://engineering.fb.com/about/",
        ]
        
        for url in test_urls:
            # Test URL-based classification
            url_score = classifier.is_article_url(url)
            logger.info(f"URL score for {url}: {url_score:.2f}")
            
            # Test content-based classification (if accessible)
            try:
                content_score = classifier.is_article_content(url)
                logger.info(f"Content score for {url}: {content_score:.2f}")
                
                # Test combined classification
                is_article, score = classifier.is_likely_article(url)
                logger.info(f"Is article: {is_article} (Score: {score:.2f})")
            except Exception as e:
                logger.warning(f"Could not test content classification for {url}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error in classifier test: {e}")
        return False

def test_extractor():
    """Test the extractor module."""
    try:
        # Add search directory to path
        search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
        if search_dir not in sys.path:
            sys.path.insert(0, search_dir)
        
        from crawler.extractor import ContentExtractor
        
        logger.info("Testing ContentExtractor...")
        extractor = ContentExtractor()
        
        # Test URL (a known article)
        test_url = "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/"
        
        # Test extraction
        logger.info(f"Extracting content from {test_url}")
        title, content, metadata = extractor.extract(test_url)
        
        logger.info(f"Title: {title}")
        logger.info(f"Content length: {len(content) if content else 0} chars")
        logger.info(f"Content preview: {content[:100]}..." if content else "No content")
        logger.info(f"Metadata stats: {metadata.get('stats', {})}")
        
        return bool(title and content)
    except Exception as e:
        logger.error(f"Error in extractor test: {e}")
        return False

def main():
    """Run the test script."""
    logger.info("Starting crawler component tests...")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Run tests
    discovery_ok = test_discovery()
    logger.info(f"Discovery test {'PASSED' if discovery_ok else 'FAILED'}")
    
    classifier_ok = test_classifier()
    logger.info(f"Classifier test {'PASSED' if classifier_ok else 'FAILED'}")
    
    extractor_ok = test_extractor()
    logger.info(f"Extractor test {'PASSED' if extractor_ok else 'FAILED'}")
    
    # Overall result
    if discovery_ok and classifier_ok and extractor_ok:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())