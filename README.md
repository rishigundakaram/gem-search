# Gem Search 💎

**Mining the Hidden Gems of the Internet**

A modern full-stack web application for discovering and searching web content using advanced text extraction and full-text search capabilities.

## 🏗️ Architecture

- **Frontend**: React TypeScript with Material-UI components
- **Backend**: FastAPI with SQLite FTS5 full-text search
- **Text Extraction**: Trafilatura + newspaper3k fallback chain
- **Database**: SQLite with FTS5 extension for fast search
- **Migrations**: yoyo-migrations with raw SQL for schema management
- **Testing**: pytest, Ruff, Black with comprehensive CI/CD
- **Dependencies**: Poetry for Python, npm for Node.js

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+** 
- **Poetry** (for dependency management)
- **Node.js 18+** (for frontend)
- **SQLite with FTS5** (usually included in modern Python)

### 🚀 Setup

```bash
# 1. Install backend dependencies
poetry install

# 2. Initialize database (creates tables and FTS5 setup)
cd backend
poetry run python init_db.py

# 3. Run database migrations (yoyo-migrations)
yoyo apply

# 4. Install frontend dependencies  
cd ../frontend
npm install

# 5. Start backend server (in one terminal)
cd ../backend  
poetry run uvicorn app.main:app --reload

# 6. Start frontend development server (in another terminal)
cd ../frontend
npm start
```

Open [http://localhost:3000](http://localhost:3000) to access the application.

## 📊 Features

### 🔍 **Advanced Text Extraction**
- **Trafilatura** for superior content extraction from web pages
- **newspaper3k** fallback for structured article extraction  
- **Plain text** support for text files
- Handles diverse content types and website structures

### 🚀 **Fast Full-Text Search**
- SQLite FTS5 with Porter stemming
- Ranked search results by relevance
- Real-time search as you type
- Handles complex queries and phrase matching

### 🕷️ **Intelligent Web Scraping**
- Automated link discovery with configurable depth
- Respect for robots.txt and rate limiting
- Duplicate detection and smart filtering
- Cross-domain and same-domain crawling options

### 📱 **Modern UI/UX**  
- Clean, responsive Material-UI interface
- Real-time search with instant results
- Mobile-friendly design
- Keyboard shortcuts and accessibility

## 🛠️ Development

### Quality Assurance

Run comprehensive pre-push checks:
```bash
./scripts/pre-push.sh
```

This validates:
- ✅ Ruff linting and code quality
- ✅ Black code formatting  
- ✅ Backend unit tests with coverage
- ✅ Integration tests
- ✅ Frontend tests and build

### Testing

```bash
# Backend tests
poetry run pytest backend/tests/ -v

# Integration tests  
poetry run pytest tests/ -v

# Frontend tests
cd frontend && npm test

# All tests
poetry run pytest -v
```

### Code Quality

```bash
# Linting
poetry run ruff check backend/ tests/

# Formatting
poetry run black backend/ tests/

# Auto-fix issues
poetry run ruff check --fix backend/ tests/
poetry run black backend/ tests/
```

## 🗄️ Database Management

### Database Migrations with yoyo-migrations

The project uses **yoyo-migrations** for managing database schema changes with raw SQL migrations.

#### Basic Migration Commands

```bash
cd backend

# Apply pending migrations
yoyo apply

# Rollback last migration  
yoyo rollback

# List migration status
yoyo list

# Show migration history
yoyo show-applied
```

#### Creating New Migrations

1. **Create migration files** in `backend/migrations/` with format: `NNN_description.sql`
2. **Add SQL commands** for the migration
3. **Create rollback file**: `NNN_description_rollback.sql` 
4. **Apply with**: `yoyo apply`

#### Migration Naming Convention

```
backend/migrations/
├── 001_initial_schema.sql              # Creates documents and FTS5 tables
├── 001_initial_schema_rollback.sql     # Rollback for initial schema
├── 002_add_embeddings.sql              # Future: Add vector embeddings
└── 002_add_embeddings_rollback.sql     # Rollback for embeddings
```

#### Example Migration

**002_add_timestamps.sql:**
```sql
-- Add timestamps to documents table
ALTER TABLE documents ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE documents ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- step: 002_add_timestamps
```

**002_add_timestamps_rollback.sql:**
```sql
-- Remove timestamp columns
ALTER TABLE documents DROP COLUMN created_at;
ALTER TABLE documents DROP COLUMN updated_at;

-- step: 002_add_timestamps_rollback
```

#### Migration Configuration

See `backend/yoyo.ini` for configuration:
- Database path: `sqlite:///search.db`
- Migration directory: `migrations/`
- Batch mode and verbosity settings

### Adding Content

#### Automated Discovery (Recommended)
```bash
cd backend

# Add starter URLs to data/links.json, then:
poetry run python app/scraper.py data/links.json search.db --discover-depth 2 --allow-cross-domain
```

#### Manual Addition
```bash
cd backend

# Add URLs to data/links.json, then:
poetry run python app/scraper.py data/links.json search.db
```

#### Reddit Content Discovery
```bash
cd backend

# Scrape r/InternetIsBeautiful with link discovery
poetry run python app/reddit_scraper.py --continuous --discover-depth 2 --max-pages 5
```

## 🌐 API Reference

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | Health check and system status |
| `/search` | POST | Search content: `{"query": "search terms"}` |

### Example API Usage

```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence"}'
```

## 🚢 Deployment

### Backend
```bash
cd backend
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend  
```bash
cd frontend
npm run build
# Serve the build/ directory with your preferred static server
```

## 🔧 Configuration

### Environment Variables
- `DATABASE_URL`: SQLite database path (default: `sqlite:///search.db`)

### Migration Configuration
See `backend/yoyo.ini` for migration settings.

## 📋 Project Structure

```
gem-search/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application  
│   │   ├── database.py        # Database connection
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── scraper.py         # Trafilatura web scraping
│   │   └── reddit_scraper.py  # Reddit content discovery
│   ├── migrations/            # yoyo-migrations SQL files
│   │   ├── 001_initial_schema.sql
│   │   └── 001_initial_schema_rollback.sql
│   ├── tests/                 # Backend unit tests
│   ├── data/                  # Seed data and links
│   ├── yoyo.ini              # Migration configuration
│   └── init_db.py            # Database initialization
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── containers/        # Container components  
│   │   └── api/              # API integration
│   └── public/               # Static assets
├── tests/                    # Integration tests
├── scripts/                  # Development scripts
│   └── pre-push.sh          # Quality assurance script
└── pyproject.toml           # Poetry configuration
```

## 🤝 Contributing

1. **Install dependencies**: `poetry install`
2. **Run quality checks**: `./scripts/pre-push.sh`  
3. **Make changes** and ensure all tests pass
4. **Submit PR** with clear description

## 📈 Performance

- **Fast search**: SQLite FTS5 with optimized indexing
- **Efficient scraping**: Trafilatura + intelligent rate limiting
- **Modern frontend**: React with optimized bundle size
- **CI/CD**: Automated testing and quality gates

## 🔒 Security

- Input validation and sanitization
- Rate limiting on API endpoints  
- Secure content extraction
- No sensitive data in repository

---

**Built with modern tools**: Poetry, Ruff, Black, pytest, FastAPI, React, TypeScript, SQLite FTS5, and yoyo-migrations.