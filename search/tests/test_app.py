#!/usr/bin/env python3
"""
Simple test app for manual verification that the crawler components work.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_app')

# Ensure the parent directory is in the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def test_discovery():
    """Test the discovery module."""
    from crawler.discovery import LinkDiscoverer
    
    logger.info("Testing LinkDiscoverer...")
    discoverer = LinkDiscoverer()
    
    # Test URL
    test_url = "https://engineering.fb.com"  # Use a real URL for testing
    
    try:
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
    from crawler.classifier import ArticleClassifier
    
    logger.info("Testing ArticleClassifier...")
    classifier = ArticleClassifier()
    
    # Test URLs
    test_urls = [
        "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/",
        "https://engineering.fb.com/about/",
    ]
    
    try:
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
    from crawler.extractor import ContentExtractor
    
    logger.info("Testing ContentExtractor...")
    extractor = ContentExtractor()
    
    # Test URL (a known article)
    test_url = "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/"
    
    try:
        # Test extraction
        logger.info(f"Extracting content from {test_url}")
        title, content, metadata = extractor.extract(test_url)
        
        logger.info(f"Title: {title}")
        logger.info(f"Content length: {len(content) if content else 0} chars")
        logger.info(f"Content preview: {content[:100]}..." if content else "No content")
        logger.info(f"Metadata: {metadata}")
        
        return bool(title and content)
    except Exception as e:
        logger.error(f"Error in extractor test: {e}")
        return False

def main():
    """Run the test app."""
    logger.info("Starting crawler component tests...")
    
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