# gem-search
Mining the Hidden Gems of the internet

## Project Structure

- `/frontend`: React TypeScript frontend
- `/search`: FastAPI backend with SQLite database

## Getting Started

### Backend

1. Install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install fastapi uvicorn pandas nltk rank_bm25 newspaper3k
   ```

2. Initialize the SQLite database:
   ```
   cd search
   python init_sqlite_db.py
   ```

3. Build the search index:
   ```
   cd search
   python tokenize_docs.py search.db
   ```

4. Run the backend server:
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
3. Rebuild the search index:
   ```
   cd search
   python tokenize_docs.py search.db
   ```