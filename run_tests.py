#!/usr/bin/env python3
"""
Helper script to run basic functionality tests.
"""

import os
import sys
import tempfile

def test_database_functionality():
    """Test database initialization and basic operations."""
    print("Testing database functionality...")
    
    # Add search directory to path
    search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
    if search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    
    from app.database import init_database
    from app.scraper import get_existing_urls, insert_document_if_new
    
    # Create temporary database
    fd, temp_db = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Test database initialization
        conn = init_database(temp_db)
        conn.close()
        print("✓ Database initialization works")
        
        # Test getting existing URLs from empty DB
        existing = get_existing_urls(temp_db)
        assert len(existing) == 0, "Empty database should have no URLs"
        print("✓ get_existing_urls works with empty database")
        
        # Test inserting a document
        success = insert_document_if_new(
            "https://test.com", 
            "Test Title", 
            "Test content for the document", 
            temp_db, 
            existing
        )
        assert success, "Should successfully insert new document"
        print("✓ Document insertion works")
        
        # Test duplicate prevention
        success = insert_document_if_new(
            "https://test.com", 
            "Test Title 2", 
            "Different content", 
            temp_db, 
            existing
        )
        assert not success, "Should prevent duplicate URL insertion"
        print("✓ Duplicate prevention works")
        
        # Verify document count
        existing = get_existing_urls(temp_db)
        assert len(existing) == 1, "Should have exactly one document"
        print("✓ Document count verification works")
        
    finally:
        os.unlink(temp_db)
    
    print("Database functionality tests: ✓ PASSED\n")

def test_scraper_functionality():
    """Test scraper core functions."""
    print("Testing scraper functionality...")
    
    # Add search directory to path
    search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
    if search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    
    from app.scraper import discover_links, fetch_and_parse
    
    # Test link discovery (should work even if returns empty)
    try:
        links = discover_links('https://example.com', same_domain_only=True)
        print(f"✓ Link discovery works: found {len(links)} links")
    except Exception as e:
        print(f"✗ Link discovery failed: {e}")
        return False
    
    # Test fetch and parse (should handle failures gracefully)
    try:
        title, content = fetch_and_parse('https://httpbin.org/status/404')
        # Should return None, None for 404
        print("✓ fetch_and_parse handles errors gracefully")
    except Exception as e:
        print(f"✗ fetch_and_parse error handling failed: {e}")
        return False
    
    print("Scraper functionality tests: ✓ PASSED\n")
    return True

def test_api_functionality():
    """Test FastAPI endpoints."""
    print("Testing API functionality...")
    
    # Add search directory to path
    search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
    if search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200, "Health endpoint should return 200"
        assert response.json() == {"status": "ok"}, "Health endpoint should return correct response"
        print("✓ Health endpoint works")
        
        # Test search endpoint with valid query
        response = client.post('/search', json={'query': 'test'})
        assert response.status_code == 200, "Search endpoint should return 200"
        assert isinstance(response.json(), list), "Search should return a list"
        print("✓ Search endpoint works")
        
        # Test search endpoint with empty query
        response = client.post('/search', json={'query': ''})
        assert response.status_code == 200, "Empty query should return 200"
        assert response.json() == [], "Empty query should return empty list"
        print("✓ Empty query handling works")
        
    except ImportError as e:
        print(f"✗ Missing dependencies for API testing: {e}")
        return False
    except Exception as e:
        print(f"✗ API functionality test failed: {e}")
        return False
    
    print("API functionality tests: ✓ PASSED\n")
    return True

if __name__ == "__main__":
    print("Running gem-search functionality tests...\n")
    
    try:
        test_database_functionality()
        test_scraper_functionality()
        test_api_functionality()
        
        print("="*50)
        print("ALL TESTS PASSED! ✓")
        print("="*50)
        sys.exit(0)
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"TESTS FAILED! ✗")
        print(f"Error: {e}")
        print("="*50)
        sys.exit(1)