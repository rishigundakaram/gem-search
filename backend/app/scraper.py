"""
Content scraper module for Gem Search.
Handles fetching and parsing web content using Trafilatura with automated link discovery.
Supports both synchronous and asynchronous concurrent scraping.
"""
import json
import sqlite3
import requests
import trafilatura
import urllib3
import time
import asyncio
import aiohttp
import threading
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

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


async def fetch_and_parse_async(session, url, semaphore):
    """
    Async version of fetch_and_parse using aiohttp.
    
    Args:
        session: aiohttp.ClientSession
        url: URL to fetch
        semaphore: asyncio.Semaphore for rate limiting
        
    Returns:
        tuple: (url, title, content) or (url, None, None) if failed
    """
    async with semaphore:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status != 200:
                    return url, None, None
                
                html_content = await response.text()
                
                # Use trafilatura to extract content (CPU-bound, run in thread)
                loop = asyncio.get_event_loop()
                title, content = await loop.run_in_executor(
                    None, 
                    lambda: extract_content_with_trafilatura(html_content, url)
                )
                
                return url, title, content
                
        except Exception:
            return url, None, None


def extract_content_with_trafilatura(html_content, url):
    """
    Helper function to extract content using trafilatura (CPU-bound).
    
    Args:
        html_content: Raw HTML content
        url: URL for fallback title generation
        
    Returns:
        tuple: (title, content) or (None, None) if failed
    """
    try:
        # Extract main text content with metadata
        content = trafilatura.extract(html_content, include_comments=False, include_tables=True)
        if not content or len(content.strip()) < 50:
            return None, None
        
        # Extract title metadata
        metadata = trafilatura.extract_metadata(html_content)
        title = None
        if metadata:
            title = metadata.title or metadata.sitename
        
        # Fallback title extraction if metadata doesn't provide one
        if not title:
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text().strip()
            except:
                pass
        
        # Final fallback for title
        if not title:
            title = f"Content from {urlparse(url).netloc}"
        
        return title, content.strip()
        
    except Exception:
        return None, None


async def discover_links_async(session, url, semaphore, same_domain_only=True):
    """
    Async version of discover_links.
    
    Args:
        session: aiohttp.ClientSession
        url: URL to discover links from
        semaphore: asyncio.Semaphore for rate limiting
        same_domain_only: If True, only return links from same domain
        
    Returns:
        set: Set of discovered URLs
    """
    async with semaphore:
        discovered_urls = set()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status != 200:
                    return discovered_urls
                
                html_content = await response.text()
                
                # Parse links (CPU-bound, run in thread)
                loop = asyncio.get_event_loop()
                discovered_urls = await loop.run_in_executor(
                    None,
                    lambda: parse_links_from_html(html_content, url, same_domain_only)
                )
                
        except Exception:
            pass
            
        return discovered_urls


