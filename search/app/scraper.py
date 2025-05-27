"""
Content scraper module for Gem Search.
Handles fetching and parsing web content using newspaper3k.
"""
import json
import sqlite3
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
    parser = argparse.ArgumentParser(description='Scrape links and store in database.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the links.')
    parser.add_argument('db_path', type=str, help='The SQLite database file path.')
    args = parser.parse_args()
    
    scrape_links_to_database(args.links_file, args.db_path)