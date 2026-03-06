"""LangGraph node functions for the RAG pipeline.

Each node takes the current ``AgentState`` and returns a partial dict
that gets merged back into the state.
"""

import logging
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.services.ai.memory import trim_and_summarize
from src.services.ai.persona import build_system_prompt
from src.services.ai.state import AgentState, streaming_callback
from src.services.ai.vector_store import search_similar
from src.services.redis_client import get_persona_profile
from src.utils.keywords import detect_high_risk_keywords
from src.utils.prohibited import check_prohibited

logger = logging.getLogger(__name__)

# Lazy-loaded LLM singleton
_llm: Optional[ChatOpenAI] = None


def _get_decision_maker_name(workspace_id: str) -> str:
    """Look up the decision-maker's display name, cached in Redis.

    Falls back to empty string if anything fails.
    """
    from src.services.redis_client import RedisManager

    cache_key = f"dm_name:{workspace_id}"
    cache = RedisManager.get_cache()
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        import uuid as _uuid
        from src.services.db import get_db
        from src.services.db.models import Workspace
        from slack_sdk import WebClient

        with get_db() as db:
            ws = db.query(Workspace).filter(
                Workspace.id == _uuid.UUID(workspace_id)
            ).first()
            if not ws or not ws.decision_maker_id or not ws.bot_token:
                return ""

            client = WebClient(token=ws.bot_token)
            resp = client.users_info(user=ws.decision_maker_id)
            name = (
                resp["user"].get("real_name")
                or resp["user"].get("profile", {}).get("display_name")
                or resp["user"].get("name", "")
            )

        if name:
            cache.set(cache_key, name, ex=86400)  # cache 24h
        return name
    except Exception:
        logger.debug("Failed to look up decision-maker name for %s", workspace_id)
        return ""


def _get_llm() -> ChatOpenAI:
    """Return a singleton ChatOpenAI (GPT-4o) instance."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            api_key=settings.openai_api_key,
        )
    return _llm


def _to_openai_messages(msgs: list) -> list[dict]:
    """Convert LangChain BaseMessages to OpenAI-style dicts."""
    result = []
    for m in msgs:
        if isinstance(m, SystemMessage):
            result.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            result.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            result.append({"role": "assistant", "content": m.content})
    return result


# ── Node: check_rules ────────────────────────────────────────────────

def check_rules(state: AgentState) -> dict:
    """Match the question against active rules (keyword search).

    If a rule matches, the answer is set immediately and the pipeline
    can skip to END via the conditional edge.
    """
    question = state["question"]
    rules = state.get("rules", [])

    for rule in rules:
        rule_text = rule.get("rule_text", "")
        # Simple keyword containment — same logic as SloughAI
        if rule_text and rule_text.lower() in question.lower():
            return {
                "answer": f"📋 [규칙 적용]\n{rule_text}",
                "is_rule_matched": True,
            }

    return {"is_rule_matched": False}


# ── Node: check_safety ───────────────────────────────────────────────

def check_safety(state: AgentState) -> dict:
    """Run prohibited-domain and high-risk keyword checks."""
    question = state["question"]

    # Prohibited domain check
    prohibited = check_prohibited(question)
    if prohibited["is_prohibited"]:
        return {
            "is_safe": False,
            "is_prohibited": True,
            "is_high_risk": False,
        }

    # High-risk keyword check (answer anyway, but flag it)
    risk = detect_high_risk_keywords(question)
    return {
        "is_safe": True,
        "is_prohibited": False,
        "is_high_risk": risk["is_high_risk"],
    }


# ── Query rewriting helper ───────────────────────────────────────────

async def _rewrite_query(question: str) -> list[str]:
    """Generate 2-3 search-optimized query variants using GPT-4o-mini.

    Expands keywords, converts temporal expressions, and maintains
    the original meaning to improve retrieval recall.

    Returns the original query plus rewritten variants.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=200,
        api_key=settings.openai_api_key,
    )
    prompt = (
        "당신은 검색 쿼리 최적화 전문가입니다.\n"
        "아래 질문을 벡터 검색에 최적화된 2-3개의 검색 쿼리로 변환하세요.\n"
        "규칙:\n"
        "- 각 쿼리는 한 줄에 하나씩\n"
        "- 시간 표현('최근', '요즘')은 구체적 키워드로 변환\n"
        "- 동의어와 관련 키워드를 확장\n"
        "- 원래 의미를 유지\n"
        "- 쿼리만 출력 (번호, 설명 없이)\n\n"
        f"질문: {question}"
    )
    try:
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        variants = [
            line.strip()
            for line in response.content.strip().split("\n")
            if line.strip()
        ]
        # Always include original query first
        return [question] + variants[:2]
    except Exception:
        logger.warning("Query rewrite failed, using original query only")
        return [question]


