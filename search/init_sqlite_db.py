#!/usr/bin/env python3
"""
Initialize the SQLite database using Alembic migrations
"""

import os
import sys
import subprocess
import logging
from sqlalchemy import text
from db.database import engine, get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('init_db')

def init_db():
    """Initialize the database using Alembic migrations"""
    logger.info("Running Alembic migrations...")
    
    # Get the current directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=current_dir,  # Set the working directory to where alembic.ini is
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Database schema successfully initialized")
        else:
            error_msg = f"Error running migrations: {result.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    except Exception as e:
        error_msg = f"Failed to run migrations: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Explicitly ensure FTS5 virtual table exists
    # This is handled separately since Alembic doesn't always handle virtual tables well
    try:
        # Get a database session
        session = next(get_db())
        
        # Create the FTS5 virtual table if it doesn't exist
        session.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        """))
        
        session.commit()
        logger.info("FTS5 virtual table is ready")
    except Exception as e:
        logger.error(f"Error initializing FTS5 table: {e}")
        raise
    
    logger.info("Database initialization complete")
    return True

if __name__ == "__main__":
    init_db()
    print("Database successfully initialized using Alembic migrations")
    print("You can now run the API server with: uvicorn main:app --reload")