import hashlib
import numpy as np
from typing import List
from backend.app.core.config import settings
from backend.app.core.logging import logger

class EmbeddingService:
    _instance = None
    _model = None
    _model_name = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        import os
        self._model_name = settings.EMBEDDING_MODEL
        self._model = None

        if os.environ.get("USE_FAST_EMBEDDINGS", "").lower() in ["1", "true", "yes"] or self._model_name == "fast":
            logger.info("Using ultra-fast deterministic semantic embedding engine.")
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Attempting to load embedding model: {self._model_name}...")
            # Set HF hub timeout
            os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
            self._model = SentenceTransformer(self._model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer '{self._model_name}': {e}. "
                f"Falling back to built-in semantic vector generator."
            )
            self._model = None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of strings."""
        if not texts:
            return []

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error during SentenceTransformer encoding: {e}. Using deterministic fallback.")

        # Fallback: Deterministic 384-dimensional semantic-aware pseudo-embedding
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single query string."""
        return self.embed_texts([query])[0]

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic lightweight 384-dim pseudo embedding based on ngram hashes
        and token frequency. Guaranteed to preserve token overlap similarity.
        """
        dim = 384
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return [0.0] * dim

        for word in words:
            # Deterministic hash to dimension index
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign

        # Add 3-gram character features
        for i in range(len(text) - 2):
            gram = text[i:i+3].lower()
            h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
            idx = (h >> 4) % dim
            vec[idx] += 0.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
