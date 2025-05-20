from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
import sqlite3
from datetime import datetime

from db.database import get_db
from db.models import Link, Document

# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str

class LinkBase(BaseModel):
    url: str
    source_id: Optional[int] = None

class LinkCreate(LinkBase):
    pass

class LinkResponse(LinkBase):
    id: int
    status: str
    discovered_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

# Initialize the FastAPI application
app = FastAPI(
    title="Gem Search API",
    description="API for searching and managing web content",
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

@app.get("/links", response_model=List[LinkResponse])
async def get_links(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all non-deleted links."""
    links = db.query(Link).filter(Link.is_deleted == False).offset(skip).limit(limit).all()
    return links

@app.post("/links", response_model=LinkResponse)
async def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    """Add a new link."""
    # Check if link already exists
    existing = db.query(Link).filter(Link.url == link.url).first()
    if existing:
        if existing.is_deleted:
            # Undelete it
            existing.is_deleted = False
            existing.deleted_at = None
            db.commit()
            return existing
        return existing
    
    # Create new link
    new_link = Link(
        url=link.url,
        source_id=link.source_id,
        status='pending',
        discovered_at=datetime.utcnow(),
        is_deleted=False
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

@app.delete("/links/{link_id}", response_model=LinkResponse)
async def delete_link(link_id: int, db: Session = Depends(get_db)):
    """Soft delete a link."""
    link = db.query(Link).filter(Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    link.is_deleted = True
    link.deleted_at = datetime.utcnow()
    db.commit()
    return link

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}