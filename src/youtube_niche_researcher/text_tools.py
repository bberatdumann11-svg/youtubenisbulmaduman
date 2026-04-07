from __future__ import annotations

import html
import re
from collections import Counter


STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "he",
    "her",
    "his",
    "how",
    "in",
    "inside",
    "is",
    "it",
    "its",
    "most",
    "new",
    "of",
    "on",
    "or",
    "our",
    "part",
    "that",
    "the",
    "their",
    "this",
    "to",
    "top",
    "truth",
    "was",
    "we",
    "what",
    "when",
    "where",
    "why",
    "with",
    "you",
    "your",
}


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("|", " ")
    return re.sub(r"\s+", " ", value).strip()


def tokenize(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9']+", clean_text(value).lower())
        if len(token) > 2 and token not in STOPWORDS
    ]


def top_terms(texts: list[str], *, limit: int = 8) -> list[str]:
    counts: Counter[str] = Counter()
    for text in texts:
        counts.update(tokenize(text))
    return [term for term, _count in counts.most_common(limit)]


def extract_title_pattern(title: str) -> str:
    title = clean_text(title)
    lower = title.lower()
    if "dark truth about" in lower:
        return "The Dark Truth About {topic}"
    if "truth about" in lower:
        return "The Truth About {topic}"
    if lower.startswith("why "):
        return "Why {topic}"
    if lower.startswith("how "):
        return "How {topic}"
    if lower.startswith("what "):
        return "What {topic}"
    if lower.startswith("inside "):
        return "Inside {topic}"
    if "history of" in lower:
        return "The History Of {topic}"
    if "rise and fall" in lower:
        return "The Rise And Fall Of {topic}"
    if lower.startswith("top ") or " most " in lower or lower.startswith("most "):
        return "Top / Most {topic}"
    if "explained" in lower:
        return "{topic} Explained"
    if "documentary" in lower:
        return "{topic} Documentary"
    terms = top_terms([title], limit=4)
    if terms:
        return f"{' '.join(term.title() for term in terms[:3])} {{topic}}"
    return "{topic} Story"


def keyword_density(text: str, keywords: set[str]) -> float:
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    hits = sum(1 for token in tokens if token in keywords)
    return hits / len(tokens)


def titlecase_phrase(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())

