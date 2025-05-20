from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.database import get_db

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

@app.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery, db: Session = Depends(get_db)):
    """Search documents using FTS5."""
    query = search_query.query.strip()
    
    try:
        # Use FTS5 for searching
        # We need to join to the links table to get URLs
        result = db.execute(text("""
            SELECT d.title, l.url 
            FROM document_content AS c
            JOIN documents AS d ON c.document_id = d.id
            JOIN links AS l ON d.link_id = l.id
            WHERE document_content MATCH :query
            AND l.is_deleted = 0
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