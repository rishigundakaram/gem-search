# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gem-search is a web application for "Mining the Hidden Gems of the internet". It consists of two main components:

1. **Backend (Python/FastAPI)**: Located in the `/backend` directory, it provides a search API using Trafilatura text extraction with a SQLite database.
2. **Frontend (React/TypeScript)**: Located in the `/frontend` directory, it provides a web interface for searching content.

## Development Commands

### Project Setup

Install Poetry and dependencies:

```bash
poetry install
```

### Backend (Python)

To initialize the SQLite database:

```bash
cd backend
poetry run python init_db.py
```

To run the FastAPI server:

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

To scrape new content:

```bash
cd backend
poetry run python app/scraper.py data/links.json search.db
```

To run backend tests:

```bash
poetry run pytest backend/tests/ -v
```

### Integration Tests

To run all tests (backend + integration):

```bash
poetry run pytest -v
```

To run tests locally (mimics CI/CD):

```bash
python scripts/run_tests.py
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
backend/
├── app/
│   ├── database.py      # Database connection and initialization
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # SQLAlchemy models
│   └── scraper.py       # Content scraping functionality with Trafilatura
├── tests/
│   ├── test_scraper.py  # Comprehensive scraper tests
│   └── __init__.py
├── data/
│   └── links.json       # URLs to scrape
└── init_db.py          # Database initialization script
```

1. **Data Collection**:
   - `app/scraper.py` fetches and parses content from URLs listed in `data/links.json`
   - Uses Trafilatura for superior text extraction with newspaper3k fallback
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

1. Install dependencies: `poetry install`
2. Initialize the database: `cd backend && poetry run python init_db.py`
3. Scrape content: `cd backend && poetry run python app/scraper.py data/links.json search.db`
4. Run tests: `poetry run pytest` or `python scripts/run_tests.py`
5. Start the backend server: `cd backend && poetry run uvicorn app.main:app --reload`
6. Start the frontend development server: `cd frontend && npm start`
7. Make changes to code - servers will automatically reload

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:
- **Backend Tests**: Python 3.11/3.12 with pytest, coverage reporting
- **Frontend Tests**: Node.js with npm test and build verification
- **Linting**: Ruff and Black for Python, ESLint for TypeScript
- **Security**: Safety and Bandit security checks
- **Integration**: Full API testing with both services running

## Development notes

1. Do not include any demo code, examples, or unused code in the final PR. It's really important to keep
   PRs non-bloated and crisp because otherwise they're hard to review.
