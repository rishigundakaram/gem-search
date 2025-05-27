"""
Content scraper module for Gem Search.
Handles fetching, link discovery, and parsing web content.
"""
import json
import os
import sqlite3
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from newspaper import Article


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
    Discover all links from a given URL.
    
    Args:
        url: The URL to discover links from
        same_domain_only: Whether to only return links from the same domain
        
    Returns:
        set: Set of discovered URLs
    """
    discovered_urls = set()
    
    try:
        print(f"Discovering links from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        base_domain = urlparse(url).netloc
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Basic URL validation
            parsed = urlparse(absolute_url)
            if not parsed.scheme or parsed.scheme not in ['http', 'https']:
                continue
                
            # Domain filtering
            if same_domain_only and parsed.netloc != base_domain:
                continue
                
            # Skip common non-content URLs
            if any(skip in absolute_url.lower() for skip in ['#', 'javascript:', 'mailto:', '.pdf', '.jpg', '.png', '.gif']):
                continue
                
            discovered_urls.add(absolute_url)
            
        print(f"Discovered {len(discovered_urls)} links from {url}")
        return discovered_urls
        
    except Exception as e:
        print(f"Failed to discover links from {url}. Error: {e}")
        return set()


def get_existing_urls(db_path):
    """
    Get all existing URLs from the database to avoid duplicates.
    
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
    Insert document into database if URL doesn't already exist.
    
    Args:
        url: Document URL
        title: Document title
        content: Document content
        db_path: Path to SQLite database
        existing_urls: Set of existing URLs to check against
        
    Returns:
        bool: True if document was inserted, False if duplicate
    """
    if url in existing_urls:
        return False
        
    if not title or not content:
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert into documents table
        cursor.execute(
            "INSERT OR IGNORE INTO documents (url, title, content) VALUES (?, ?, ?)",
            (url, title, content)
        )
        
        # Check if the insert was successful (not a duplicate)
        if cursor.rowcount == 0:
            conn.close()
            return False
            
        # Insert into FTS5 table
        document_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO document_content (document_id, content) VALUES (?, ?)",
            (document_id, content)
        )
        
        conn.commit()
        conn.close()
        
        # Add to our existing_urls set to prevent duplicates in this session
        existing_urls.add(url)
        return True
        
    except sqlite3.IntegrityError:
        # URL already exists (shouldn't happen with our checks, but safety net)
        return False
    except Exception as e:
        print(f"Database error for {url}: {e}")
        return False


def scrape_with_discovery(links_file, db_path, discover_depth=1, same_domain_only=True):
    """
    Scrape starter links and discovered links, storing all in database.
    
    Args:
        links_file: Path to JSON file containing starter URLs
        db_path: Path to SQLite database
        discover_depth: How many levels deep to discover links (1 = starter + linked pages)
        same_domain_only: Whether to only discover links from the same domain
        
    Returns:
        dict: Statistics about the scraping process
    """
    from app.database import init_database
    
    # Read starter links from JSON file
    with open(links_file, 'r') as file:
        starter_links = json.load(file)
    
    print(f"Starting with {len(starter_links)} starter URLs")
    
    # Initialize database if it doesn't exist or doesn't have tables
    try:
        existing_urls = get_existing_urls(db_path)
        print(f"Found {len(existing_urls)} existing URLs in database")
    except (sqlite3.OperationalError, FileNotFoundError):
        print("Initializing database...")
        conn = init_database(db_path)
        conn.close()
        existing_urls = set()
        print("Database initialized with 0 existing URLs")
    
    # Track all URLs to process
    all_urls_to_process = set(starter_links)
    processed_urls = set()
    stats = {
        'starter_urls': len(starter_links),
        'discovered_urls': 0,
        'processed_successfully': 0,
        'failed_processing': 0,
        'skipped_duplicates': 0
    }
    
    # Discover links from starter URLs
    if discover_depth > 0:
        print(f"Discovering links from starter URLs (depth: {discover_depth})...")
        
        for starter_url in starter_links:
            if starter_url not in processed_urls:
                discovered = discover_links(starter_url, same_domain_only)
                all_urls_to_process.update(discovered)
                processed_urls.add(starter_url)
                stats['discovered_urls'] += len(discovered)
    
    print(f"Total URLs to process: {len(all_urls_to_process)}")
    print(f"Discovered {stats['discovered_urls']} new URLs")
    
    # Process all URLs (starter + discovered)
    for url in all_urls_to_process:
        if url in existing_urls:
            stats['skipped_duplicates'] += 1
            continue
            
        print(f"Processing: {url}")
        title, content = fetch_and_parse(url)
        
        if insert_document_if_new(url, title, content, db_path, existing_urls):
            stats['processed_successfully'] += 1
            print(f"✓ Added: {title[:50]}...")
        else:
            stats['failed_processing'] += 1
            print(f"✗ Failed or duplicate: {url}")
    
    # Print summary
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Starter URLs: {stats['starter_urls']}")
    print(f"Discovered URLs: {stats['discovered_urls']}")
    print(f"Successfully processed: {stats['processed_successfully']}")
    print(f"Failed processing: {stats['failed_processing']}")
    print(f"Skipped duplicates: {stats['skipped_duplicates']}")
    print(f"Total new documents: {stats['processed_successfully']}")
    
    return stats


def scrape_links_to_database(links_file, db_path):
    """
    Legacy function - calls new scrape_with_discovery function.
    Kept for backward compatibility.
    """
    result = scrape_with_discovery(links_file, db_path, discover_depth=0)
    return result['processed_successfully']


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Scrape links with discovery and store in database.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the starter links.')
    parser.add_argument('db_path', type=str, help='The SQLite database file path.')
    parser.add_argument('--discover-depth', type=int, default=1, help='How many levels deep to discover links (default: 1)')
    parser.add_argument('--allow-cross-domain', action='store_true', help='Allow discovering links from different domains')
    args = parser.parse_args()
    
    same_domain_only = not args.allow_cross_domain
    scrape_with_discovery(args.links_file, args.db_path, args.discover_depth, same_domain_only)