def parse_links_from_html(html_content, base_url, same_domain_only=True):
    """
    Helper function to parse links from HTML (CPU-bound).
    
    Args:
        html_content: Raw HTML content
        base_url: Base URL for resolving relative links
        same_domain_only: If True, only return links from same domain
        
    Returns:
        set: Set of discovered URLs
    """
    discovered_urls = set()
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Validate URL format
            parsed = urlparse(absolute_url)
            if not parsed.scheme or not parsed.netloc:
                continue
            
            # Filter by domain if required
            if same_domain_only and parsed.netloc != base_domain:
                continue
                
            # Skip common non-content URLs
            if any(ext in absolute_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']):
                continue
                
            discovered_urls.add(absolute_url)
            
    except Exception:
        pass
        
    return discovered_urls


def insert_document_batch(documents, db_path, existing_urls):
    """
    Insert multiple documents into database in a single transaction.
    
    Args:
        documents: List of (url, title, content) tuples
        db_path: Database path
        existing_urls: Set of existing URLs (will be updated)
        
    Returns:
        int: Number of documents inserted
    """
    if not documents:
        return 0
    
    # Filter out existing URLs
    new_documents = [(url, title, content) for url, title, content in documents 
                     if url not in existing_urls and title and content]
    
    if not new_documents:
        return 0
    
    inserted_count = 0
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            cursor = conn.cursor()
            
            # Insert all documents in a single transaction
            for url, title, content in new_documents:
                try:
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
                    
                    inserted_count += 1
                    existing_urls.add(url)
                    
                except sqlite3.IntegrityError:
                    # URL already exists
                    existing_urls.add(url)
                    continue
            
            conn.commit()
            conn.close()
            return inserted_count
            
        except sqlite3.OperationalError as e:
            if conn:
                conn.close()
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                break
        except Exception:
            if conn:
                conn.close()
            break
    
    return inserted_count


async def scrape_urls_concurrent(urls, db_path, max_concurrent=20, batch_size=50):
    """
    Scrape multiple URLs concurrently using asyncio.
    
    Args:
        urls: List of URLs to scrape
        db_path: Database path
        max_concurrent: Maximum concurrent requests
        batch_size: Batch size for database inserts
        
    Returns:
        tuple: (new_documents_count, total_processed)
    """
    if not urls:
        return 0, 0
    
    print(f"Starting concurrent scraping of {len(urls)} URLs...")
    print(f"Concurrency: {max_concurrent}, Batch size: {batch_size}")
    
    # Get existing URLs
    existing_urls = get_existing_urls(db_path)
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create aiohttp session with connection limits
    connector = aiohttp.TCPConnector(
        limit=max_concurrent * 2,
        limit_per_host=10,
        keepalive_timeout=30,
        enable_cleanup_closed=True
    )
    
    timeout = aiohttp.ClientTimeout(total=15)
    
    new_documents_count = 0
    processed_count = 0
    pending_documents = []
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Process URLs in chunks to avoid memory issues
        for i in range(0, len(urls), batch_size * 4):
            chunk = urls[i:i + batch_size * 4]
            
            # Create tasks for this chunk
            tasks = [fetch_and_parse_async(session, url, semaphore) for url in chunk]
            
            # Process tasks as they complete
            for coro in asyncio.as_completed(tasks):
                url, title, content = await coro
                processed_count += 1
                
                if title and content:
                    pending_documents.append((url, title, content))
                
                # Insert batch when we have enough documents
                if len(pending_documents) >= batch_size:
                    inserted = insert_document_batch(pending_documents, db_path, existing_urls)
                    new_documents_count += inserted
                    if inserted > 0:
                        print(f"✓ Batch inserted {inserted} documents (Total: {new_documents_count})")
                    pending_documents = []
                
                # Show progress
                if processed_count % 50 == 0:
                    print(f"  Processed {processed_count}/{len(urls)} URLs...")
    
    # Insert remaining documents
    if pending_documents:
        inserted = insert_document_batch(pending_documents, db_path, existing_urls)
        new_documents_count += inserted
        if inserted > 0:
            print(f"✓ Final batch inserted {inserted} documents")
    
    print(f"Concurrent scraping complete!")
    print(f"Processed: {processed_count}, Added: {new_documents_count}")
    
    return new_documents_count, processed_count


async def scrape_with_discovery_concurrent(links_file, db_path, discover_depth=1, allow_cross_domain=False, max_concurrent=20):
    """
    Async version of scrape_with_discovery with concurrent processing.
    
    Args:
        links_file: Path to JSON file containing starter URLs
        db_path: Database path
        discover_depth: Depth of link discovery
        allow_cross_domain: Allow cross-domain link discovery
        max_concurrent: Maximum concurrent requests
        
    Returns:
        tuple: (new_documents_count, total_discovered_urls)
    """
    # Read starter URLs
    with open(links_file, 'r') as file:
        starter_urls = json.load(file)
    
    print(f"Starting concurrent discovery scraping with depth {discover_depth}")
    print(f"Starter URLs: {len(starter_urls)}")
    print(f"Max concurrent requests: {max_concurrent}")
    
    all_discovered_urls = set(starter_urls)
    current_urls = starter_urls[:]
    new_documents_count = 0
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # Create aiohttp session
    connector = aiohttp.TCPConnector(
        limit=max_concurrent * 2,
        limit_per_host=10,
        keepalive_timeout=30
    )
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for depth in range(discover_depth):
            if not current_urls:
                break
                
            print(f"\n=== Depth {depth + 1}/{discover_depth} ({len(current_urls)} URLs) ===")
            
            # Scrape current URLs concurrently
            docs_added, processed = await scrape_urls_concurrent(
                current_urls, db_path, max_concurrent, batch_size=50
            )
            new_documents_count += docs_added
            
            # Discover links for next depth (if not at max depth)
            if depth + 1 < discover_depth:
                print(f"Discovering links from {len(current_urls)} URLs...")
                
                # Create discovery tasks
                discovery_tasks = [
                    discover_links_async(session, url, semaphore, same_domain_only=not allow_cross_domain)
                    for url in current_urls
                ]
                
                # Collect discovered URLs
                next_urls = []
                discovery_count = 0
                
                for coro in asyncio.as_completed(discovery_tasks):
                    discovered = await coro
                    discovery_count += 1
                    
                    for url in discovered:
                        if url not in all_discovered_urls:
                            all_discovered_urls.add(url)
                            next_urls.append(url)
                    
                    if discovery_count % 20 == 0:
                        print(f"  Discovery progress: {discovery_count}/{len(current_urls)}")
                
                current_urls = next_urls
                print(f"Discovered {len(next_urls)} new URLs for next depth")
            else:
                current_urls = []
    
    print(f"\nConcurrent discovery scraping complete!")
    print(f"Total URLs discovered: {len(all_discovered_urls)}")
    print(f"Total documents added: {new_documents_count}")
    
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
    parser.add_argument('--concurrent', action='store_true',
                        help='Use concurrent/async scraping for much faster processing')
    parser.add_argument('--max-concurrent', type=int, default=20,
                        help='Maximum concurrent requests when using --concurrent (default: 20)')
    args = parser.parse_args()
    
    if args.concurrent:
        print(f"Using CONCURRENT scraping with max {args.max_concurrent} requests")
        if args.discover_depth > 1 or args.allow_cross_domain:
            print(f"Link discovery enabled with depth {args.discover_depth}")
            if args.allow_cross_domain:
                print("Cross-domain crawling enabled")
            asyncio.run(scrape_with_discovery_concurrent(
                args.links_file, args.db_path, args.discover_depth, 
                args.allow_cross_domain, args.max_concurrent
            ))
        else:
            print("Basic concurrent scraping (no link discovery)")
            with open(args.links_file, 'r') as f:
                urls = json.load(f)
            asyncio.run(scrape_urls_concurrent(urls, args.db_path, args.max_concurrent))
    else:
        print("Using SEQUENTIAL scraping (use --concurrent for much faster processing)")
        if args.discover_depth > 1 or args.allow_cross_domain:
            print(f"Using link discovery with depth {args.discover_depth}")
            if args.allow_cross_domain:
                print("Cross-domain crawling enabled")
            scrape_with_discovery(args.links_file, args.db_path, args.discover_depth, args.allow_cross_domain)
        else:
            print("Using basic scraping (no link discovery)")
            scrape_links_to_database(args.links_file, args.db_path)