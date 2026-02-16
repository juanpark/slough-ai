"""LangGraph agent state definition for the RAG pipeline."""

import contextvars
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Streaming callback — set by generate_answer_streaming(), read by generate node.
# When set, the generate node streams tokens via this callback instead of
# waiting for the full response.
streaming_callback: contextvars.ContextVar = contextvars.ContextVar(
    "streaming_callback", default=None
)


class AgentState(TypedDict):
    """State that flows through the RAG pipeline nodes.

    Each node reads from and writes to this shared state dict.
    ``messages`` uses LangGraph's ``add_messages`` reducer so that
    new messages are appended rather than overwriting.
    """

    # Conversation
    messages: Annotated[list[BaseMessage], add_messages]
    question: str

    # Multi-tenant context
    workspace_id: str
    rules: list[dict]  # active rules from DB: [{"id": int, "rule_text": str}]

    # Output
    answer: str

    # Retrieval context
    context: list[str]
    sources_used: int

    # Flags
    is_safe: bool
    is_high_risk: bool
    is_prohibited: bool
    is_rule_matched: bool
