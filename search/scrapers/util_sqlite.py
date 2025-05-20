import requests
import json
import os
import sqlite3
from newspaper import Article

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT
    )
    ''')
    
    conn.commit()
    return conn

def fetch_and_parse(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        title = article.title
        full_text = article.text
        
        return title, full_text
    except Exception as e:
        print(f"Failed to process {url}. Error: {e}")
        return None, None

def main(links_file, db_path):
    # Read links from links.json
    with open(links_file, 'r') as file:
        links = json.load(file)
    
    # Initialize database
    conn = init_db(db_path)
    cursor = conn.cursor()
    
    # Get existing URLs from the database
    cursor.execute("SELECT url FROM documents")
    existing_urls = {row[0] for row in cursor.fetchall()}
    
    # Process new links
    new_count = 0
    for url in links:
        if url not in existing_urls:
            title, full_text = fetch_and_parse(url)
            if title and full_text:
                cursor.execute(
                    "INSERT INTO documents (url, title, content) VALUES (?, ?, ?)",
                    (url, title, full_text)
                )
                new_count += 1
    
    conn.commit()
    conn.close()
    
    if new_count > 0:
        print(f"Added {new_count} new documents to {db_path}")
    else:
        print("No new documents to add.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Process links and store in SQLite database.')
    parser.add_argument('links_file', type=str, help='The JSON file containing the links.')
    parser.add_argument('db_path', type=str, help='The SQLite database file path.')
    args = parser.parse_args()
    main(args.links_file, args.db_path)