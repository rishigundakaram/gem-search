#!/usr/bin/env python3
"""
Test the API endpoints using requests.
"""
import os
import subprocess
import sys
import time

import requests

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, backend_dir)


def start_server():
    """Start the FastAPI server in the background."""
    os.chdir(backend_dir)
    return subprocess.Popen(
        [
            "python",
            "-c",
            "from app.main import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8003)",
        ]
    )


def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://127.0.0.1:8003"

    # Start server
    print("Starting server...")
    server_process = start_server()

    try:
        # Wait for server to start
        time.sleep(3)

        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
            return False

        # Test search endpoint with empty query
        print("Testing search endpoint with empty query...")
        response = requests.post(
            f"{base_url}/search",
            json={"query": ""},
            headers={"X-API-Key": "gem-search-dev-key-12345"},
            timeout=5,
        )
        if response.status_code == 200:
            print("✓ Search endpoint working (empty query)")
        else:
            print(f"✗ Search endpoint failed: {response.status_code}")
            return False

        # Test search endpoint with query
        print("Testing search endpoint with test query...")
        response = requests.post(
            f"{base_url}/search",
            json={"query": "test"},
            headers={"X-API-Key": "gem-search-dev-key-12345"},
            timeout=5,
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✓ Search endpoint working (found {len(results)} results)")
        else:
            print(f"✗ Search endpoint failed: {response.status_code}")
            return False

        # Test authentication failure
        print("Testing authentication failure...")
        response = requests.post(
            f"{base_url}/search",
            json={"query": "test"},
            headers={"X-API-Key": "invalid-key"},
            timeout=5,
        )
        if response.status_code == 401:
            print("✓ Authentication rejection working")
        else:
            print(f"✗ Authentication should fail but got: {response.status_code}")
            return False

        # Test embedding endpoint - only basic availability, not functionality
        # (skip actual embedding to avoid model downloads in CI)
        print("Testing embedding endpoint availability...")
        response = requests.post(
            f"{base_url}/embed",
            json={"text": "test"},
            headers={"X-API-Key": "gem-search-dev-key-12345"},
            timeout=10,
        )
        # Expect 500 (model not available) or 200 (if model loads), but not 404/401
        if response.status_code in [200, 500]:
            print("✓ Embedding endpoint available (model may not load in CI)")
        else:
            print(f"✗ Embedding endpoint unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        return True

    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to server")
        return False
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False
    finally:
        # Kill server
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
