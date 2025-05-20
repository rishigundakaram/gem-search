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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content TEXT
    )
    ''')
    
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
        cursor.execute(
            "INSERT OR IGNORE INTO documents (url, title, content) VALUES (?, ?, ?)",
            (row['url'], row['title'], row['extracted text'])
        )
    
    conn.commit()
    print(f"Imported {cursor.rowcount} documents into the SQLite database")
    
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")