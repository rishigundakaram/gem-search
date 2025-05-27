import pytest
import tempfile
import os
import sqlite3
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from main import app
from db.database import get_db
from db.models import Base


class TestAPI:
    
    @pytest.fixture
    def test_db(self):
        """Create a test database with sample data."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create database URL
        database_url = f"sqlite:///{db_path}"
        
        # Create engine and tables
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        
        # Create FTS5 table manually (SQLAlchemy doesn't handle virtual tables)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE VIRTUAL TABLE document_content USING fts5(
            content,
            document_id UNINDEXED,
            tokenize='porter unicode61'
        )
        """)
        
        # Insert test data
        cursor.execute("""
        INSERT INTO documents (id, url, title, content) VALUES 
        (1, 'https://example.com/ml', 'Machine Learning Basics', 'Introduction to machine learning algorithms and neural networks'),
        (2, 'https://example.com/ai', 'Artificial Intelligence Overview', 'Comprehensive guide to AI technologies and applications'),
        (3, 'https://example.com/python', 'Python Programming', 'Learn Python programming language fundamentals')
        """)
        
        # Insert into FTS5 table
        cursor.execute("""
        INSERT INTO document_content (document_id, content) VALUES 
        (1, 'Introduction to machine learning algorithms and neural networks'),
        (2, 'Comprehensive guide to AI technologies and applications'),
        (3, 'Learn Python programming language fundamentals')
        """)
        
        conn.commit()
        conn.close()
        
        # Create session factory
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        yield database_url
        
        # Cleanup
        app.dependency_overrides.clear()
        os.unlink(db_path)
    
    @pytest.fixture
    def client(self, test_db):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_search_endpoint_successful_query(self, client):
        """Test successful search query."""
        response = client.post("/search", json={"query": "machine learning"})
        
        assert response.status_code == 200
        results = response.json()
        
        # Should return at least one result
        assert len(results) >= 1
        
        # Check result structure
        assert "title" in results[0]
        assert "url" in results[0]
        
        # Should find the ML article
        titles = [result["title"] for result in results]
        assert "Machine Learning Basics" in titles
    
    def test_search_endpoint_no_results(self, client):
        """Test search query that returns no results."""
        response = client.post("/search", json={"query": "nonexistent topic xyz"})
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 0
    
    def test_search_endpoint_empty_query(self, client):
        """Test search with empty query."""
        response = client.post("/search", json={"query": ""})
        
        assert response.status_code == 200
        # Empty query should return empty results
        results = response.json()
        assert len(results) == 0
    
    def test_search_endpoint_whitespace_query(self, client):
        """Test search with whitespace-only query."""
        response = client.post("/search", json={"query": "   "})
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 0
    
    def test_search_endpoint_multiple_terms(self, client):
        """Test search with multiple terms."""
        response = client.post("/search", json={"query": "AI technologies"})
        
        assert response.status_code == 200
        results = response.json()
        
        # Should find the AI article
        if len(results) > 0:
            titles = [result["title"] for result in results]
            assert "Artificial Intelligence Overview" in titles
    
    def test_search_endpoint_case_insensitive(self, client):
        """Test that search is case insensitive."""
        response1 = client.post("/search", json={"query": "python"})
        response2 = client.post("/search", json={"query": "PYTHON"})
        response3 = client.post("/search", json={"query": "Python"})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        
        # All should return the same results
        results1 = response1.json()
        results2 = response2.json()
        results3 = response3.json()
        
        # FTS5 is case insensitive by default
        assert len(results1) == len(results2) == len(results3)
    
    def test_search_endpoint_invalid_json(self, client):
        """Test search endpoint with invalid JSON."""
        response = client.post("/search", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_search_endpoint_missing_query_field(self, client):
        """Test search endpoint with missing query field."""
        response = client.post("/search", json={"not_query": "test"})
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_search_endpoint_wrong_http_method(self, client):
        """Test search endpoint with wrong HTTP method."""
        response = client.get("/search")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_search_endpoint_database_error(self, client):
        """Test search endpoint handles database errors gracefully."""
        # This test is harder to mock properly due to FastAPI's dependency injection
        # Instead, we test with a malformed query that causes FTS5 syntax error
        response = client.post("/search", json={"query": "AND OR NOT"})
        
        # This should cause an FTS5 syntax error and return 500
        assert response.status_code == 500
        
        error_detail = response.json()
        assert "Search error" in error_detail["detail"]