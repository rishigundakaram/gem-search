"""
Database module for Gem Search.
Handles SQLite database setup and SQLAlchemy sessions.
Database schema is managed via migrations in /migrations/
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./search.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # Needed for SQLite

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database initialization is handled by migrations (yoyo apply)
# All schema changes should be done via migration files in /migrations/
