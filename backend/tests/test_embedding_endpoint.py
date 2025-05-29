"""
Tests for the embedding FastAPI endpoint.
"""

from unittest.mock import Mock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """Standard API headers for testing."""
    return {"X-API-Key": "gem-search-dev-key-12345"}


class TestEmbedEndpoint:
    """Test cases for the /embed endpoint."""

    @patch('app.main.get_embedding_service')
    def test_embed_text_success(self, mock_get_service, client, api_headers):
        """Test successful text embedding."""
        # Mock the embedding service
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1, 0.2, 0.3, 0.4]
        mock_get_service.return_value = mock_service

        # Make request
        response = client.post(
            "/embed",
            json={"text": "Hello world"},
            headers=api_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert data["embedding"] == [0.1, 0.2, 0.3, 0.4]

        # Verify service was called correctly
        mock_service.embed_text.assert_called_once_with("Hello world")

    @patch('app.main.get_embedding_service')
    def test_embed_text_strips_whitespace(self, mock_get_service, client, api_headers):
        """Test that text is stripped of whitespace."""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1, 0.2]
        mock_get_service.return_value = mock_service

        response = client.post(
            "/embed",
            json={"text": "  hello world  "},
            headers=api_headers
        )

        assert response.status_code == 200
        mock_service.embed_text.assert_called_once_with("hello world")

    def test_embed_text_empty_string(self, client, api_headers):
        """Test embedding empty string returns 400."""
        response = client.post(
            "/embed",
            json={"text": ""},
            headers=api_headers
        )

        assert response.status_code == 400
        assert "Text cannot be empty" in response.json()["detail"]

    def test_embed_text_whitespace_only(self, client, api_headers):
        """Test embedding whitespace-only string returns 400."""
        response = client.post(
            "/embed",
            json={"text": "   "},
            headers=api_headers
        )

        assert response.status_code == 400
        assert "Text cannot be empty" in response.json()["detail"]

    def test_embed_text_missing_api_key(self, client):
        """Test embedding without API key returns 422."""
        response = client.post(
            "/embed",
            json={"text": "Hello world"}
        )

        assert response.status_code == 422

    def test_embed_text_invalid_api_key(self, client):
        """Test embedding with invalid API key returns 401."""
        response = client.post(
            "/embed",
            json={"text": "Hello world"},
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_embed_text_missing_text_field(self, client, api_headers):
        """Test embedding without text field returns 422."""
        response = client.post(
            "/embed",
            json={},
            headers=api_headers
        )

        assert response.status_code == 422

    def test_embed_text_invalid_json(self, client, api_headers):
        """Test embedding with invalid JSON returns 422."""
        response = client.post(
            "/embed",
            data="invalid json",
            headers={**api_headers, "Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @patch('app.main.get_embedding_service')
    def test_embed_text_service_error(self, mock_get_service, client, api_headers):
        """Test handling of embedding service errors."""
        # Mock the embedding service to raise an exception
        mock_service = Mock()
        mock_service.embed_text.side_effect = Exception("Model failed")
        mock_get_service.return_value = mock_service

        response = client.post(
            "/embed",
            json={"text": "Hello world"},
            headers=api_headers
        )

        assert response.status_code == 500
        assert "Embedding error" in response.json()["detail"]

    @patch('app.main.get_embedding_service')
    def test_embed_text_large_input(self, mock_get_service, client, api_headers):
        """Test embedding with large text input."""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1] * 1024  # Typical embedding size
        mock_get_service.return_value = mock_service

        # Create a large text input
        large_text = "word " * 1000  # 5000 characters

        response = client.post(
            "/embed",
            json={"text": large_text},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["embedding"]) == 1024
        mock_service.embed_text.assert_called_once_with(large_text.strip())

    @patch('app.main.get_embedding_service')
    def test_embed_text_special_characters(self, mock_get_service, client, api_headers):
        """Test embedding with special characters."""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1, 0.2]
        mock_get_service.return_value = mock_service

        special_text = "Hello! @#$%^&*()_+-=[]{}|;:'\",.<>?/~`"

        response = client.post(
            "/embed",
            json={"text": special_text},
            headers=api_headers
        )

        assert response.status_code == 200
        mock_service.embed_text.assert_called_once_with(special_text)

    @patch('app.main.get_embedding_service')
    def test_embed_text_unicode_characters(self, mock_get_service, client, api_headers):
        """Test embedding with Unicode characters."""
        mock_service = Mock()
        mock_service.embed_text.return_value = [0.1, 0.2]
        mock_get_service.return_value = mock_service

        unicode_text = "Hello 世界 🌍 café naïve résumé"

        response = client.post(
            "/embed",
            json={"text": unicode_text},
            headers=api_headers
        )

        assert response.status_code == 200
        mock_service.embed_text.assert_called_once_with(unicode_text)

    @patch('app.main.get_embedding_service')
    def test_embed_response_format(self, mock_get_service, client, api_headers):
        """Test that response format matches EmbedResponse model."""
        mock_service = Mock()
        test_embedding = [0.1, -0.2, 0.3, -0.4, 0.0]
        mock_service.embed_text.return_value = test_embedding
        mock_get_service.return_value = mock_service

        response = client.post(
            "/embed",
            json={"text": "test"},
            headers=api_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert isinstance(data, dict)
        assert "embedding" in data
        assert isinstance(data["embedding"], list)
        assert all(isinstance(x, int | float) for x in data["embedding"])
        assert data["embedding"] == test_embedding
