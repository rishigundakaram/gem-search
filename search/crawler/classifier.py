"""
Article classifier module for the crawler.
Determines whether a URL is likely to be a blog post or article.
"""

import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler.classifier')

class ArticleClassifier:
    def __init__(self, headers=None, timeout=10):
        """Initialize the article classifier.
        
        Args:
            headers: Request headers to use
            timeout: Request timeout in seconds
        """
        self.headers = headers or {
            'User-Agent': 'GemSearch/1.0 Blog Indexer'
        }
        self.timeout = timeout
    
    def is_article_url(self, url):
        """Check if a URL is likely to be an article based on its pattern.
        
        Args:
            url: The URL to check
            
        Returns:
            float: Score between 0 and 1 indicating likelihood of being an article
        """
        score = 0.0
        path = urlparse(url).path
        
        # URL pattern checks (up to 0.5 points)
        
        # Check for date patterns in URL
        if re.search(r'/\d{4}/\d{1,2}/\d{1,2}/', path):  # /2023/05/25/
            score += 0.3
        elif re.search(r'/\d{4}/\d{1,2}/', path):  # /2023/05/
            score += 0.2
        elif re.search(r'/\d{4}-\d{1,2}-\d{1,2}/', path):  # /2023-05-25/
            score += 0.3
        
        # Check for slug patterns
        if re.search(r'/[a-zA-Z0-9-]{10,}/?$', path):  # long-kebab-case-slug
            score += 0.2
        
        # Check for blog/article indicators
        blog_indicators = ['/blog/', '/article/', '/post/', '/news/']
        if any(indicator in path.lower() for indicator in blog_indicators):
            score += 0.2
        
        return min(score, 0.5)  # Cap URL-based score at 0.5
    
    def is_article_content(self, url):
        """Check if a URL's content is likely to be an article.
        
        Args:
            url: The URL to check
            
        Returns:
            float: Score between 0 and 1 indicating likelihood of being an article
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            score = 0.0
            
            # Look for article tags (up to 0.3 points)
            if soup.find('article'):
                score += 0.3
            elif soup.find(attrs={"class": re.compile(r'article|post|blog', re.I)}):
                score += 0.25
            elif soup.find(attrs={"id": re.compile(r'article|post|blog', re.I)}):
                score += 0.25
            
            # Check content length (up to 0.2 points)
            content_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content_length = sum(len(tag.get_text(strip=True)) for tag in content_tags)
            
            if content_length > 2000:  # Longer articles
                score += 0.2
            elif content_length > 1000:
                score += 0.15
            elif content_length > 500:
                score += 0.1
            
            # Look for publication date (up to 0.2 points)
            date_patterns = [
                'published', 'published at', 'posted on', 'date', 'datetime',
                'pubdate', 'pub_date', 'post-date'
            ]
            
            for pattern in date_patterns:
                if soup.find(attrs={"class": re.compile(pattern, re.I)}) or \
                   soup.find(attrs={"id": re.compile(pattern, re.I)}):
                    score += 0.2
                    break
            
            # Look for author information (up to 0.1 points)
            author_patterns = ['author', 'byline', 'writer']
            for pattern in author_patterns:
                if soup.find(attrs={"class": re.compile(pattern, re.I)}) or \
                   soup.find(attrs={"id": re.compile(pattern, re.I)}):
                    score += 0.1
                    break
            
            # Check content-to-HTML ratio (up to 0.2 points)
            html_length = len(response.text)
            if html_length > 0:
                content_ratio = content_length / html_length
                if content_ratio > 0.2:
                    score += 0.2
                elif content_ratio > 0.1:
                    score += 0.1
            
            return min(score, 0.5)  # Cap content-based score at 0.5
            
        except requests.RequestException as e:
            logger.error(f"Error analyzing {url}: {e}")
            return 0.0
    
    def is_likely_article(self, url, threshold=0.6):
        """Determine if a URL is likely to be an article.
        
        Args:
            url: The URL to check
            threshold: Minimum score to be considered an article
            
        Returns:
            tuple: (is_article, score)
        """
        # First check URL pattern
        url_score = self.is_article_url(url)
        
        # If URL score is very low, skip content check
        if url_score < 0.1:
            return False, url_score
        
        # Check content
        content_score = self.is_article_content(url)
        
        # Combine scores
        total_score = url_score + content_score
        
        logger.info(f"Classified {url} with score {total_score:.2f} (URL: {url_score:.2f}, Content: {content_score:.2f})")
        
        return total_score >= threshold, total_score


# Simple usage example
if __name__ == "__main__":
    classifier = ArticleClassifier()
    test_url = "https://engineering.fb.com/2023/01/17/data-infrastructure/how-meta-moved-masses-of-data/"
    is_article, score = classifier.is_likely_article(test_url)
    print(f"URL: {test_url}")
    print(f"Is article: {is_article} (Score: {score:.2f})")