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
   pip install fastapi uvicorn sqlalchemy alembic newspaper3k pandas beautifulsoup4 requests
   ```

2. Initialize the SQLite database:
   ```
   cd search
   python init_db.py
   ```
   
   This creates the SQLite database with FTS5 full-text search support.

3. Run the backend server:
   ```
   cd search
   uvicorn app.main:app --reload
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

### Using the Link Discovery System (Recommended)

The automated link discovery system can crawl and discover content from starter URLs:

1. Add starter URLs to `search/data/links.json`
2. Run the scraper with link discovery:
   ```
   cd search
   python app/scraper.py data/links.json search.db --discover-depth 2
   ```

Options:
- `--discover-depth N`: Crawl depth for link discovery (default: 1)
- `--allow-cross-domain`: Allow crawling across different domains

### Manual Content Addition

For direct article links:

1. Add article URLs to `search/data/links.json`
2. Run the basic scraper:
   ```
   cd search
   python app/scraper.py data/links.json search.db
   ```

## SQLite Full-Text Search

This project uses SQLite's FTS5 extension for efficient text search. FTS5 is required and the application will not run without it.

Key features:
- Full-text indexing for fast searches
- Porter stemming for better matching
- Ranking of search results by relevance
- Native SQLite integration

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /search` - Search content with JSON payload: `{"query": "search terms"}`

## Database Status

Currently contains **196 websites** indexed for search.

## Troubleshooting

### Backend Issues

1. **Server won't start**: Make sure you're using the correct command:
   ```
   uvicorn app.main:app --reload
   ```

2. **Import errors**: Ensure you're in the `search` directory when running commands.

3. **Database errors**: Run the database initialization:
   ```
   python init_db.py
   ```

4. **FTS5 not available**: Ensure your SQLite installation supports FTS5 extension.