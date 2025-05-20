from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import pickle
from rank_bm25 import BM25Okapi
import nltk

# Define database path
DB_PATH = 'search.db'
INDEX_PATH = 'bm25_index.pkl'

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

# Load the BM25 index
with open(INDEX_PATH, 'rb') as f:
    index_data = pickle.load(f)
    tokenized_documents = index_data['tokenized_documents']
    doc_ids = index_data['doc_ids']

# Initialize the BM25 model
bm25 = BM25Okapi(tokenized_documents)

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
    # Tokenize the query
    tokenized_query = nltk.word_tokenize(search_query.query.lower())
    
    # Get top document indices from BM25
    top_doc_indices = bm25.get_top_n(tokenized_query, list(range(len(tokenized_documents))), n=10)
    
    # Get the corresponding document IDs from our stored mapping
    top_doc_ids = [doc_ids[idx] for idx in top_doc_indices]
    
    # Fetch the actual documents from the database
    placeholders = ', '.join(['?' for _ in top_doc_ids])
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT title, url FROM documents WHERE id IN ({placeholders})",
        top_doc_ids
    )
    
    # Convert to response format
    results = [{"title": row['title'], "url": row['url']} for row in cursor.fetchall()]
    
    return results

@app.get("/health")
async def health_check():
    return {"status": "ok"}