import sqlite3
import pandas as pd
import os

# Paths
CSV_PATH = 'scrapers/output.csv'
DB_PATH = 'search.db'

def init_db():
    # Create database schema
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create regular documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT
    )
    ''')
    
    # Try to create FTS5 virtual table
    try:
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        ''')
        print("FTS5 extension is enabled")
        has_fts = True
    except sqlite3.Error as e:
        print(f"FTS5 extension not available: {e}")
        print("Falling back to standard tables")
        has_fts = False
    
    conn.commit()
    
    # Check if CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"CSV file {CSV_PATH} not found!")
        conn.close()
        return
    
    # Load CSV data
    df = pd.read_csv(CSV_PATH)
    
    # Insert data into SQLite
    for _, row in df.iterrows():
        # Insert into documents table
        cursor.execute(
            "INSERT OR IGNORE INTO documents (url, title, content) VALUES (?, ?, ?)",
            (row['url'], row['title'], row['extracted text'])
        )
        
        # If FTS5 is available, also insert into FTS table
        if has_fts:
            document_id = cursor.lastrowid
            if not document_id:  # If document already existed
                cursor.execute("SELECT id FROM documents WHERE url = ?", (row['url'],))
                document_id = cursor.fetchone()[0]
                
            cursor.execute(
                "INSERT OR REPLACE INTO document_content (document_id, content) VALUES (?, ?)",
                (document_id, row['extracted text'])
            )
    
    conn.commit()
    print(f"Imported {cursor.rowcount} documents into the SQLite database")
    
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")