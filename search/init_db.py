#!/usr/bin/env python3
"""
Simple database initialization script.
Creates the SQLite database with documents table and FTS5 support.
"""

from app.database import init_database

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
    print("You can now run the scraper or API server.")