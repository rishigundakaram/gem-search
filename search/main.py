from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
import os

# Define request and response models
class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    title: str
    url: str

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

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search.db')

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery):
    """Search documents using FTS5"""
    query = search_query.query.strip()
    
    if not query:
        return []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use FTS5 for searching
        # Join to the links and documents tables to get URLs and titles
        cursor.execute("""
            SELECT d.title, l.url 
            FROM document_content AS c
            JOIN documents AS d ON c.document_id = d.id
            JOIN links AS l ON d.link_id = l.id
            WHERE document_content MATCH ? 
            AND l.is_deleted = 0
            ORDER BY rank
            LIMIT 10
        """, (query,))
        
        results = []
        for row in cursor.fetchall():
            results.append({"title": row["title"], "url": row["url"]})
        
        conn.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/links")
async def get_links(skip: int = 0, limit: int = 10):
    """Get all non-deleted links"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, status, discovered_at, last_processed_at, is_deleted
            FROM links 
            WHERE is_deleted = 0
            LIMIT ? OFFSET ?
        """, (limit, skip))
        
        links = []
        for row in cursor.fetchall():
            links.append(dict(row))
        
        conn.close()
        return links
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/links")
async def create_link(url: str):
    """Add a new link"""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if link already exists
        cursor.execute("SELECT id, is_deleted FROM links WHERE url = ?", (url,))
        existing = cursor.fetchone()
        
        if existing:
            link_id = existing["id"]
            is_deleted = existing["is_deleted"]
            
            if is_deleted:
                # Undelete it
                cursor.execute(
                    "UPDATE links SET is_deleted = 0, status = 'pending' WHERE id = ?", 
                    (link_id,)
                )
                conn.commit()
            
            conn.close()
            return {"id": link_id, "url": url, "status": "pending"}
        
        # Create new link
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "INSERT INTO links (url, status, discovered_at) VALUES (?, ?, ?)",
            (url, 'pending', now)
        )
        
        link_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": link_id, "url": url, "status": "pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/links/{link_id}")
async def delete_link(link_id: int):
    """Soft delete a link"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if link exists
        cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
        existing = cursor.fetchone()
        
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Link not found")
        
        # Soft delete the link
        now = datetime.utcnow().isoformat()
        cursor.execute(
            "UPDATE links SET is_deleted = 1, deleted_at = ? WHERE id = ?",
            (now, link_id)
        )
        
        conn.commit()
        conn.close()
        
        return {"id": link_id, "status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}