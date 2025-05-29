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

To run database migrations:

```bash
cd backend
yoyo apply               # Apply pending migrations
yoyo rollback            # Rollback last migration
yoyo list                # List migration status
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

### Code Quality and Formatting

**CRITICAL: Always run linting and formatting before pushing**

Before pushing any code changes, run these commands to fix linting and formatting issues:

```bash
# Fix linting issues
poetry run ruff check backend/ --fix

# Format code with Black
poetry run black backend/

# Run type checking with MyPy
poetry run mypy backend/

# Run tests to ensure nothing is broken
cd backend && poetry run pytest tests/ -v
```

### Pre-Push Quality Checks

Before pushing code to the remote repository, run the comprehensive pre-push script:

```bash
./scripts/pre-push.sh
```

This script performs all CI/CD checks locally:
- ✅ Ruff linting and code quality checks
- ✅ Black code formatting verification  
- ✅ Backend unit tests with coverage
- ✅ Integration tests (if backend server available)
- ✅ Frontend tests and build verification
- 🚀 Provides clear feedback and helpful tips for fixing issues

The script ensures your code will pass CI/CD before pushing, saving time and preventing failed builds.

### Pre-Push Hook

A pre-push hook is automatically installed that runs all CI/CD checks locally before allowing pushes. If checks fail, you'll be prompted to either fix the issues or push anyway.

The pre-push hook runs:
- ✅ Ruff linting and code quality checks
- ✅ Black code formatting verification
- ✅ MyPy type checking
- ✅ Backend unit tests with coverage
- ✅ Integration tests
- ✅ Frontend tests and build verification (if applicable)

If any checks fail, you'll see helpful tips for fixing issues and be asked if you want to push anyway. This prevents pushing code that would fail CI/CD.

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
├── migrations/          # Database migrations (yoyo-migrations)
│   └── *.sql           # SQL migration files
├── tests/
│   ├── test_scraper.py  # Comprehensive scraper tests
│   └── __init__.py
├── data/
│   └── links.json       # URLs to scrape
├── yoyo.ini            # Migration configuration
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
3. Run database migrations: `cd backend && yoyo apply`
4. Scrape content: `cd backend && poetry run python app/scraper.py data/links.json search.db`
5. Run tests: `poetry run pytest` or `./scripts/pre-push.sh`
6. Start the backend server: `cd backend && poetry run uvicorn app.main:app --reload`
7. Start the frontend development server: `cd frontend && npm start`
8. Make changes to code - servers will automatically reload

## Database Migrations

Database schema changes are managed using yoyo-migrations. All migrations are written in raw SQL.

### Creating a new migration:

1. Create a new SQL file in `backend/migrations/` with format: `NNN_description.sql`
2. Add the migration SQL
3. Create a corresponding rollback file: `NNN_description_rollback.sql`
4. Apply with: `cd backend && yoyo apply`

### Migration naming convention:
- `001_initial_schema.sql` / `001_initial_schema_rollback.sql`
- `002_add_embeddings.sql` / `002_add_embeddings_rollback.sql`

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:
- **Backend Tests**: Python 3.11/3.12 with pytest, coverage reporting
- **Frontend Tests**: Node.js with npm test and build verification
- **Linting**: Ruff and Black for Python code quality
- **Type Checking**: MyPy for static type analysis
- **Integration**: Full API testing with both services running

## Development notes

1. Do not include any demo code, examples, or unused code in the final PR. It's really important to keep
   PRs non-bloated and crisp because otherwise they're hard to review.

## ⚠️ CRITICAL: CI/CD Compliance Requirements

**NEVER PUSH CODE THAT FAILS CI/CD CHECKS**

Before pushing any code changes, you MUST ensure all CI/CD checks pass locally:

### Required Checks (ALL must pass):
```bash
# 1. Linting
poetry run ruff check backend/ tests/

# 2. Code formatting 
poetry run black --check backend/ tests/

# 3. Type checking
poetry run mypy backend/

# 4. Unit tests
poetry run pytest backend/tests/ -v

