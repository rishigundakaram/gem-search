# gem-search
Mining the Hidden Gems of the internet

## Project Structure

- `/frontend`: React TypeScript frontend
- `/search`: FastAPI backend with SQLite Full-Text Search

## Getting Started

### Backend

1. Install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn pandas newspaper3k
   ```

2. Initialize the SQLite database:
   ```
   cd search
   python init_sqlite_db.py
   ```

3. Run the backend server:
   ```
   cd search
   uvicorn main:app --reload
   ```

### Frontend

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Run the frontend:
   ```
   cd frontend
   npm start
   ```

3. Open browser at [http://localhost:3000](http://localhost:3000)

## Adding New Content

To add new links to the database:

1. Add URLs to `search/scrapers/links.json`
2. Run the scraper:
   ```
   cd search
   python scrapers/util.py scrapers/links.json search.db
   ```

## SQLite Full-Text Search

This project uses SQLite's FTS5 extension for efficient text search. FTS5 is required and the application will not run without it.

Key features:
- Full-text indexing for fast searches
- Porter stemming for better matching
- Ranking of search results by relevance
- Native SQLite integration