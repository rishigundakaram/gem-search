#!/usr/bin/env python3
"""
Demo script for the simple scraper
Shows how to use the simplified scraper to process links
"""

import os
import json
from simple_scraper import process_links_from_json, process_pending_links

def main():
    """Run a demo of the simple scraper"""
    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(current_dir), 'search.db')
    links_file = os.path.join(current_dir, 'links.json')
    
    # Ensure links.json exists
    if not os.path.exists(links_file):
        # Create a sample links file if it doesn't exist
        sample_links = [
            "https://research.google/blog/announcing-scann-efficient-vector-similarity-search/",
            "https://danluu.com/seo-spam/"
        ]
        with open(links_file, 'w') as f:
            json.dump(sample_links, f, indent=2)
        print(f"Created sample links file at {links_file}")
    
    # Process links from the JSON file
    print("Processing links from JSON file...")
    process_links_from_json(db_path, links_file)
    
    # Process any pending links
    print("\nProcessing any pending links...")
    process_pending_links(db_path)
    
    print("\nDemo complete! Database is available at:", db_path)
    print("You can now run the search API with uvicorn main:app --reload")

if __name__ == "__main__":
    main()