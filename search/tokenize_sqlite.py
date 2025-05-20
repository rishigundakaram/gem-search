import sqlite3
import nltk
import pickle
from rank_bm25 import BM25Okapi

def tokenize_documents(db_path, index_path):
    # Download NLTK data if needed
    nltk.download('punkt')
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all documents
    cursor.execute("SELECT id, content FROM documents")
    documents = cursor.fetchall()
    
    # Extract document IDs and content
    doc_ids = [doc[0] for doc in documents]
    contents = [doc[1] for doc in documents]
    
    # Tokenize the documents
    tokenized_documents = [nltk.word_tokenize(doc.lower()) for doc in contents]
    
    # Create BM25 index
    bm25 = BM25Okapi(tokenized_documents)
    
    # Save the index and document IDs
    with open(index_path, 'wb') as f:
        pickle.dump({
            'tokenized_documents': tokenized_documents,
            'doc_ids': doc_ids
        }, f)
    
    conn.close()
    print(f"Tokenized {len(documents)} documents and saved index to {index_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Tokenize documents and create search index.')
    parser.add_argument('db_path', type=str, help='The SQLite database file path.')
    parser.add_argument('--index_path', type=str, default='bm25_index.pkl',
                        help='Path to save the tokenized index.')
    args = parser.parse_args()
    
    tokenize_documents(args.db_path, args.index_path)