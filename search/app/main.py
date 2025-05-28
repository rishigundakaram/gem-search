from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db, init_database

# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str

# Initialize the FastAPI application
app = FastAPI(
    title="Gem Search API",
    description="API for searching web content",
    version="1.0.0"
)

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

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_database()
    except Exception as e:
        print(f"Failed to initialize database: {e}")

@app.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery, db: Session = Depends(get_db)):
    """Search documents using FTS5."""
    query = search_query.query.strip()
    
    # Return empty results for empty queries
    if not query:
        return []
    
    try:
        # Use FTS5 for searching with simple schema
        result = db.execute(text("""
            SELECT d.title, d.url 
            FROM document_content AS c
            JOIN documents AS d ON c.document_id = d.id
            WHERE document_content MATCH :query
            ORDER BY rank
            LIMIT 10
        """), {"query": query}).fetchall()
        
        results = [{"title": row[0], "url": row[1]} for row in result]
        return results
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}