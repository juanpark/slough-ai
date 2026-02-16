"""OpenAI embedding helpers — lazy-loaded singleton."""

import logging
from typing import Optional

from langchain_openai import OpenAIEmbeddings

from src.config import settings

logger = logging.getLogger(__name__)

_embeddings: Optional[OpenAIEmbeddings] = None


def get_embeddings() -> OpenAIEmbeddings:
    """Return a singleton ``OpenAIEmbeddings`` instance (text-embedding-3-small)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )
    return _embeddings


def embed_text(text: str) -> list[float]:
    """Embed a single text string and return the 1536-dim vector."""
    return get_embeddings().embed_query(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in a single API call (batched)."""
    return get_embeddings().embed_documents(texts)
