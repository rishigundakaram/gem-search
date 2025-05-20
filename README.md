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
   pip install -r requirements.txt
   ```

2. Initialize the SQLite database (uses Alembic migrations):
   ```
   cd search
   python init_sqlite_db.py
   ```
   
   This runs Alembic migrations to create the database schema.

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

### Using the Advanced Crawler (Recommended)

The advanced crawler can discover blog articles from source URLs:

1. Add base URLs to `search/scrapers/links.json` (these are the main blog URLs)
2. Run the crawler to discover and extract content:
   ```
   cd search
   python -m crawler.crawler --sources_file scrapers/links.json
   ```

3. Process any pending links:
   ```
   cd search
   python -m crawler.crawler --process_pending
   ```

### Testing the Crawler

#### Manual Verification

For a quick manual test of the crawler components:

```
cd gem-search
python test_crawler.py
```

This will verify that the key components (link discovery, article classification, content extraction) work with real URLs and will automatically check for missing dependencies.

#### Automated Tests

The crawler includes a comprehensive test suite that uses mocks to avoid external dependencies:

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run the tests from the project root:
   ```
   PYTHONPATH=$PYTHONPATH:$(pwd) pytest search/tests/crawler
   ```

3. Test a specific component:
   ```
   PYTHONPATH=$PYTHONPATH:$(pwd) pytest search/tests/crawler/test_utils.py
   ```

Note: Setting PYTHONPATH ensures the tests can locate all the necessary modules.

### Using the Simple Scraper

For direct article links:

1. Add article URLs to `search/scrapers/links.json`
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