"""
Vector search module for Gem Search.
Handles embedding generation and vector similarity search.
"""
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
import faiss

class VectorSearch:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector search with a sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index = None
        self.document_ids = []
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a given text."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.astype(np.float32)
    
    def serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Serialize embedding for database storage."""
        return pickle.dumps(embedding)
    
    def deserialize_embedding(self, embedding_bytes: bytes) -> np.ndarray:
        """Deserialize embedding from database."""
        return pickle.loads(embedding_bytes)
    
    def build_index(self, db: Session):
        """Build FAISS index from all embeddings in the database."""
        result = db.execute(text("""
            SELECT id, embedding FROM documents 
            WHERE embedding IS NOT NULL
        """)).fetchall()
        
        if not result:
            print("No embeddings found in database")
            return
        
        embeddings = []
        document_ids = []
        
        for doc_id, embedding_bytes in result:
            if embedding_bytes:
                embedding = self.deserialize_embedding(embedding_bytes)
                embeddings.append(embedding)
                document_ids.append(doc_id)
        
        if embeddings:
            embeddings_array = np.vstack(embeddings)
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            self.index.add(embeddings_array)
            self.document_ids = document_ids
            print(f"Built FAISS index with {len(embeddings)} embeddings")
    
    def search_similar(self, query: str, db: Session, top_k: int = 10) -> List[Tuple[str, str, float]]:
        """Search for similar documents using vector similarity."""
        if self.index is None or len(self.document_ids) == 0:
            self.build_index(db)
            if self.index is None:
                return []
        
        query_embedding = self.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.document_ids)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid result
                doc_id = self.document_ids[idx]
                doc_result = db.execute(text("""
                    SELECT title, url FROM documents WHERE id = :doc_id
                """), {"doc_id": doc_id}).fetchone()
                
                if doc_result:
                    title, url = doc_result
                    results.append((title, url, float(score)))
        
        return results

# Global instance
vector_search = VectorSearch()