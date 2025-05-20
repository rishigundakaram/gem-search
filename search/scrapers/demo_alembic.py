#!/usr/bin/env python3
"""
Demo script for the SQLAlchemy-integrated scraper
Shows how to use the scraper with Alembic migrations
"""

import os
import json
import sys
import subprocess
from alembic_scraper import process_links_from_json, process_pending_links

def run_alembic_migrations():
    """Run Alembic migrations to ensure database is up to date"""
    print("Running Alembic migrations...")
    
    # Get the parent directory (search)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Change to parent directory where alembic.ini is located
    original_dir = os.getcwd()
    os.chdir(parent_dir)
    
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print("Database schema is up to date!")
        else:
            print(f"Error running migrations: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(original_dir)
    
    return True

def main():
    """Run a demo of the SQLAlchemy-integrated scraper"""
    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
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
    
    # Run migrations
    if not run_alembic_migrations():
        print("Failed to run migrations. Exiting.")
        return
    
    # Process links from the JSON file
    print("\nProcessing links from JSON file...")
    process_links_from_json(links_file)
    
    # Process any pending links
    print("\nProcessing any pending links...")
    process_pending_links()
    
    print("\nDemo complete!")
    print("You can now run the search API with: uvicorn main:app --reload")

if __name__ == "__main__":
    main()