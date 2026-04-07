from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class VideoRecord:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    duration_seconds: int
    view_count: int
    like_count: int | None
    comment_count: int | None
    thumbnail_url: str | None
    url: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    seed_keyword: str | None = None
    source_query: str | None = None

    @property
    def age_days(self) -> int:
        published = parse_datetime(self.published_at)
        now = datetime.now(timezone.utc)
        return max((now - published).days, 1)

    @property
    def is_probable_short(self) -> bool:
        return self.duration_seconds <= 90


@dataclass(slots=True)
class ChannelRecord:
    channel_id: str
    title: str
    subscriber_count: int | None
    video_count: int | None
    view_count: int | None
    description: str
    uploads_playlist_id: str | None = None
    country: str | None = None
    custom_url: str | None = None


@dataclass(slots=True)
class VideoAnalysis:
    video_id: str
    opportunity_score: float
    views_per_subscriber: float | None
    velocity: float
    faceless_probability: float
    ai_suitability: str
    factual_risk: str
    evergreen_score: float
    repeatable_format_score: float
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NicheReport:
    name: str
    score: float
    seed_keywords: list[str]
    example_channels: list[str]
    example_videos: list[str]
    example_formats: list[str]
    repeat_search_terms: list[str]
    ai_suitability: str
    risk_level: str
    why_promising: list[str]
    starting_angles: list[str]
    estimated_series_size: int


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def dataclass_to_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: dataclass_to_dict(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, list):
        return [dataclass_to_dict(item) for item in value]
    return value

