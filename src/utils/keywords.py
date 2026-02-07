HIGH_RISK_KEYWORDS = ["계약", "해고", "투자", "법적", "소송", "퇴사", "연봉"]


def detect_high_risk_keywords(text: str) -> dict:
    """Check text for high-risk Korean keywords.

    Returns:
        {"is_high_risk": bool, "keywords": list[str]}
    """
    found = [kw for kw in HIGH_RISK_KEYWORDS if kw in text]
    return {"is_high_risk": len(found) > 0, "keywords": found}
