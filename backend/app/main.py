import os
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.embedding_service import get_embedding_service

# API Key configuration
API_KEY = os.getenv("API_KEY", "gem-search-dev-key-12345")


def verify_api_key(x_api_key: Annotated[str, Header()]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Define request and response models
class SearchQuery(BaseModel):
    query: str


class SearchResult(BaseModel):
    title: str
    url: str


class EmbedQuery(BaseModel):
    text: str


class EmbedResponse(BaseModel):
    embedding: list[float]


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


# Database is initialized via migrations (yoyo apply)
# No need for startup initialization


@app.post("/search", response_model=list[SearchResult])
async def search(
    search_query: SearchQuery, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)
):
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

        results = [{"title": row[0], "url": row[1]} for row in result]
        return results
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}") from e


@app.post("/embed", response_model=EmbedResponse)
async def embed_text(
    embed_query: EmbedQuery, api_key: str = Depends(verify_api_key)
):
    """Generate text embedding using Jina CLIP v2 model."""
    text = embed_query.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        embedding_service = get_embedding_service()
        embedding = embedding_service.embed_text(text)
        return {"embedding": embedding}
    except Exception as e:
        print(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}") from e


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
