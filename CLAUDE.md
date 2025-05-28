# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gem-search is a web application for "Mining the Hidden Gems of the internet". It consists of two main components:

1. **Backend (Python/FastAPI)**: Located in the `/search` directory, it provides a search API using BM25 ranking algorithm with a SQLite database.
2. **Frontend (React/TypeScript)**: Located in the `/frontend` directory, it provides a web interface for searching content.

## Development Commands

### Backend (Python)

To install dependencies:

```bash
cd search
pip install -r requirements.txt
```

To initialize the SQLite database:

```bash
cd search
python init_db.py
```

To run database migrations:

```bash
cd search
yoyo apply               # Apply pending migrations
yoyo rollback            # Rollback last migration
yoyo list                # List migration status
```

To run the FastAPI server:

```bash
cd search
uvicorn app.main:app --reload
```

To scrape new content:

```bash
cd search
python app/scraper.py data/links.json search.db
```

To run tests:

```bash
cd search
pytest
```

### Frontend (React/TypeScript)

To run the frontend development server:

```bash
cd frontend
npm install  # Only needed first time or when dependencies change
npm start    # Runs app in development mode at http://localhost:3000
```

Other available commands:

```bash
cd frontend
npm run build  # Build for production to the 'build' folder
npm test       # Run tests in interactive watch mode
```

## Architecture

### Backend Architecture

The backend follows a clean, modular structure:

```
search/
├── app/
│   ├── database.py      # Database connection and initialization
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # SQLAlchemy models
│   └── scraper.py       # Content scraping functionality
├── migrations/          # Database migrations (yoyo-migrations)
│   └── *.sql           # SQL migration files
├── tests/
│   ├── test_api.py      # API endpoint tests
│   └── test_scraper.py  # Scraper functionality tests
├── data/
│   └── links.json       # URLs to scrape
├── yoyo.ini            # Migration configuration
└── init_db.py          # Database initialization script
```

1. **Data Collection**:
   - `app/scraper.py` fetches and parses content from URLs listed in `data/links.json`
   - Uses newspaper3k for content extraction
   - Stores content in SQLite database with FTS5 for full-text search

2. **Search Engine**:
   - `app/main.py` exposes FastAPI endpoints
   - `/search` endpoint uses SQLite FTS5 for fast full-text search
   - `/health` endpoint for status checks

3. **Database Schema**:
   ```sql
   CREATE TABLE documents (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       url TEXT UNIQUE,
       title TEXT,
       content TEXT
   );
   
   CREATE VIRTUAL TABLE document_content USING fts5(
       content,
       document_id UNINDEXED,
       tokenize='porter unicode61'
   );
   ```

### Frontend Architecture

1. **API Integration**:

   - `api/SearchAPI.ts` handles communication with the backend API

2. **Component Structure**:

   - `containers/SearchContainer.tsx`: Main container component that handles state and search logic
   - `components/SearchBar.tsx`: UI component for entering search queries
   - `components/SearchResults.tsx`: UI component for displaying search results

3. **Data Flow**:
   - User enters a query in SearchBar
   - SearchContainer calls the API via SearchAPI.ts
   - Results are displayed in SearchResults component

## Development Workflow

1. Install dependencies: `pip install -r requirements.txt`
2. Run database migrations: `yoyo apply`
3. Scrape content: `python app/scraper.py data/links.json search.db`
4. Run tests: `pytest`
5. Start the backend server: `uvicorn app.main:app --reload`
6. Start the frontend development server: `npm start`
7. Make changes to code - servers will automatically reload

## Database Migrations

Database schema changes are managed using yoyo-migrations. All migrations are written in raw SQL.

### Creating a new migration:

1. Create a new SQL file in `search/migrations/` with format: `NNN_description.sql`
2. Add the migration SQL
3. Create a corresponding rollback file: `NNN_description_rollback.sql`
4. Apply with: `yoyo apply`

### Migration naming convention:
- `001_initial_schema.sql` / `001_initial_schema_rollback.sql`
- `002_add_embeddings.sql` / `002_add_embeddings_rollback.sql`

## Development notes

1. Do not include any demo code, examples, or unused code in the final PR. It's really important to keep
   PRs non-bloated and crisp because otherwise they're hard to review.
