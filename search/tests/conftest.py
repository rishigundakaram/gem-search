"""Fixtures for tests."""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.models import Base
from crawler import utils, discovery, classifier, extractor, db

# Setup in-memory SQLite for tests
@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    
    # Create FTS5 virtual table
    with engine.connect() as conn:
        conn.execute("""
        CREATE VIRTUAL TABLE document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        """)
    
    return engine

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a new database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.rollback()
        db_session.close()

@pytest.fixture
def db_handler(test_db_session):
    """Create a DatabaseHandler with a test session."""
    handler = db.DatabaseHandler()
    # Override get_session to return the test session
    handler.get_session = lambda: test_db_session
    return handler

@pytest.fixture
def test_html_article():
    """Return test HTML for an article."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article Title</title>
        <meta property="og:image" content="https://example.com/image.jpg">
    </head>
    <body>
        <article>
            <h1>Test Article Heading</h1>
            <div class="author">John Doe</div>
            <div class="date">2023-05-20</div>
            <p>This is the first paragraph of test content.</p>
            <p>This is the second paragraph with more detailed information.</p>
            <p>This is the third paragraph concluding the article.</p>
        </article>
    </body>
    </html>
    """

@pytest.fixture
def test_html_non_article():
    """Return test HTML for a non-article page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>About Us</title>
    </head>
    <body>
        <div class="header">
            <h1>About Our Company</h1>
        </div>
        <div class="content">
            <p>We are a company that does things.</p>
            <p>Contact us at contact@example.com</p>
        </div>
    </body>
    </html>
    """

@pytest.fixture
def test_urls():
    """Return a dict of test URLs for different purposes."""
    return {
        "article": "https://blog.example.com/2023/05/20/test-article",
        "blog_home": "https://blog.example.com",
        "about_page": "https://blog.example.com/about",
        "article_with_date": "https://example.com/blog/2023-05-20-test-article",
        "article_with_path": "https://example.com/blog/posts/test-article",
    }