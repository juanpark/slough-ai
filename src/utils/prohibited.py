"""Prohibited domain checker — refuses questions about topics the bot should not answer."""

# Keywords that indicate prohibited domains
# (legal, financial, HR decisions, interpersonal)
PROHIBITED_KEYWORDS = [
    # Legal
    "법률 자문", "법적 판단", "법적 책임", "소송 전략",
    # Contracts & termination
    "계약 해지", "해고 결정", "해고 통보", "징계 처분",
    # Financial decisions
    "투자 결정", "투자 승인", "자금 집행",
    # Compensation & resignation
    "연봉 결정", "연봉 협상", "퇴직금 결정", "퇴사 승인",
    # Interpersonal / non-business
    "개인적 조언", "사적인 문제",
]

# Broader domain markers (single words that in context signal prohibited areas)
PROHIBITED_DOMAINS = [
    "법률 판단",
    "최종 결정",
    "계약서 검토",
    "소송 대응",
]


def check_prohibited(text: str) -> dict:
    """Check if a question falls into a prohibited domain.

    Returns:
        {"is_prohibited": bool, "matched": list[str]}
    """
    matched = []
    for phrase in PROHIBITED_KEYWORDS + PROHIBITED_DOMAINS:
        if phrase in text:
            matched.append(phrase)
    return {"is_prohibited": len(matched) > 0, "matched": matched}
