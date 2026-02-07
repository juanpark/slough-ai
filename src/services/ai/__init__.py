"""
AI Service Interface Contract
=============================
This is the boundary between Slack-side (Juan) and AI-side (Teammate).
Juan calls these functions; Teammate implements them.

Vector DB: pgvector (PostgreSQL extension) — NOT Pinecone.
Embeddings are stored in the 'embeddings' table via pgvector.
See src/services/db/models.py for the Embedding model.

Current: STUB implementations for development.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AnswerResult:
    answer: str
    is_high_risk: bool
    is_prohibited: bool
    sources_used: int


@dataclass
class IngestResult:
    chunks_created: int
    embeddings_stored: int


async def generate_answer(
    question: str,
    workspace_id: str,
    asker_id: str,
    rules: list[dict],
) -> AnswerResult:
    """
    Generate an answer to an employee's question using RAG + persona.

    Args:
        question: The employee's question text
        workspace_id: UUID of the workspace
        asker_id: Slack user ID of the asker
        rules: Active rules for this workspace [{"id": int, "rule_text": str}]

    Returns:
        AnswerResult with answer text (Korean), risk flags, and source count.
    """
    # STUB
    return AnswerResult(
        answer=f'[STUB] 이 질문에 대한 의사결정자의 응답입니다: "{question}"',
        is_high_risk=False,
        is_prohibited=False,
        sources_used=0,
    )


async def ingest_messages(
    workspace_id: str,
    messages: list[dict],
) -> IngestResult:
    """
    Ingest and embed an array of decision-maker messages.

    Args:
        workspace_id: UUID of the workspace
        messages: List of {"text": str, "channel": str, "ts": str, "thread_ts"?: str}

    Returns:
        IngestResult with chunk and embedding counts.
    """
    # STUB
    print(f"[STUB] Would ingest {len(messages)} messages for workspace {workspace_id}")
    return IngestResult(chunks_created=0, embeddings_stored=0)


async def process_feedback(
    workspace_id: str,
    question_id: str,
    feedback_type: str,
    corrected_answer: Optional[str] = None,
) -> None:
    """
    Store feedback and update learning data.

    Args:
        workspace_id: UUID of the workspace
        question_id: UUID from qa_history
        feedback_type: One of 'approved', 'rejected', 'corrected', 'caution'
        corrected_answer: Only for 'corrected' type
    """
    # STUB
    print(f"[STUB] Feedback {feedback_type} for question {question_id}")
