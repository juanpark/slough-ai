"""LangGraph StateGraph definition for the RAG pipeline.

Flow:
    check_rules ──┬── (rule matched) ──→ END
                  └── (no rule)     ──→ check_safety ──┬── (safe)       ──→ retrieve → generate → END
                                                       └── (prohibited) ──→ refuse   → END
"""

from langgraph.graph import END, StateGraph

from src.services.ai.nodes import (
    check_rules,
    check_safety,
    generate,
    refuse_answer,
    retrieve,
)
from src.services.ai.state import AgentState


def create_graph() -> StateGraph:
    """Build and return the (uncompiled) RAG workflow graph."""
    workflow = StateGraph(AgentState)

    # 1. Add nodes
    workflow.add_node("check_rules", check_rules)
    workflow.add_node("check_safety", check_safety)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("refuse", refuse_answer)

    # 2. Entry point
    workflow.set_entry_point("check_rules")

    # 3. Conditional edges
    def route_rule(state: AgentState) -> str:
        if state.get("is_rule_matched"):
            return "end"
        return "check_safety"

    workflow.add_conditional_edges(
        "check_rules",
        route_rule,
        {"end": END, "check_safety": "check_safety"},
    )

    def route_safety(state: AgentState) -> str:
        if state.get("is_safe"):
            return "retrieve"
        return "refuse"

    workflow.add_conditional_edges(
        "check_safety",
        route_safety,
        {"retrieve": "retrieve", "refuse": "refuse"},
    )

    # 4. Sequential edges
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    workflow.add_edge("refuse", END)

    return workflow


def get_compiled_graph(checkpointer=None):
    """Return a compiled, ready-to-invoke graph.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g. AsyncPostgresSaver)
                      for persisting conversation state across invocations.
    """
    return create_graph().compile(checkpointer=checkpointer)
