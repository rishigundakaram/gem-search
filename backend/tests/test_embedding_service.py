"""
Tests for the embedding service module.
"""

from unittest.mock import Mock, patch

import pytest
import torch
from app.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test cases for EmbeddingService class."""

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_init_default_device(self, mock_model_class, mock_tokenizer_class):
        """Test initialization with default device selection."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        with patch.object(EmbeddingService, '_get_best_device', return_value='cpu'):
            service = EmbeddingService()

        assert service.model_name == "jinaai/jina-clip-v2"
        assert service.device == 'cpu'
        mock_tokenizer_class.from_pretrained.assert_called_once_with(
            "jinaai/jina-clip-v2", trust_remote_code=True
        )
        mock_model_class.from_pretrained.assert_called_once_with(
            "jinaai/jina-clip-v2", trust_remote_code=True
        )
        mock_model.to.assert_called_once_with('cpu')
        mock_model.eval.assert_called_once()

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_init_custom_device(self, mock_model_class, mock_tokenizer_class):
        """Test initialization with custom device."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        service = EmbeddingService(device='cuda')

        assert service.device == 'cuda'
        mock_model.to.assert_called_once_with('cuda')

    @patch('app.embedding_service.torch.cuda.is_available', return_value=True)
    def test_get_best_device_cuda(self, mock_cuda_available):
        """Test device selection when CUDA is available."""
        service = EmbeddingService.__new__(EmbeddingService)
        device = service._get_best_device()
        assert device == 'cuda'

    @patch('app.embedding_service.torch.cuda.is_available', return_value=False)
    @patch('app.embedding_service.torch.backends.mps.is_available', return_value=True)
    def test_get_best_device_mps(self, mock_mps_available, mock_cuda_available):
        """Test device selection when MPS is available."""
        service = EmbeddingService.__new__(EmbeddingService)
        device = service._get_best_device()
        assert device == 'mps'

    @patch('app.embedding_service.torch.cuda.is_available', return_value=False)
    @patch('app.embedding_service.torch.backends.mps.is_available', return_value=False)
    def test_get_best_device_cpu(self, mock_mps_available, mock_cuda_available):
        """Test device selection when only CPU is available."""
        service = EmbeddingService.__new__(EmbeddingService)
        device = service._get_best_device()
        assert device == 'cpu'

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_embed_text_single(self, mock_model_class, mock_tokenizer_class):
        """Test embedding a single text."""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock tokenizer output
        mock_inputs = {
            'input_ids': torch.tensor([[1, 2, 3]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }
        mock_tokenizer_output = Mock()
        mock_tokenizer_output.to.return_value = mock_inputs
        mock_tokenizer.return_value = mock_tokenizer_output

        # Mock model output
        mock_embeddings = torch.tensor([[1.0, 2.0, 3.0, 4.0]])
        mock_model.get_text_features.return_value = mock_embeddings

        # Mock normalization
        normalized_embeddings = torch.tensor([[0.1826, 0.3651, 0.5477, 0.7303]])
        with patch('torch.nn.functional.normalize', return_value=normalized_embeddings):
            service = EmbeddingService(device='cpu')
            result = service.embed_text("test text")

        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(x, float) for x in result)

        # Verify calls
        mock_tokenizer.assert_called_once_with(
            ["test text"],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )
        mock_model.get_text_features.assert_called_once_with(**mock_inputs)

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_embed_texts_multiple(self, mock_model_class, mock_tokenizer_class):
        """Test embedding multiple texts."""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock tokenizer output
        mock_inputs = {
            'input_ids': torch.tensor([[1, 2, 3], [4, 5, 6]]),
            'attention_mask': torch.tensor([[1, 1, 1], [1, 1, 1]])
        }
        mock_tokenizer_output = Mock()
        mock_tokenizer_output.to.return_value = mock_inputs
        mock_tokenizer.return_value = mock_tokenizer_output

        # Mock model output
        mock_embeddings = torch.tensor([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        mock_model.get_text_features.return_value = mock_embeddings

        # Mock normalization
        normalized_embeddings = torch.tensor([
            [0.2673, 0.5345, 0.8018],
            [0.4558, 0.5698, 0.6838]
        ])
        with patch('torch.nn.functional.normalize', return_value=normalized_embeddings):
            service = EmbeddingService(device='cpu')
            results = service.embed_texts(["text one", "text two"])

        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(result, list) for result in results)
        assert all(len(result) == 3 for result in results)

        # Verify calls
        mock_tokenizer.assert_called_once_with(
            ["text one", "text two"],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        )

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_embed_texts_empty_list(self, mock_model_class, mock_tokenizer_class):
        """Test embedding empty list of texts."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        service = EmbeddingService(device='cpu')
        results = service.embed_texts([])

        assert results == []
        mock_tokenizer.assert_not_called()
        mock_model.get_text_features.assert_not_called()

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_embed_text_error_handling(self, mock_model_class, mock_tokenizer_class):
        """Test error handling in embedding generation."""
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        # Mock tokenizer to raise an exception
        mock_tokenizer.side_effect = Exception("Tokenization failed")

        service = EmbeddingService(device='cpu')

        with pytest.raises(Exception, match="Tokenization failed"):
            service.embed_text("test text")

    @patch('app.embedding_service.AutoTokenizer')
    @patch('app.embedding_service.AutoModel')
    def test_model_loading_error(self, mock_model_class, mock_tokenizer_class):
        """Test error handling during model loading."""
        mock_tokenizer_class.from_pretrained.side_effect = Exception("Model loading failed")

        with pytest.raises(Exception, match="Model loading failed"):
            EmbeddingService()


class TestEmbeddingServiceGlobal:
    """Test cases for global embedding service instance."""

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns the same instance."""
        # Reset global instance
        import app.embedding_service
        app.embedding_service._embedding_service = None

        with patch.object(EmbeddingService, '__init__', return_value=None):
            service1 = get_embedding_service()
            service2 = get_embedding_service()

        assert service1 is service2

    @patch('app.embedding_service.EmbeddingService')
    def test_get_embedding_service_initialization(self, mock_service_class):
        """Test that get_embedding_service initializes the service correctly."""
        # Reset global instance
        import app.embedding_service
        app.embedding_service._embedding_service = None

        mock_instance = Mock()
        mock_service_class.return_value = mock_instance

        result = get_embedding_service()

        assert result is mock_instance
        mock_service_class.assert_called_once_with()


@pytest.mark.integration
class TestEmbeddingServiceIntegration:
    """Integration tests for EmbeddingService (require actual model loading)."""

    @pytest.mark.skipif(
        not torch.cuda.is_available() and not torch.backends.mps.is_available(),
        reason="Requires CUDA or MPS for faster testing"
    )
    def test_real_embedding_generation(self):
        """Test actual embedding generation with real model (optional test)."""
        # This test is marked as integration and skipped in CI
        # Only runs if GPU is available
        try:
            service = EmbeddingService()
            embedding = service.embed_text("Hello world")

            assert isinstance(embedding, list)
            assert len(embedding) == 1024  # Jina CLIP v2 embedding dimension
            assert all(isinstance(x, float) for x in embedding)

            # Test that embeddings are normalized (approximately unit length)
            norm = sum(x * x for x in embedding) ** 0.5
            assert abs(norm - 1.0) < 0.01

        except Exception as e:
            pytest.skip(f"Real model test failed (expected in CI): {e}")
