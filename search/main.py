from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3

# Define database path
DB_PATH = 'search.db'

# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str

# Database connection function
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize the FastAPI application
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery, conn: sqlite3.Connection = Depends(get_db)):
    query = search_query.query.strip()
    
    cursor = conn.cursor()
    
    # Check if FTS5 is available and document_content table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_content'")
    has_fts = cursor.fetchone() is not None
    
    if has_fts:
        # Use FTS5 for searching
        cursor.execute(
            """
            SELECT d.title, d.url 
            FROM document_content AS c
            JOIN documents AS d ON c.document_id = d.id
            WHERE document_content MATCH ?
            ORDER BY rank
            LIMIT 10
            """, 
            (query,)
        )
    else:
        # Fallback to basic LIKE query
        like_pattern = f"%{query}%"
        cursor.execute(
            """
            SELECT title, url
            FROM documents
            WHERE content LIKE ?
            LIMIT 10
            """,
            (like_pattern,)
        )
    
    results = [{"title": row['title'], "url": row['url']} for row in cursor.fetchall()]
    
    return results

@app.get("/health")
async def health_check():
    return {"status": "ok"}