# 5. Integration tests
poetry run pytest tests/ -v
```

### 🚫 NEVER:
- Push code with failing tests
- Push code with type errors
- Push code with linting violations
- Push code with formatting issues
- Bypass pre-push hooks with `--no-verify` unless fixing the hook itself

### ✅ ALWAYS:
- Run all checks locally before pushing
- Fix ALL issues before pushing
- Use the pre-push hook - it prevents CI/CD failures
- If pre-push hook fails, fix the issues instead of bypassing

### Emergency Override:
If you must bypass checks for urgent fixes, document why in the commit message and create an immediate follow-up PR to fix the issues.

## Type Hinting Requirements

**ALL functions must have complete type annotations**

### Required Type Annotations:
```python
# ✅ Good - All parameters and return types annotated
def process_data(items: list[str], threshold: int = 10) -> ProcessResult:
    return ProcessResult(processed=items, count=len(items))

# ❌ Bad - Missing type annotations
def process_data(items, threshold=10):
    return {"processed": items, "count": len(items)}
```

### Complex Return Types - Create Classes:
When return types become complex (multiple values, nested structures), create dedicated classes:

```python
from dataclasses import dataclass
from typing import Any

# ❌ Bad - Complex tuple return type
def analyze_content(text: str) -> tuple[str | None, str | None, int, dict[str, Any]]:
    return title, summary, word_count, metadata

# ✅ Good - Dedicated class for complex return
@dataclass
class ContentAnalysis:
    title: str | None
    summary: str | None
    word_count: int
    metadata: dict[str, Any]

def analyze_content(text: str) -> ContentAnalysis:
    return ContentAnalysis(
        title=title,
        summary=summary, 
        word_count=word_count,
        metadata=metadata
    )
```

### Type Annotation Guidelines:

1. **Use Modern Python Syntax** (Python 3.10+):
   - `list[str]` instead of `List[str]`
   - `dict[str, int]` instead of `Dict[str, int]`
   - `str | None` instead of `Optional[str]`

2. **Be Specific with Collections**:
   ```python
   # ✅ Specific
   def get_user_ids() -> set[int]:
   def parse_config() -> dict[str, str | int]:
   
   # ❌ Too generic  
   def get_user_ids() -> set:
   def parse_config() -> dict:
   ```

3. **Create Classes for Complex Structures**:
   ```python
   from dataclasses import dataclass
   
   # When you have 3+ return values or nested data:
   @dataclass 
   class ScrapingResult:
       urls_found: int
       documents_created: int
       errors: list[str]
       next_page_token: str | None = None
   ```

4. **Handle External Libraries**:
   ```python
   from typing import TYPE_CHECKING
   
   if TYPE_CHECKING:
       from requests import Response
       from sqlalchemy.orm import Session
   ```

5. **Use Type Aliases for Complex Types**:
   ```python
   # For frequently used complex types
   URLMapping = dict[str, tuple[str, int]]
   ConfigDict = dict[str, str | int | bool]
   
   def process_urls(mapping: URLMapping) -> ConfigDict:
       pass
   ```

### When to Create New Classes:

- **3+ return values**: Always use a class instead of tuple
- **Nested dictionaries**: Create structured classes
- **API responses**: Define response models
- **Configuration objects**: Use dataclasses or Pydantic models

### MyPy Integration:
- All code must pass `poetry run mypy backend/` with zero errors
- Use `# type: ignore[error-code]` sparingly and only with comments explaining why
- Add missing type stubs when needed: `poetry add types-library-name --group dev`

## Testing Requirements

**CRITICAL: Always run tests before submitting code to the user**

### Running Tests

```bash
cd backend
poetry run pytest tests/ -v
```

### Test Coverage Requirements

- **All new functions must have tests** - No exceptions
- **All modified functions must have updated tests**
- **All tests must pass** before submitting code
- **Integration tests should use mocked external dependencies**

### Test Categories

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test component interactions 
3. **API Tests**: Test HTTP endpoints
4. **Database Tests**: Test database operations with temp databases

### Test Patterns

- Use `pytest` fixtures for setup/teardown
- Mock external dependencies (HTTP calls, file operations)
- Use temporary databases for database tests
- Test both success and error cases
- Include edge cases and validation tests

### Pre-Submission Checklist

Before submitting ANY code changes:

1. ✅ Run `poetry run pytest tests/ -v` 
2. ✅ All tests pass (no failures, no errors)
3. ✅ New code has corresponding tests
4. ✅ Modified code has updated tests
5. ✅ No commented-out code or debug prints

**If tests fail or are missing, do not submit code to the user until fixed.**
