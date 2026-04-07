from __future__ import annotations

import unicodedata


BLOCKED_SCRIPT_RANGES = [
    (0x0400, 0x052F, "Cyrillic"),
    (0x0590, 0x05FF, "Hebrew"),
    (0x0600, 0x06FF, "Arabic"),
    (0x0750, 0x077F, "Arabic Supplement"),
    (0x0900, 0x097F, "Devanagari"),
    (0x0980, 0x09FF, "Bengali"),
    (0x0A00, 0x0A7F, "Gurmukhi"),
    (0x0A80, 0x0AFF, "Gujarati"),
    (0x0B00, 0x0B7F, "Oriya"),
    (0x0B80, 0x0BFF, "Tamil"),
    (0x0C00, 0x0C7F, "Telugu"),
    (0x0C80, 0x0CFF, "Kannada"),
    (0x0D00, 0x0D7F, "Malayalam"),
    (0x0E00, 0x0E7F, "Thai"),
    (0x3040, 0x309F, "Hiragana"),
    (0x30A0, 0x30FF, "Katakana"),
    (0x3400, 0x4DBF, "CJK"),
    (0x4E00, 0x9FFF, "CJK"),
    (0xAC00, 0xD7AF, "Hangul"),
]

ROMANIZED_NON_ENGLISH_MARKERS = {
    " en español ",
    " español ",
    " portugues ",
    " português ",
    " hindi ",
    " urdu ",
    " ka sach ",
    " ki kahani ",
    " kya hai ",
    " kahani ",
}


def looks_like_english_title(value: str, *, min_latin_ratio: float = 0.8) -> bool:
    """Reject titles that are clearly not in a Latin/English-looking script."""
    text = f" {value.strip().lower()} "
    if not value.strip():
        return False
    if contains_blocked_script(value):
        return False
    if any(marker in text for marker in ROMANIZED_NON_ENGLISH_MARKERS):
        return False
    return latin_letter_ratio(value) >= min_latin_ratio


def contains_blocked_script(value: str) -> bool:
    for char in value:
        codepoint = ord(char)
        if any(start <= codepoint <= end for start, end, _name in BLOCKED_SCRIPT_RANGES):
            return True
    return False


def latin_letter_ratio(value: str) -> float:
    letters = [char for char in value if unicodedata.category(char).startswith("L")]
    if not letters:
        return 1.0
    latin_letters = [char for char in letters if "LATIN" in unicodedata.name(char, "")]
    return len(latin_letters) / len(letters)

