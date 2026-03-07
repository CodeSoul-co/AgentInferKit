from typing import List, Optional

import numpy as np
from loguru import logger

from src.config import settings

# Lazy-loaded model instance
_model = None
_model_name = None


def _load_model(model_name: Optional[str] = None) -> None:
    """Load the sentence-transformers embedding model (lazy singleton)."""
    global _model, _model_name
    target = model_name or settings.embedding_model
    if _model is not None and _model_name == target:
        return
    logger.info(f"Loading embedding model: {target}")
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer(target)
    _model_name = target
    logger.info(f"Embedding model loaded: {target}, dim={_model.get_sentence_embedding_dimension()}")


def embed(texts: List[str], model_name: Optional[str] = None) -> np.ndarray:
    """Embed a list of texts into dense vectors.

    Args:
        texts: List of text strings to embed.
        model_name: Optional override for the embedding model name.

    Returns:
        A numpy array of shape (len(texts), dim).
    """
    _load_model(model_name)
    embeddings = _model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.array(embeddings)


def get_embedding_dim(model_name: Optional[str] = None) -> int:
    """Return the embedding dimension of the loaded model."""
    _load_model(model_name)
    return _model.get_sentence_embedding_dimension()
