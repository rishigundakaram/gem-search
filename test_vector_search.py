"""
Test script for vector search functionality.
"""
import requests
import json

API_KEY = "gem-search-dev-key-12345"
BASE_URL = "http://localhost:8000"

def test_vector_search():
    """Test the vector search endpoint."""
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    test_queries = [
        "machine learning algorithms",
        "web development frameworks", 
        "data analysis techniques",
        "artificial intelligence"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        data = {"query": query}
        
        try:
            response = requests.post(
                f"{BASE_URL}/vector-search",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results[:3], 1):
                    print(f"  {i}. {result['title']} (score: {result['score']:.4f})")
                    print(f"     URL: {result['url']}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the server. Make sure it's running on localhost:8000")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_vector_search()