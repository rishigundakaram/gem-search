"""
Content scraper module for Gem Search.
Handles fetching and parsing web content using newspaper3k with automated link discovery.
"""
import json
import sqlite3
import requests
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def fetch_and_parse(url):
    """
    Fetch and parse content from a URL.
    
    Args:
        url: The URL to fetch and parse
        
    Returns:
        tuple: (title, content) or (None, None) if failed
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        title = article.title
        content = article.text
        
        return title, content
    except Exception as e:
        print(f"Failed to process {url}. Error: {e}")
        return None, None


def discover_links(url, same_domain_only=True):
    """
    Discover links from a given URL using BeautifulSoup.
    
    Args:
        url: The URL to discover links from
        same_domain_only: If True, only return links from the same domain
        
    Returns:
        set: Set of discovered URLs
    """
    discovered_urls = set()
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        base_domain = urlparse(url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Parse the URL
            parsed = urlparse(absolute_url)
            
            # Skip invalid URLs
            if not parsed.scheme or not parsed.netloc:
                continue
                
            # Skip non-HTTP(S) URLs
            if parsed.scheme not in ['http', 'https']:
                continue
                
            # Check domain restriction
            if same_domain_only and parsed.netloc != base_domain:
                continue
                
            # Skip common non-content URLs
            if any(ext in absolute_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']):
                continue
                
            discovered_urls.add(absolute_url)
            
    except Exception as e:
        print(f"Failed to discover links from {url}. Error: {e}")
        
    return discovered_urls


def get_existing_urls(db_path):
    """
    Get all existing URLs from the database.
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        set: Set of existing URLs
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM documents")
    existing_urls = {row[0] for row in cursor.fetchall()}
    conn.close()
    return existing_urls


def insert_document_if_new(url, title, content, db_path, existing_urls):
    """
    Insert a document into the database if it's new.
    
    Args:
        url: Document URL
        title: Document title
        content: Document content
        db_path: Path to SQLite database
        existing_urls: Set of existing URLs
        
    Returns:
        bool: True if document was inserted, False if it already existed
    """
    if url in existing_urls:
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert into documents table
        cursor.execute(
            "INSERT INTO documents (url, title, content) VALUES (?, ?, ?)",
            (url, title, content)
        )
        
        # Insert into FTS5 table
        document_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO document_content (document_id, content) VALUES (?, ?)",
            (document_id, content)
        )
        
        conn.commit()
        conn.close()
        
        # Add to existing URLs set to prevent duplicates in this session
        existing_urls.add(url)
        return True
        
    except Exception as e:
        print(f"Failed to insert document {url}. Error: {e}")
        return False


def scrape_with_discovery(links_file, db_path, discover_depth=1, allow_cross_domain=False):
    """
    Scrape links with automated link discovery.
    
    Args:
        links_file: Path to JSON file containing starter URLs
        db_path: Path to SQLite database
        discover_depth: How many levels deep to discover links (default: 1)
        allow_cross_domain: Allow discovering links from different domains
        
    Returns:
        tuple: (new_documents_count, total_discovered_urls)
    """
    # Read starter links from JSON file
    with open(links_file, 'r') as file:
        starter_links = json.load(file)
    
    # Get existing URLs from database
    existing_urls = get_existing_urls(db_path)
    
    # Track discovered URLs and process queue
    all_discovered_urls = set(starter_links)
    urls_to_process = list(starter_links)
    processed_urls = set()
    new_documents_count = 0
    
    current_depth = 0
    
    while current_depth < discover_depth and urls_to_process:
        print(f"Processing depth {current_depth + 1}/{discover_depth} ({len(urls_to_process)} URLs)")
        
        next_level_urls = []
        
        for url in urls_to_process:
            if url in processed_urls:
                continue
                
            processed_urls.add(url)
            
            # Try to scrape content from this URL
            title, content = fetch_and_parse(url)
            if title and content:
                if insert_document_if_new(url, title, content, db_path, existing_urls):
                    new_documents_count += 1
                    print(f"Added: {title[:60]}...")
            
            # Discover links from this URL for next depth level
            if current_depth + 1 < discover_depth:
                discovered = discover_links(url, same_domain_only=not allow_cross_domain)
                for discovered_url in discovered:
                    if discovered_url not in all_discovered_urls:
                        all_discovered_urls.add(discovered_url)
                        next_level_urls.append(discovered_url)
        
        urls_to_process = next_level_urls
        current_depth += 1
    
    print(f"\nScraping complete!")
    print(f"Discovered {len(all_discovered_urls)} total URLs")
    print(f"Added {new_documents_count} new documents to database")
    
    return new_documents_count, len(all_discovered_urls)


def scrape_links_to_database(links_file, db_path):
    """
    Scrape links from JSON file and store in database.
    
    Args:
        links_file: Path to JSON file containing URLs
        db_path: Path to SQLite database
        
    Returns:
        int: Number of new documents added
    """
    # Read links from JSON file
    with open(links_file, 'r') as file:
        links = json.load(file)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get existing URLs from the database
    cursor.execute("SELECT url FROM documents")
    existing_urls = {row[0] for row in cursor.fetchall()}
    
    # Process new links
    new_count = 0
    for url in links:
        if url not in existing_urls:
            title, content = fetch_and_parse(url)
            if title and content:
                # Insert into documents table
                cursor.execute(
                    "INSERT INTO documents (url, title, content) VALUES (?, ?, ?)",
                    (url, title, content)
                )
                
                # Insert into FTS5 table
                document_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO document_content (document_id, content) VALUES (?, ?)",
                    (document_id, content)
                )
                
                new_count += 1
    
    conn.commit()
    conn.close()
    
    if new_count > 0:
        print(f"Added {new_count} new documents to {db_path}")
    else:
        print("No new documents to add.")
    
    return new_count


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Scrape links and store in database with optional link discovery.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the starter links.')
    parser.add_argument('db_path', type=str, help='The SQLite database file path.')
    parser.add_argument('--discover-depth', type=int, default=1, 
                        help='Depth of link discovery (default: 1, max recommended: 3)')
    parser.add_argument('--allow-cross-domain', action='store_true',
                        help='Allow crawling links from different domains')
    args = parser.parse_args()
    
    if args.discover_depth > 1 or args.allow_cross_domain:
        print(f"Using link discovery with depth {args.discover_depth}")
        if args.allow_cross_domain:
            print("Cross-domain crawling enabled")
        scrape_with_discovery(args.links_file, args.db_path, args.discover_depth, args.allow_cross_domain)
    else:
        print("Using basic scraping (no link discovery)")
        scrape_links_to_database(args.links_file, args.db_path)