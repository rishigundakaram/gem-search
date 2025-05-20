"""
Main crawler module for gem-search.
Discovers, classifies, and extracts content from blog sites.
"""

import os
import json
import logging
import time
from datetime import datetime
import argparse
import concurrent.futures
from urllib.parse import urlparse

from discovery import LinkDiscoverer
from classifier import ArticleClassifier
from extractor import ContentExtractor
from db import DatabaseHandler
import utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('crawler')

class GemCrawler:
    def __init__(self, config=None):
        """Initialize the crawler.
        
        Args:
            config: Optional configuration dict
        """
        self.config = config or {}
        
        # Initialize components
        self.discoverer = LinkDiscoverer()
        self.classifier = ArticleClassifier()
        self.extractor = ContentExtractor()
        self.db = DatabaseHandler()
        
        # Set default configuration values
        self.max_links_per_source = self.config.get('max_links_per_source', 100)
        self.article_threshold = self.config.get('article_threshold', 0.6)
        self.max_workers = self.config.get('max_workers', 5)
        self.request_delay = self.config.get('request_delay', 2.0)
        
        # Track request times for throttling
        self.last_request_times = {}
    
    def process_source(self, source_url, source_name=None):
        """Process a source URL to discover and extract articles.
        
        Args:
            source_url: The source URL to crawl
            source_name: Optional name for the source
            
        Returns:
            dict: Stats about the crawl
        """
        logger.info(f"Processing source: {source_url}")
        
        stats = {
            'source_url': source_url,
            'start_time': datetime.now().isoformat(),
            'links_discovered': 0,
            'links_processed': 0,
            'articles_found': 0,
            'errors': 0
        }
        
        try:
            # Ensure URL has a scheme
            source_url = utils.add_scheme_if_missing(source_url)
            
            # Register source in database
            source_id = self.db.get_or_create_source(source_url, source_name)
            
            # Discover links
            links = self.discoverer.discover_blog_links(source_url)
            stats['links_discovered'] = len(links)
            
            # Limit the number of links to process
            links = links[:self.max_links_per_source]
            
            # Process each link
            for link in links:
                try:
                    # Throttle requests to be polite
                    domain = utils.get_domain(link)
                    wait_time = utils.should_throttle(
                        self.last_request_times, domain, self.request_delay
                    )
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    # Update last request time
                    self.last_request_times[domain] = time.time()
                    
                    # Check if it's an article
                    is_article, score = self.classifier.is_likely_article(
                        link, threshold=self.article_threshold
                    )
                    
                    if is_article:
                        # Add to database
                        link_id, is_new = self.db.add_link(link, source_id)
                        
                        if is_new:
                            # Extract content
                            title, content, metadata = self.extractor.extract(link)
                            
                            if title and content and len(content) > 200:
                                # Add document
                                self.db.add_document(link_id, title, content, metadata)
                                stats['articles_found'] += 1
                            else:
                                # Mark as failed
                                self.db.mark_link_failed(link_id, "Insufficient content")
                    
                    stats['links_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing link {link}: {e}")
                    stats['errors'] += 1
            
            stats['end_time'] = datetime.now().isoformat()
            logger.info(f"Completed source {source_url}: found {stats['articles_found']} articles")
            return stats
            
        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}")
            stats['errors'] += 1
            stats['end_time'] = datetime.now().isoformat()
            return stats
    
    def process_sources_from_json(self, json_path):
        """Process all sources from a JSON file.
        
        Args:
            json_path: Path to JSON file with source URLs
            
        Returns:
            list: Stats for each source
        """
        # Load URLs from JSON
        urls = utils.load_urls_from_json(json_path)
        logger.info(f"Loaded {len(urls)} URLs from {json_path}")
        
        all_stats = []
        
        # Process each URL
        for url in urls:
            stats = self.process_source(url)
            all_stats.append(stats)
        
        # Save stats
        stats_path = os.path.join(
            os.path.dirname(json_path),
            f"crawl_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            with open(stats_path, 'w') as f:
                json.dump(all_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats to {stats_path}: {e}")
        
        return all_stats
    
    def process_sources_parallel(self, urls, max_workers=None):
        """Process multiple sources in parallel.
        
        Args:
            urls: List of URLs to process
            max_workers: Maximum number of worker threads
            
        Returns:
            list: Stats for each source
        """
        if max_workers is None:
            max_workers = self.max_workers
        
        all_stats = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.process_source, url): url for url in urls
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    stats = future.result()
                    all_stats.append(stats)
                except Exception as e:
                    logger.error(f"Error processing {url}: {e}")
                    all_stats.append({
                        'source_url': url,
                        'error': str(e),
                        'start_time': datetime.now().isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'links_discovered': 0,
                        'links_processed': 0,
                        'articles_found': 0,
                        'errors': 1
                    })
        
        return all_stats
    
    def process_pending_links(self, limit=100):
        """Process pending links from the database.
        
        Args:
            limit: Maximum number of links to process
            
        Returns:
            dict: Stats about the processing
        """
        logger.info(f"Processing up to {limit} pending links")
        
        stats = {
            'start_time': datetime.now().isoformat(),
            'links_processed': 0,
            'articles_found': 0,
            'errors': 0
        }
        
        # Get pending links
        pending_links = self.db.get_pending_links(limit)
        logger.info(f"Found {len(pending_links)} pending links")
        
        # Process each link
        for link_id, url in pending_links:
            try:
                # Throttle requests to be polite
                domain = utils.get_domain(url)
                wait_time = utils.should_throttle(
                    self.last_request_times, domain, self.request_delay
                )
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Update last request time
                self.last_request_times[domain] = time.time()
                
                # Extract content
                title, content, metadata = self.extractor.extract(url)
                
                if title and content and len(content) > 200:
                    # Add document
                    self.db.add_document(link_id, title, content, metadata)
                    stats['articles_found'] += 1
                else:
                    # Mark as failed
                    self.db.mark_link_failed(link_id, "Insufficient content")
                
                stats['links_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing link {url}: {e}")
                stats['errors'] += 1
                
                # Mark as failed
                try:
                    self.db.mark_link_failed(link_id, str(e))
                except:
                    pass
        
        stats['end_time'] = datetime.now().isoformat()
        logger.info(f"Completed processing {stats['links_processed']} links, found {stats['articles_found']} articles")
        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Gem Search Crawler")
    
    # Command group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--sources_file', type=str, help='JSON file with source URLs')
    group.add_argument('--source_url', type=str, help='Single source URL to crawl')
    group.add_argument('--process_pending', action='store_true', help='Process pending links')
    
    # Optional arguments
    parser.add_argument('--max_links', type=int, default=100, help='Maximum links per source')
    parser.add_argument('--max_workers', type=int, default=5, help='Maximum worker threads')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--threshold', type=float, default=0.6, help='Article classifier threshold')
    parser.add_argument('--limit', type=int, default=100, help='Limit for pending links')
    
    args = parser.parse_args()
    
    # Configure crawler
    config = {
        'max_links_per_source': args.max_links,
        'max_workers': args.max_workers,
        'request_delay': args.delay,
        'article_threshold': args.threshold
    }
    
    # Initialize crawler
    crawler = GemCrawler(config)
    
    # Process command
    if args.sources_file:
        crawler.process_sources_from_json(args.sources_file)
    elif args.source_url:
        crawler.process_source(args.source_url)
    elif args.process_pending:
        crawler.process_pending_links(args.limit)


if __name__ == "__main__":
    main()