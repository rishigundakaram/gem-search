from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///search.db')

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_fts5(db):
    """Initialize FTS5 virtual table - must be done with raw SQL"""
    # This needs to be executed outside of migrations since Alembic doesn't handle virtual tables well
    db.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
        content,
        document_id UNINDEXED,
        tokenize='porter unicode61'
    )
    ''')
    db.commit()