# ── Node: retrieve ───────────────────────────────────────────────────

async def retrieve(state: AgentState) -> dict:
    """Retrieve similar documents from pgvector with query rewriting.

    1. Rewrite the question into 2-3 search variants (GPT-4o-mini)
    2. Run vector search for each variant
    3. Deduplicate by content, keep highest score per doc
    4. Annotate with relevance labels and dates
    """
    workspace_id = state.get("workspace_id", "")
    question = state["question"]

    try:
        queries = await _rewrite_query(question)
        logger.info("Query rewrite: %d variants for '%s'", len(queries), question[:50])

        # Collect results from all query variants
        seen: dict[str, tuple[float, str]] = {}  # content -> (best_score, date_str)
        for q in queries:
            results = search_similar(
                workspace_id=workspace_id,
                query=q,
                k=8,
                threshold=0.3,
            )
            for content, score, date_str in results:
                if content not in seen or score > seen[content][0]:
                    seen[content] = (score, date_str)

        # Sort by score descending, cap at k=8
        ranked = sorted(seen.items(), key=lambda x: x[1][0], reverse=True)[:8]

        # Annotate each doc with relevance level and date
        annotated = []
        for content, (score, date_str) in ranked:
            if score > 0.5:
                label = "[높은 관련성]"
            elif score >= 0.35:
                label = "[관련성 있음]"
            else:
                label = "[낮은 관련성]"
            annotated.append(f"{label} [{date_str}]\n{content}")

        return {
            "context": annotated,
            "sources_used": len(ranked),
        }
    except Exception:
        logger.exception("Vector search failed")
        return {
            "context": [],
            "sources_used": 0,
        }


# ── Node: generate ───────────────────────────────────────────────────

async def generate(state: AgentState) -> dict:
    """Generate an answer using GPT-4o with persona prompt + conversation memory.

    Memory management:
      1. ``trim_and_summarize`` compresses old messages into a summary
      2. Recent 2 Q&A pairs are kept verbatim
      3. Token cost is bounded at ~400-700 regardless of conversation length
    """
    # Skip if rule already matched
    if state.get("is_rule_matched"):
        return {}

    rules = state.get("rules", [])
    context = state.get("context", [])
    workspace_id = state.get("workspace_id", "")

    persona = get_persona_profile(workspace_id) if workspace_id else ""

    # Look up decision-maker name for self-identity in prompt
    dm_name = ""
    if workspace_id:
        dm_name = _get_decision_maker_name(workspace_id)

    system_prompt = build_system_prompt(
        rules, context, persona=persona, decision_maker_name=dm_name,
    )

    # Trim conversation history for token efficiency
    raw_messages = state.get("messages", [])
    trimmed = await trim_and_summarize(raw_messages, max_recent_pairs=2)

    # Build final message list: system prompt + trimmed memory + current question
    messages = [
        {"role": "system", "content": system_prompt},
        *_to_openai_messages(trimmed),
    ]

    llm = _get_llm()

    # Check for streaming callback
    on_chunk = streaming_callback.get(None)

    try:
        if on_chunk:
            # Streaming mode — send tokens progressively
            answer_chunks: list[str] = []
            async for chunk in llm.astream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    answer_chunks.append(chunk.content)
                    on_chunk("".join(answer_chunks))
            answer_text = "".join(answer_chunks)
        else:
            # Non-streaming mode (backward compatible)
            response = await llm.ainvoke(messages)
            answer_text = response.content
    except Exception:
        logger.exception("LLM generation failed")
        answer_text = "죄송합니다. 답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    return {
        "answer": answer_text,
        "messages": [AIMessage(content=answer_text)],
    }


# ── Node: refuse_answer ──────────────────────────────────────────────

def refuse_answer(state: AgentState) -> dict:
    """Refuse to answer prohibited-domain questions."""
    return {
        "answer": (
            "죄송합니다. 이 주제는 법적·재무적·운영상 판단이 필요한 영역으로, "
            "AI가 답변을 제공할 수 없습니다. 직접 의사결정자에게 문의해 주세요."
        ),
    }

