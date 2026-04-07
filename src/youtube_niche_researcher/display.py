from __future__ import annotations


AI_LABELS = {
    "AI-only friendly": "Sadece yapay zeka ile yapılabilir",
    "AI-assisted only": "Yapay zeka destekli, insan kontrolü gerekli",
    "not suitable for AI-only": "Sadece yapay zeka için uygun değil",
}

RISK_LABELS = {
    "low": "düşük",
    "medium": "orta",
    "high": "yüksek",
}


def turkish_ai_label(value: str) -> str:
    return AI_LABELS.get(value, value)


def turkish_risk_label(value: str) -> str:
    return RISK_LABELS.get(value, value)

