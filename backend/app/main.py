import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db, init_database

# API Key configuration
API_KEY = os.getenv("API_KEY", "gem-search-dev-key-12345")


def verify_api_key(x_api_key: Annotated[str, Header()]) -> str:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Define request and response models
class SearchQuery(BaseModel):
    query: str


class SearchResult(BaseModel):
    title: str
    url: str


# Initialize the FastAPI application
app = FastAPI(title="Gem Search API", description="API for searching web content", version="1.0.0")

# Configure CORS
origins = [
    "http://localhost:3000",
    "https://*.vercel.app",
    "https://gem-search-2.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize database on startup."""
    try:
        init_database()
    except Exception as e:
        print(f"Failed to initialize database: {e}")


@app.post("/search", response_model=list[SearchResult])
async def search(
    search_query: SearchQuery, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)
) -> list[SearchResult]:
    """Search documents using FTS5."""
    query = search_query.query.strip()

    # Return empty results for empty queries
    if not query:
        return []

    try:
        # Use FTS5 for searching with simple schema
        result = db.execute(
            text(
                """
            SELECT d.title, d.url
            FROM document_content AS c
            JOIN documents AS d ON c.document_id = d.id
            WHERE document_content MATCH :query
            ORDER BY rank
            LIMIT 10
        """
            ),
            {"query": query},
        ).fetchall()

        results = [SearchResult(title=row[0], url=row[1]) for row in result]
        return results
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}") from e


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
