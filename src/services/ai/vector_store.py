"""pgvector search and storage using the existing Embedding ORM model."""

import logging
import uuid as uuid_mod

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from src.services.db.connection import get_db
from src.services.db.models import Embedding
from src.services.ai.embeddings import embed_text, embed_texts

logger = logging.getLogger(__name__)


def search_similar(
    workspace_id: str,
    query: str,
    k: int = 3,
) -> list[str]:
    """Search for the top-k most similar embeddings by cosine distance.

    Args:
        workspace_id: UUID string of the workspace.
        query: The question text to search for.
        k: Number of results to return.

    Returns:
        List of content strings from the most similar embeddings.
    """
    query_embedding = embed_text(query)

    with get_db() as db:
        # Use pgvector's <=> (cosine distance) operator via raw SQL
        # for optimal performance with the ivfflat index.
        results = db.execute(
            sa_text("""
                SELECT content
                FROM embeddings
                WHERE workspace_id = :ws_id
                ORDER BY embedding <=> :query_vec
                LIMIT :k
            """),
            {
                "ws_id": uuid_mod.UUID(workspace_id),
                "query_vec": str(query_embedding),
                "k": k,
            },
        ).fetchall()

    return [row[0] for row in results]


def store_embeddings(
    workspace_id: str,
    chunks: list[dict],
) -> int:
    """Embed and store message chunks into the embeddings table.

    Args:
        workspace_id: UUID string of the workspace.
        chunks: List of dicts with keys: "content", "channel_id", "message_ts",
                and optionally "thread_ts".

    Returns:
        Number of embeddings stored.
    """
    if not chunks:
        return 0

    texts = [c["content"] for c in chunks]
    vectors = embed_texts(texts)

    ws_uuid = uuid_mod.UUID(workspace_id)
    stored = 0

    with get_db() as db:
        for chunk, vector in zip(chunks, vectors):
            record = Embedding(
                workspace_id=ws_uuid,
                content=chunk["content"],
                embedding=vector,
                channel_id=chunk.get("channel_id"),
                message_ts=chunk.get("message_ts"),
                thread_ts=chunk.get("thread_ts"),
            )
            db.add(record)
            stored += 1
        db.flush()

    logger.info("Stored %d embeddings for workspace %s", stored, workspace_id)
    return stored
