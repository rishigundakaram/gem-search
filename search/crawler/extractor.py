"""
Content extractor module for the crawler.
Extracts article content from URLs.
"""

import time
from newspaper import Article
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler.extractor')

class ContentExtractor:
    def __init__(self, headers=None, timeout=15):
        """Initialize the content extractor.
        
        Args:
            headers: Request headers to use
            timeout: Request timeout in seconds
        """
        self.headers = headers or {
            'User-Agent': 'GemSearch/1.0 Blog Indexer'
        }
        self.timeout = timeout
    
    def extract_with_newspaper(self, url):
        """Extract content using newspaper3k.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            tuple: (title, content, metadata)
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            # Extract metadata
            metadata = {
                'authors': article.authors,
                'publish_date': article.publish_date,
                'top_image': article.top_image,
                'language': article.meta_lang
            }
            
            return article.title, article.text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting with newspaper3k from {url}: {e}")
            return None, None, {}
    
    def extract_with_custom(self, url):
        """Extract content using custom BeautifulSoup extraction.
        This is a fallback method when newspaper3k fails.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            tuple: (title, content, metadata)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string
            
            # Try to find main content
            content = ""
            
            # First try to find article tag
            article_tag = soup.find('article')
            if article_tag:
                paragraphs = article_tag.find_all('p')
                content = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
            # If no article tag or content is very short, try main tag
            if not content or len(content) < 200:
                main_tag = soup.find('main')
                if main_tag:
                    paragraphs = main_tag.find_all('p')
                    content = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
            # Last resort: look for div with content-like class names
            if not content or len(content) < 200:
                content_divs = soup.find_all('div', class_=lambda c: c and any(
                    name in str(c).lower() for name in ['content', 'article', 'post', 'entry']
                ))
                if content_divs:
                    paragraphs = content_divs[0].find_all('p')
                    content = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
            # Extract basic metadata
            metadata = {
                'authors': [],
                'publish_date': None,
                'top_image': None
            }
            
            # Look for author
            author_tag = soup.find(['a', 'span', 'div'], class_=lambda c: c and 'author' in str(c).lower())
            if author_tag:
                metadata['authors'] = [author_tag.get_text().strip()]
            
            # Look for publish date
            date_tag = soup.find(['time', 'span', 'div'], class_=lambda c: c and any(
                name in str(c).lower() for name in ['date', 'time', 'published']
            ))
            if date_tag:
                date_text = date_tag.get_text().strip()
                if date_text:
                    metadata['publish_date'] = date_text
            
            # Look for top image
            top_img = soup.find('meta', property='og:image')
            if top_img and top_img.get('content'):
                metadata['top_image'] = top_img.get('content')
            
            return title, content, metadata
            
        except Exception as e:
            logger.error(f"Error extracting with custom method from {url}: {e}")
            return None, None, {}
    
    def extract(self, url):
        """Extract content from a URL using multiple methods.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            tuple: (title, content, metadata)
        """
        logger.info(f"Extracting content from: {url}")
        
        # First try newspaper3k
        title, content, metadata = self.extract_with_newspaper(url)
        
        # If newspaper extraction failed or returned minimal content, try custom extraction
        if not title or not content or len(content) < 200:
            logger.info(f"Newspaper extraction failed or insufficient for {url}, trying custom extraction")
            alt_title, alt_content, alt_metadata = self.extract_with_custom(url)
            
            # Use custom extraction results if they're better
            if alt_title and (not title or len(alt_title) > len(title)):
                title = alt_title
            
            if alt_content and (not content or len(alt_content) > len(content)):
                content = alt_content
            
            # Merge metadata
            for key, value in alt_metadata.items():
                if value and not metadata.get(key):
                    metadata[key] = value
        
        # Calculate some content statistics
        stats = {
            'content_length': len(content) if content else 0,
            'title_length': len(title) if title else 0,
            'has_author': bool(metadata.get('authors')),
            'has_date': bool(metadata.get('publish_date')),
            'has_image': bool(metadata.get('top_image'))
        }
        
        # Add stats to metadata
        metadata['stats'] = stats
        
        # Logging
        if title and content and len(content) > 200:
            logger.info(f"Successfully extracted {stats['content_length']} chars from {url}")
        else:
            logger.warning(f"Extraction may be incomplete for {url}: title={bool(title)}, content_length={stats['content_length']}")
        
        return title, content, metadata


# Simple usage example
if __name__ == "__main__":
    extractor = ContentExtractor()
    test_url = "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/"
    title, content, metadata = extractor.extract(test_url)
    
    print(f"URL: {test_url}")
    print(f"Title: {title}")
    print(f"Content length: {len(content) if content else 0} chars")
    print("Content preview:", content[:200], "..." if content else "")
    print(f"Metadata: {metadata}")