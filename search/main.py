from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
from functools import lru_cache

# Define database path
DB_PATH = 'search.db'

# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str

# Create a function that returns a new connection each time
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Get a cached connection
@lru_cache(maxsize=1)
def get_db():
    return get_connection()

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
async def search(search_query: SearchQuery):
    # Get a connection for this request
    conn = get_db()
    query = search_query.query.strip()
    
    cursor = conn.cursor()
    
    try:
        # Use FTS5 for searching - we assume the table exists
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
        
        results = [{"title": row['title'], "url": row['url']} for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"Search error: {e}")
        raise
    finally:
        cursor.close()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Proper application shutdown
@app.on_event("shutdown")
def shutdown_event():
    try:
        conn = get_db()
        conn.close()
        print("Database connection closed")
    except Exception as e:
        print(f"Error closing database: {e}")