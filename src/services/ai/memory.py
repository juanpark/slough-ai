"""Conversation memory — hybrid 3-layer approach.

Layer 1: AsyncPostgresSaver  — persists full LangGraph state per thread
Layer 2: Summary Memory      — compresses old messages via GPT-4o-mini
Layer 3: Sliding Window       — keeps the most recent N Q&A pairs verbatim

The ``trim_and_summarize`` function is the core entry point, called inside
the ``generate`` node to ensure the LLM always receives a bounded number
of tokens regardless of conversation length.
"""

import logging
from contextlib import asynccontextmanager

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from src.config import settings

logger = logging.getLogger(__name__)

# ── Layer 1: AsyncPostgresSaver (checkpoint persistence) ──────────────

_POOL_MAX_SIZE = 5  # Kept small — checkpointing is low-concurrency


@asynccontextmanager
async def get_checkpointer():
    """Yield an ``AsyncPostgresSaver`` backed by an async connection pool.

    Imports psycopg_pool and langgraph lazily to avoid import-time hangs
    when the database is not available.

    Usage::

        async with get_checkpointer() as checkpointer:
            graph = get_compiled_graph(checkpointer=checkpointer)
            result = await graph.ainvoke(inputs, config=config)
    """
    # Lazy imports — avoid module-level import of psycopg/pool
    try:
        from psycopg_pool import AsyncConnectionPool
    except ImportError as exc:
        raise ImportError(
            "psycopg_pool 패키지를 찾을 수 없습니다. "
            "'pip install psycopg-pool>=3.2.0'을 실행하세요. "
            "진단: python scripts/check_psycopg.py"
        ) from exc

    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    except ImportError as exc:
        raise ImportError(
            "langgraph-checkpoint-postgres 패키지를 찾을 수 없습니다. "
            "'pip install langgraph-checkpoint-postgres>=2.0.0'을 실행하세요."
        ) from exc

    async with AsyncConnectionPool(
        conninfo=settings.postgres_dsn,
        max_size=_POOL_MAX_SIZE,
        kwargs={"autocommit": True},
    ) as pool:
        saver = AsyncPostgresSaver(pool)
        await saver.setup()
        yield saver


# ── Layer 2: Summary Memory (compress old messages) ───────────────────

_SUMMARY_PREFIX = "[이전 대화 요약] "

# Lazy-loaded mini model for cheap summarization
_mini_llm: ChatOpenAI | None = None


def _get_mini_llm() -> ChatOpenAI:
    global _mini_llm
    if _mini_llm is None:
        _mini_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            api_key=settings.openai_api_key,
        )
    return _mini_llm


async def _summarize_messages(messages: list[BaseMessage]) -> str:
    """Summarize a list of messages into a concise Korean paragraph."""
    if not messages:
        return ""

    conversation = "\n".join(
        f"{'Q' if isinstance(m, HumanMessage) else 'A'}: {_truncate(m.content, 300)}"
        for m in messages
        if isinstance(m, (HumanMessage, AIMessage))
    )

    prompt = (
        "아래 대화 기록을 한국어 3줄 이내로 요약하세요. "
        "핵심 질문과 결론만 간결하게 포함하세요.\n\n"
        f"{conversation}"
    )

    try:
        response = await _get_mini_llm().ainvoke([{"role": "user", "content": prompt}])
        return response.content.strip()
    except Exception:
        logger.exception("Summary generation failed, dropping old context")
        return ""


# ── Layer 3: Sliding Window (keep recent pairs) ──────────────────────

def _truncate(text: str, max_len: int = 500) -> str:
    """Truncate text with ellipsis if it exceeds max_len."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _extract_existing_summary(messages: list[BaseMessage]) -> tuple[str, list[BaseMessage]]:
    """Separate any existing summary SystemMessage from the rest."""
    if messages and isinstance(messages[0], SystemMessage):
        content = messages[0].content
        if content.startswith(_SUMMARY_PREFIX):
            return content[len(_SUMMARY_PREFIX):], messages[1:]
    return "", messages


def _split_recent_and_old(
    messages: list[BaseMessage],
    max_recent_pairs: int = 2,
) -> tuple[list[BaseMessage], list[BaseMessage]]:
    """Split messages into old and recent, keeping max_recent_pairs Q&A pairs.

    Scans backwards to find the N-th HumanMessage from the end, then splits
    at that position. Everything before is "old", everything from there is "recent".
    """
    # Collect indices of all HumanMessages
    human_indices = [
        i for i, m in enumerate(messages) if isinstance(m, HumanMessage)
    ]

    if len(human_indices) <= max_recent_pairs:
        return [], messages

    # The split point is at the (max_recent_pairs)-th HumanMessage from the end
    split_idx = human_indices[-max_recent_pairs]
    return messages[:split_idx], messages[split_idx:]


# ── Entry point ──────────────────────────────────────────────────────

async def trim_and_summarize(
    messages: list[BaseMessage],
    max_recent_pairs: int = 2,
) -> list[BaseMessage]:
    """Compress conversation history for token-efficient LLM input.

    Returns:
        A trimmed message list: [summary SystemMessage?] + [recent messages]

    Token budget (approximate):
        - Summary: ~100-200 tokens (fixed, regardless of history length)
        - Recent 2 Q&A pairs: ~200-300 tokens
        - Total: ~300-500 tokens (bounded)
    """
    # Filter to only conversation messages (Human + AI)
    conv_messages = [
        m for m in messages
        if isinstance(m, (HumanMessage, AIMessage, SystemMessage))
    ]

    if not conv_messages:
        return messages

    # Separate existing summary from messages
    existing_summary, conv_messages = _extract_existing_summary(conv_messages)

    # Count actual Q&A pairs
    human_count = sum(1 for m in conv_messages if isinstance(m, HumanMessage))

    # If within window, no trimming needed
    if human_count <= max_recent_pairs:
        result = []
        if existing_summary:
            result.append(SystemMessage(content=f"{_SUMMARY_PREFIX}{existing_summary}"))
        result.extend(conv_messages)
        return result

    # Split into old and recent
    old_messages, recent_messages = _split_recent_and_old(
        conv_messages, max_recent_pairs
    )

    # Build text to summarize: existing summary + old messages
    to_summarize: list[BaseMessage] = []
    if existing_summary:
        to_summarize.append(AIMessage(content=f"이전 요약: {existing_summary}"))
    to_summarize.extend(old_messages)

    new_summary = await _summarize_messages(to_summarize)

    result: list[BaseMessage] = []
    if new_summary:
        result.append(SystemMessage(content=f"{_SUMMARY_PREFIX}{new_summary}"))
    result.extend(recent_messages)

    logger.info(
        "Memory trimmed: %d messages → summary + %d recent",
        len(messages),
        len(recent_messages),
    )
    return result
