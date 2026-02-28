"""Persona prompt builder for the decision-maker AI."""


def build_system_prompt(
    rules: list[dict],
    context: list[str],
    persona: str = "",
) -> str:
    """Build a system prompt that reflects the decision-maker's persona.

    Args:
        rules: Active rules from DB — [{"id": int, "rule_text": str}].
        context: Retrieved conversation excerpts from pgvector.
        persona: Auto-extracted persona profile from Redis.

    Returns:
        A system prompt string for GPT-4o.
    """
    sections: list[str] = [
        "당신은 특정 회사 의사결정자의 AI 분신입니다.",
        "팀원의 질문에 의사결정자가 직접 답변하는 것처럼 자연스럽게 한국어로 답변하세요.",
    ]

    # Persona profile — extracted from decision-maker's actual messages
    if persona:
        sections.append(
            f"\n[대표 페르소나 — 실제 대화에서 자동 분석됨]\n{persona}"
        )
        sections.extend([
            "",
            "[행동 규칙]",
            "1. 위 페르소나의 말투와 어조를 일관되게 유지하세요.",
            "2. 아래 참고 문맥에 의사결정자가 실제로 한 말이 있으면, 그 표현과 논리를 우선 반영하세요.",
            "3. 문맥에 없는 내용은 페르소나에 기반한 추론으로 답변하되, 확실하지 않으면 '확인이 필요합니다'라고 하세요.",
            "4. 절대 페르소나를 벗어난 답변을 하지 마세요.",
        ])
    else:
        sections.extend([
            "아래의 규칙과 문맥을 참고하여 답변하되, 불확실하면 솔직히 모른다고 하세요.",
        ])

    # Conversation memory rules
    sections.extend([
        "",
        "[대화 기억 규칙]",
        "- 당신은 이 사용자와의 이전 대화를 기억하고 있습니다.",
        "- 대화 앞부분에 '[이전 대화 요약]'이 있으면, 그것은 이전 대화의 핵심 내용입니다. 이를 적극 활용하세요.",
        "- 사용자가 이전 질문, 대화 내용, 맥락을 물으면 기억하고 있는 내용을 바탕으로 답변하세요.",
        "- 절대로 '이전 대화를 저장하지 않습니다', '기억할 수 없습니다' 등의 답변을 하지 마세요.",
        "- 기억에 없는 내용이면 '해당 내용은 이전 대화에서 다루지 않았습니다'라고 답하세요.",
    ])

    # Rules take priority over learned patterns
    if rules:
        rule_lines = "\n".join(f"- {r['rule_text']}" for r in rules)
        sections.append(f"\n[필수 규칙 — 반드시 준수]\n{rule_lines}")

    # Retrieved context from vector search
    if context:
        context_text = "\n\n".join(context)
        sections.append(f"\n[학습된 대화 문맥 — 의사결정자의 과거 발언]\n{context_text}")
    else:
        sections.append("\n[학습된 대화 문맥]\n관련 문맥 없음")

    return "\n".join(sections)
