import os
import sys
from scrapers.scraper import Scraper

# Constants
DB_PATH = 'search.db'
LINKS_FILE = 'scrapers/links.json'

def main():
    """Import links from the existing links.json file."""
    # Check if the links file exists
    if not os.path.exists(LINKS_FILE):
        print(f"Links file not found: {LINKS_FILE}")
        return False
    
    # Initialize the scraper
    scraper = Scraper(DB_PATH)
    
    # Process links
    print(f"Processing links from {LINKS_FILE}...")
    result = scraper.process_links_from_json(
        LINKS_FILE,
        source_name="Default Source",
        source_url="https://example.com"
    )
    
    if result:
        print("Successfully imported links")
    else:
        print("Error importing links")
    
    return result

if __name__ == "__main__":
    main()