# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gem-search is a web application for "Mining the Hidden Gems of the internet". It consists of two main components:

1. **Backend (Python/FastAPI)**: Located in the `/search` directory, it provides a search API using BM25 ranking algorithm with a SQLite database.
2. **Frontend (React/TypeScript)**: Located in the `/frontend` directory, it provides a web interface for searching content.

## Development Commands

### Backend (Python)

To initialize the SQLite database:
```bash
cd search
python init_sqlite_db.py
```

To build the search index:
```bash
cd search
python tokenize_docs.py search.db
```

To run the FastAPI server:
```bash
cd search
# Make sure you have the required dependencies installed:
pip install fastapi uvicorn pandas nltk rank_bm25 newspaper3k
# Start the server
uvicorn main:app --reload
```

To scrape new content:
```bash
cd search
python scrapers/util.py scrapers/links.json search.db
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

1. **Data Collection**:
   - `scrapers/util.py` fetches and parses content from URLs listed in `links.json`
   - Extracted content is stored in a SQLite database (`search.db`)

2. **Search Engine**:
   - `tokenize_docs.py` processes the content from the SQLite database and creates a BM25 index
   - `main.py` exposes a FastAPI endpoint `/search` that accepts POST requests with search queries
   - The endpoint uses the BM25 index to find relevant documents and returns them

3. **Database Schema**:
   The SQLite database has a single table `documents` with the following schema:
   ```
   CREATE TABLE documents (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       url TEXT UNIQUE,
       title TEXT,
       content TEXT
   )
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

1. Initialize the database (if not already done): `python init_sqlite_db.py`
2. Build the search index: `python tokenize_docs.py search.db`
3. Start the backend server: `uvicorn main:app --reload`
4. Start the frontend development server: `npm start`
5. Make changes to code
6. For backend changes, the server will automatically reload
7. For frontend changes, the page will automatically reload