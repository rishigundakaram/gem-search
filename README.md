# Gem Search 💎

**Mining the Hidden Gems of the internet**

An intelligent content discovery and search engine that automatically crawls and indexes web content, making it searchable through a clean React interface.

## 🚀 Features

- **Automated Link Discovery**: Start with seed URLs and automatically discover linked content
- **Intelligent Content Extraction**: Uses newspaper3k for robust article and content parsing  
- **Full-Text Search**: SQLite FTS5 for fast, relevant search results
- **Duplicate Prevention**: Robust URL deduplication with database constraints
- **Configurable Crawling**: Control depth and domain scope
- **Modern UI**: Clean React/TypeScript frontend with real-time search

## 🏗️ Architecture

### Backend (Python/FastAPI)
```
search/
├── app/
│   ├── main.py          # FastAPI routes and search endpoints
│   ├── scraper.py       # Content discovery and extraction
│   ├── database.py      # SQLite setup and FTS5 configuration
│   └── models.py        # Data models
├── data/
│   └── links.json       # Starter URLs for discovery
└── init_db.py          # Database initialization
```

### Frontend (React/TypeScript)
```
frontend/
├── src/
│   ├── components/      # Search UI components
│   ├── api/            # Backend API integration
│   └── containers/     # Main app containers
└── public/             # Static assets
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- SQLite with FTS5 extension (usually included)

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd search
   pip install fastapi uvicorn requests newspaper3k beautifulsoup4 sqlalchemy
   ```

2. **Initialize database:**
   ```bash
   python init_db.py
   ```

3. **Add starter URLs to discover content:**
   ```bash
   # Edit data/links.json with your starter URLs
   echo '["https://danluu.com", "https://research.google.com/blog"]' > data/links.json
   ```

4. **Run content discovery:**
   ```bash
   # Discover and index content (1 level deep)
   python app/scraper.py data/links.json search.db --discover-depth 1
   
   # For deeper crawling (more content, takes longer)
   python app/scraper.py data/links.json search.db --discover-depth 3
   
   # Allow cross-domain discovery
   python app/scraper.py data/links.json search.db --allow-cross-domain
   ```

5. **Start the API server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. **Install and run:**
   ```bash
   cd frontend
   npm install
   npm start
   ```

2. **Open browser:** [http://localhost:3000](http://localhost:3000)

## 🔍 Content Discovery

### Automated Discovery (Recommended)
The scraper automatically discovers content from starter URLs:

- **Starter URLs** → **Discover linked pages** → **Extract content** → **Store in database**
- Configurable crawl depth (1-3 levels recommended)
- Domain filtering (same-domain or cross-domain)
- Automatic duplicate prevention

### Manual URLs
For specific articles, add direct URLs to `data/links.json` and run with `--discover-depth 0`.

### Command Options
```bash
# Basic discovery (1 level deep, same domain only)
python app/scraper.py data/links.json search.db

# Deep discovery (3 levels, finds more content)
python app/scraper.py data/links.json search.db --discover-depth 3

# Cross-domain discovery (finds content on different sites)
python app/scraper.py data/links.json search.db --allow-cross-domain

# Manual mode (only process exact URLs in JSON)
python app/scraper.py data/links.json search.db --discover-depth 0
```

## 🔧 Development

### API Endpoints
- `GET /health` - Health check
- `POST /search` - Search content with JSON payload: `{"query": "search terms"}`

### Database Schema
```sql
-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    content TEXT
);

-- Full-text search index
CREATE VIRTUAL TABLE document_content USING fts5(
    content,
    document_id UNINDEXED,
    tokenize='porter unicode61'
);
```

### Adding New Features
1. Backend changes: Modify files in `search/app/`
2. Frontend changes: Modify files in `frontend/src/`
3. Database changes: Update `search/app/database.py`

## 📊 Examples

### Sample Starter URLs
```json
[
  "https://danluu.com",
  "https://research.google.com/blog", 
  "https://engineering.fb.com",
  "https://netflixtechblog.com"
]
```

### Sample Search Results
After running discovery, you can search for:
- "machine learning algorithms"
- "distributed systems"
- "performance optimization"
- "software engineering best practices"

## 🛠️ Technical Stack

- **Backend**: FastAPI, SQLite FTS5, newspaper3k, BeautifulSoup
- **Frontend**: React, TypeScript, Create React App
- **Search**: SQLite Full-Text Search with Porter stemming
- **Content Extraction**: newspaper3k with fallback parsing
- **Deployment**: Vercel (frontend), self-hosted (backend)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and test locally
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.