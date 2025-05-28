"""
Script to generate embeddings for existing documents in the database.
Run this after updating the database schema to add embeddings.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.vector_search import vector_search

def generate_embeddings_for_existing_docs(db_path="search.db"):
    """Generate embeddings for all documents that don't have them yet."""
    engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Get documents without embeddings
        result = db.execute(text("""
            SELECT id, title, content FROM documents 
            WHERE embedding IS NULL AND content IS NOT NULL
        """)).fetchall()
        
        print(f"Found {len(result)} documents without embeddings")
        
        for doc_id, title, content in result:
            # Combine title and content for embedding
            text_to_embed = f"{title or ''} {content or ''}".strip()
            
            if text_to_embed:
                print(f"Generating embedding for document {doc_id}: {title}")
                embedding = vector_search.generate_embedding(text_to_embed)
                embedding_bytes = vector_search.serialize_embedding(embedding)
                
                # Update the document with the embedding
                db.execute(text("""
                    UPDATE documents SET embedding = :embedding WHERE id = :doc_id
                """), {"embedding": embedding_bytes, "doc_id": doc_id})
        
        db.commit()
        print("Embeddings generated successfully")
        
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "search.db"
    generate_embeddings_for_existing_docs(db_path)