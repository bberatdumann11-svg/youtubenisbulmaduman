from __future__ import annotations

import re


_ISO_DURATION_RE = re.compile(
    r"^P"
    r"(?:(?P<days>\d+)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?"
    r")?$"
)


def parse_iso8601_duration(value: str) -> int:
    """Parse YouTube ISO-8601 durations such as PT12M34S into seconds."""
    match = _ISO_DURATION_RE.match(value or "")
    if not match:
        return 0
    parts = {key: int(val) if val else 0 for key, val in match.groupdict().items()}
    return (
        parts["days"] * 86400
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )


def format_duration(seconds: int) -> str:
    hours, rem = divmod(max(seconds, 0), 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

