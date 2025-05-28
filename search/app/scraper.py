"""
Content scraper module for Gem Search.
Handles fetching and parsing web content using Trafilatura with automated link discovery.
"""
import json
import sqlite3
import requests
import trafilatura
import urllib3
import time
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Suppress SSL warnings to reduce noise
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_and_parse(url):
    """
    Fetch and parse content from a URL using Trafilatura for superior text extraction.
    
    Args:
        url: The URL to fetch and parse
        
    Returns:
        tuple: (title, content) or (None, None) if failed
    """
    try:
        # First, download the content with custom headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        downloaded = trafilatura.fetch_url(url, headers=headers, timeout=15)
        if not downloaded:
            return None, None
        
        # Extract main text content with metadata
        content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        if not content or len(content.strip()) < 50:
            return None, None
        
        # Extract title metadata
        metadata = trafilatura.extract_metadata(downloaded)
        title = None
        if metadata:
            title = metadata.title or metadata.sitename
        
        # Fallback title extraction if metadata doesn't provide one
        if not title:
            # Try to extract title from HTML using BeautifulSoup
            try:
                soup = BeautifulSoup(downloaded, 'html.parser')
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text().strip()
            except:
                pass
        
        # Final fallback for title
        if not title:
            title = f"Content from {urlparse(url).netloc}"
        
        return title, content.strip()
        
    except Exception as e:
        # Fallback to newspaper3k for structured articles
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if article.title and article.text and len(article.text.strip()) > 50:
                return article.title, article.text
        except Exception:
            pass
        
        # Final fallback: handle plain text files
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/plain' in content_type:
                content = response.text.strip()
                if len(content) > 50:
                    filename = url.split('/')[-1]
                    title = filename if filename else f"Text from {urlparse(url).netloc}"
                    return title, content
                    
        except Exception:
            # Silently handle errors to reduce noise
            pass
    
    return None, None


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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, verify=False)
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
        # Silently handle common errors to reduce noise
        pass
        
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
        
    # Retry logic for database operations
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=30)
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
            
        except sqlite3.IntegrityError:
            # URL already exists - this is expected
            if conn:
                conn.close()
            existing_urls.add(url)
            return False
        except sqlite3.OperationalError as e:
            if conn:
                conn.close()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue
            else:
                break
        except Exception as e:
            if conn:
                conn.close()
            break
    
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
        processed_in_batch = 0
        
        for url in urls_to_process:
            if url in processed_urls:
                continue
                
            processed_urls.add(url)
            processed_in_batch += 1
            
            # Show progress every 20 URLs
            if processed_in_batch % 20 == 0:
                print(f"  Processed {processed_in_batch}/{len(urls_to_process)} URLs in this batch...")
            
            # Try to scrape content from this URL
            title, content = fetch_and_parse(url)
            if title and content:
                if insert_document_if_new(url, title, content, db_path, existing_urls):
                    new_documents_count += 1
                    print(f"✓ Added: {title[:60]}...")
            
            # Discover links from this URL for next depth level
            if current_depth + 1 < discover_depth:
                discovered = discover_links(url, same_domain_only=not allow_cross_domain)
                for discovered_url in discovered:
                    if discovered_url not in all_discovered_urls:
                        all_discovered_urls.add(discovered_url)
                        next_level_urls.append(discovered_url)
            
            # Small delay to be respectful
            time.sleep(0.1)
        
        urls_to_process = next_level_urls
        current_depth += 1
    
    print(f"\nScraping complete!")
    print(f"Discovered {len(all_discovered_urls)} total URLs")
    print(f"Added {new_documents_count} new documents to database")
    
    return new_documents_count, len(all_discovered_urls)


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