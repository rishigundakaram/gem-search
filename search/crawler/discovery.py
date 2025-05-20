"""
Link discovery module for the crawler.
Finds potential article links from source URLs.
"""

import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler.discovery')

class LinkDiscoverer:
    def __init__(self, headers=None, timeout=10):
        """Initialize the link discoverer.
        
        Args:
            headers: Request headers to use
            timeout: Request timeout in seconds
        """
        self.headers = headers or {
            'User-Agent': 'GemSearch/1.0 Blog Indexer'
        }
        self.timeout = timeout
    
    def get_links_from_url(self, url):
        """Fetch all links from a given URL.
        
        Args:
            url: The URL to fetch links from
            
        Returns:
            List of discovered URLs
        """
        logger.info(f"Discovering links from: {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get base domain for filtering
            base_domain = urlparse(url).netloc
            
            # Extract all links
            all_links = []
            for a_tag in soup.find_all('a', href=True):
                link = a_tag['href']
                
                # Handle relative URLs
                absolute_link = urljoin(url, link)
                
                # Filter only links from the same domain
                if urlparse(absolute_link).netloc == base_domain:
                    all_links.append(absolute_link)
            
            logger.info(f"Discovered {len(all_links)} links from {url}")
            return list(set(all_links))  # Remove duplicates
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return []

    def discover_blog_links(self, url):
        """Discover potential blog/article links from a source URL.
        
        This is a higher-level function that gets all links and filters
        to find the most likely blog/article candidates.
        
        Args:
            url: The source URL to crawl
            
        Returns:
            List of potential blog/article URLs
        """
        # First get all links
        all_links = self.get_links_from_url(url)
        
        # Quick filter by URL pattern - looking for common blog URL patterns
        blog_indicators = [
            '/blog/', 
            '/article', 
            '/post',
            '/news/',
            '/research/',
            '/engineering/'
        ]
        
        filtered_links = []
        for link in all_links:
            # Skip URLs with query parameters or fragments - often not blog posts
            if '?' in link or '#' in link:
                continue
                
            # Skip obvious non-content pages
            skip_patterns = ['/tag/', '/category/', '/author/', '/about/', '/contact/']
            if any(pattern in link.lower() for pattern in skip_patterns):
                continue
                
            # Include URLs with blog indicators
            if any(indicator in link.lower() for indicator in blog_indicators):
                filtered_links.append(link)
                continue
                
            # Include URLs with date patterns
            # /2023/05/..., /2023-05-...
            path = urlparse(link).path
            if any(str(year) in path for year in range(2010, 2026)):
                filtered_links.append(link)
                continue
        
        logger.info(f"Filtered to {len(filtered_links)} potential blog links")
        return filtered_links


# Simple usage example
if __name__ == "__main__":
    discoverer = LinkDiscoverer()
    links = discoverer.discover_blog_links("https://engineering.fb.com")
    print(f"Discovered {len(links)} potential blog links:")
    for link in links[:10]:  # Print first 10
        print(f"  - {link}")