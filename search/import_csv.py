import sqlite3
import pandas as pd
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.models import Source, Link, Document

# Paths
CSV_PATH = 'scrapers/output.csv'
DB_PATH = 'search.db'

def import_csv():
    """Import data from the CSV file into SQLite."""
    # Check if CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"CSV file {CSV_PATH} not found!")
        return False
    
    # Create engine and session
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Load CSV data
        df = pd.read_csv(CSV_PATH)
        print(f"Found {len(df)} entries in CSV file")
        
        # Process each row
        imported_count = 0
        for _, row in df.iterrows():
            # Check if URL already exists in links table
            exists = session.query(Link).filter_by(url=row['url']).first()
            if exists:
                print(f"Skipping existing URL: {row['url']}")
                continue
            
            # Create new link
            link = Link(
                url=row['url'],
                status='processed',
                discovered_at=datetime.utcnow(),
                last_processed_at=datetime.utcnow(),
                is_deleted=False
            )
            session.add(link)
            session.flush()  # Generate ID for the link
            
            # Create document
            document = Document(
                link_id=link.id,
                title=row['title'],
                content=row['extracted text'],
                processed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(document)
            session.flush()  # Generate ID for the document
            
            # Insert into FTS table
            # Since we can't use SQLAlchemy ORM for virtual tables, use raw SQL
            session.execute(text(
                "INSERT INTO document_content (document_id, content) VALUES (:doc_id, :content)"
            ), {
                "doc_id": document.id,
                "content": row['extracted text']
            })
            
            imported_count += 1
        
        session.commit()
        print(f"Successfully imported {imported_count} documents")
        return True
    
    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    import_csv()