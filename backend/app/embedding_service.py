"""
Embedding service using Jina CLIP v2 model.
Provides text embedding functionality for search queries.
"""

import logging
import os

import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings using Jina CLIP v2 model."""

    def __init__(self, model_name: str = "jinaai/jina-clip-v2", device: str | None = None):
        """
        Initialize the embedding service.

        Args:
            model_name: HuggingFace model identifier for Jina CLIP v2
            device: Device to run the model on ('cpu', 'cuda', 'mps', or None for auto)
        """
        self.model_name = model_name
        self.device = device or self._get_best_device()
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _get_best_device(self) -> str:
        """Determine the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """Load the model and tokenizer."""
        try:
            logger.info(f"Loading Jina CLIP v2 model: {self.model_name}")
            # Use local_files_only=True if offline mode is set (for CI)
            offline_mode = os.getenv("HF_HUB_OFFLINE", "0") == "1"

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                local_files_only=offline_mode
            )
            self.model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                local_files_only=offline_mode
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Model loaded successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of float values representing the embedding vector
        """
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors, each as a list of floats
        """
        if not texts:
            return []

        try:
            with torch.no_grad():
                # Tokenize texts
                inputs = self.tokenizer(
                    texts,
                    padding=True,
                    truncation=True,
                    return_tensors="pt",
                    max_length=512
                ).to(self.device)

                # Generate embeddings
                outputs = self.model.get_text_features(**inputs)

                # Normalize embeddings (common practice for similarity search)
                embeddings = torch.nn.functional.normalize(outputs, p=2, dim=1)

                # Convert to list of lists
                return embeddings.cpu().numpy().tolist()

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

# Global instance (lazy initialization)
_embedding_service: EmbeddingService | None = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
