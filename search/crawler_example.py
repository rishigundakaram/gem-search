#!/usr/bin/env python3
"""
Example script demonstrating how to use the crawler.
This script crawls a few blog sites and indexes their content.
"""

import os
import json
import logging
from datetime import datetime
from crawler.crawler import GemCrawler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crawler_example')

def main():
    """Main entry point for the example."""
    # Example source URLs
    example_sources = [
        "https://engineering.fb.com",
        "https://ai.googleblog.com",
        "https://netflixtechblog.com",
        "https://medium.com/airbnb-engineering"
    ]
    
    # Create a temporary JSON file if it doesn't exist
    json_file = os.path.join(os.path.dirname(__file__), 'scrapers/example_sources.json')
    try:
        with open(json_file, 'w') as f:
            json.dump(example_sources, f, indent=2)
        logger.info(f"Created example sources file at {json_file}")
    except Exception as e:
        logger.error(f"Error creating example sources file: {e}")
        return
    
    # Configuration for the crawler
    config = {
        'max_links_per_source': 5,  # Limit to 5 articles per source for this example
        'max_workers': 2,
        'request_delay': 3.0,  # Be extra polite in this example
        'article_threshold': 0.6
    }
    
    # Initialize crawler
    crawler = GemCrawler(config)
    
    # Process the sources
    logger.info("Starting crawler example...")
    start_time = datetime.now()
    
    # Option 1: Process all sources from JSON file
    logger.info(f"Processing sources from {json_file}")
    stats = crawler.process_sources_from_json(json_file)
    
    # Option 2: Process sources in parallel
    # logger.info("Processing sources in parallel")
    # stats = crawler.process_sources_parallel(example_sources)
    
    # Option 3: Process a single source
    # logger.info("Processing a single source")
    # stats = crawler.process_source(example_sources[0])
    
    # Print summary
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    articles_found = sum(s.get('articles_found', 0) for s in stats)
    links_processed = sum(s.get('links_processed', 0) for s in stats)
    
    logger.info(f"Crawler example completed in {total_time:.2f} seconds")
    logger.info(f"Processed {links_processed} links and found {articles_found} articles")
    logger.info("You can now run your search engine on the indexed content!")

if __name__ == "__main__":
    main()