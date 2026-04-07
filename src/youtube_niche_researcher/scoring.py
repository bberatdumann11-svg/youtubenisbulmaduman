from __future__ import annotations

import math
from collections import Counter

from .models import ChannelRecord, VideoAnalysis, VideoRecord
from .text_tools import extract_title_pattern, keyword_density


FACELESS_KEYWORDS = {
    "documentary",
    "explained",
    "story",
    "stories",
    "history",
    "mystery",
    "mythology",
    "legend",
    "facts",
    "case",
    "animated",
    "ai",
    "narrated",
    "voiceover",
    "top",
    "luxury",
    "business",
    "company",
}

FACE_SHOWING_KEYWORDS = {
    "podcast",
    "vlog",
    "interview",
    "reaction",
    "try on",
    "makeup",
    "fitness",
    "workout",
    "travel vlog",
}

HIGH_RISK_KEYWORDS = {
    "medical",
    "health",
    "disease",
    "treatment",
    "doctor",
    "crypto",
    "stock",
    "investment",
    "legal",
    "lawsuit",
    "crime",
    "murder",
    "war",
    "politics",
    "breaking",
    "news",
}

LOW_RISK_KEYWORDS = {
    "mythology",
    "legend",
    "luxury",
    "history",
    "ancient",
    "explained",
    "story",
    "mystery",
    "horror",
    "business",
    "technology",
}

AI_FRIENDLY_KEYWORDS = {
    "mythology",
    "legend",
    "history",
    "explained",
    "documentary",
    "story",
    "mystery",
    "horror",
    "luxury",
    "top",
    "facts",
    "animated",
    "business",
    "company",
    "technology",
}

AI_ASSISTED_KEYWORDS = {
    "news",
    "current",
    "breaking",
    "finance",
    "law",
    "science",
    "medical",
    "true crime",
    "investigation",
}


def analyze_video(
    video: VideoRecord,
    channel: ChannelRecord | None,
    *,
    channel_recent_videos: list[VideoRecord] | None = None,
) -> VideoAnalysis:
    text = f"{video.title} {video.description} {' '.join(video.tags)}".lower()
    subscriber_count = channel.subscriber_count if channel else None
    views_per_subscriber = None
    if subscriber_count and subscriber_count > 0:
        views_per_subscriber = video.view_count / subscriber_count

    demand_score = scale_log(video.view_count, low=10_000, high=1_500_000, max_score=20)
    underdog_score = ratio_score(views_per_subscriber)
    velocity = video.view_count / video.age_days
    velocity_score = scale_log(velocity, low=500, high=50_000, max_score=10)
    faceless_probability = estimate_faceless_probability(video, channel)
    faceless_score = faceless_probability * 10
    ai_suitability = classify_ai_suitability(video, channel)
    ai_score = {"AI-only friendly": 10, "AI-assisted only": 6, "not suitable for AI-only": 1}[ai_suitability]
    factual_risk = classify_factual_risk(video, channel)
    risk_penalty = {"low": 0, "medium": 6, "high": 16}[factual_risk]
    evergreen_score = estimate_evergreen_score(text) * 10
    repeatable_format_score = estimate_repeatable_format_score(video, channel_recent_videos or []) * 10
    shorts_penalty = 20 if video.is_probable_short else 0

    score = (
        demand_score
        + underdog_score
        + velocity_score
        + faceless_score
        + ai_score
        + evergreen_score
        + repeatable_format_score
        - risk_penalty
        - shorts_penalty
    )
    notes = []
    if views_per_subscriber and views_per_subscriber >= 10:
        notes.append(f"views/subscriber oranı güçlü: {views_per_subscriber:.1f}x")
    if repeatable_format_score >= 6:
        notes.append("kanalda tekrar eden başlık/format sinyali var")
    if faceless_probability >= 0.65:
        notes.append("faceless üretime benzer sinyaller yüksek")
    if factual_risk == "high":
        notes.append("yüksek doğruluk/uyumluluk riski")

    return VideoAnalysis(
        video_id=video.video_id,
        opportunity_score=round(clamp(score, 0, 100), 2),
        views_per_subscriber=round(views_per_subscriber, 2) if views_per_subscriber is not None else None,
        velocity=round(velocity, 2),
        faceless_probability=round(faceless_probability, 2),
        ai_suitability=ai_suitability,
        factual_risk=factual_risk,
        evergreen_score=round(evergreen_score, 2),
        repeatable_format_score=round(repeatable_format_score, 2),
        notes=notes,
    )


def scale_log(value: float, *, low: float, high: float, max_score: float) -> float:
    if value <= low:
        return 0
    if value >= high:
        return max_score
    low_log = math.log10(low)
    high_log = math.log10(high)
    value_log = math.log10(max(value, 1))
    return ((value_log - low_log) / (high_log - low_log)) * max_score


def ratio_score(views_per_subscriber: float | None) -> float:
    if views_per_subscriber is None:
        return 8
    if views_per_subscriber >= 50:
        return 25
    if views_per_subscriber >= 20:
        return 21
    if views_per_subscriber >= 10:
        return 17
    if views_per_subscriber >= 5:
        return 12
    if views_per_subscriber >= 1:
        return 6
    return 0


def estimate_faceless_probability(video: VideoRecord, channel: ChannelRecord | None) -> float:
    text = f"{video.title} {video.description} {' '.join(video.tags)}".lower()
    channel_text = f"{channel.title if channel else ''} {channel.description if channel else ''}".lower()
    score = 0.45
    score += keyword_density(text, FACELESS_KEYWORDS) * 2.2
    score += keyword_density(channel_text, FACELESS_KEYWORDS) * 1.8
    score -= keyword_density(text, FACE_SHOWING_KEYWORDS) * 2.5
    score -= keyword_density(channel_text, FACE_SHOWING_KEYWORDS) * 2.0
    if video.duration_seconds >= 480:
        score += 0.08
    if "official music" in text or "live performance" in text:
        score -= 0.35
    return clamp(score, 0, 1)


def classify_ai_suitability(video: VideoRecord, channel: ChannelRecord | None) -> str:
    text = f"{video.title} {video.description} {' '.join(video.tags)} {channel.description if channel else ''}".lower()
    friendly = keyword_density(text, AI_FRIENDLY_KEYWORDS)
    assisted = keyword_density(text, AI_ASSISTED_KEYWORDS)
    if any(phrase in text for phrase in ["reaction", "interview", "vlog", "prank", "makeup tutorial"]):
        return "not suitable for AI-only"
    if assisted >= 0.08 or any(phrase in text for phrase in ["true crime", "breaking news", "stock market"]):
        return "AI-assisted only"
    if friendly >= 0.06 or any(
        phrase in text
        for phrase in ["explained", "documentary", "mythology", "luxury", "history", "horror story"]
    ):
        return "AI-only friendly"
    return "AI-assisted only"


def classify_factual_risk(video: VideoRecord, channel: ChannelRecord | None) -> str:
    text = f"{video.title} {video.description} {' '.join(video.tags)} {channel.description if channel else ''}".lower()
    high = keyword_density(text, HIGH_RISK_KEYWORDS)
    low = keyword_density(text, LOW_RISK_KEYWORDS)
    if high >= 0.08 or any(phrase in text for phrase in ["breaking news", "medical advice", "investment advice"]):
        return "high"
    if high > 0.03 or "true crime" in text:
        return "medium"
    if low >= 0.04:
        return "low"
    return "medium"


def estimate_evergreen_score(text: str) -> float:
    score = 0.55
    evergreen_words = {"history", "ancient", "mythology", "legend", "explained", "story", "luxury", "mystery"}
    current_words = {"news", "today", "2025", "2026", "breaking", "latest", "update"}
    score += keyword_density(text, evergreen_words) * 2.0
    score -= keyword_density(text, current_words) * 2.2
    return clamp(score, 0, 1)


def estimate_repeatable_format_score(video: VideoRecord, recent_videos: list[VideoRecord]) -> float:
    if not recent_videos:
        return 0.35
    target_pattern = extract_title_pattern(video.title)
    patterns = Counter(extract_title_pattern(item.title) for item in recent_videos)
    if not patterns:
        return 0.35
    pattern_frequency = patterns[target_pattern] / max(len(recent_videos), 1)
    high_performers = sum(1 for item in recent_videos if item.view_count >= 50_000)
    performer_ratio = high_performers / max(len(recent_videos), 1)
    return clamp(0.25 + pattern_frequency * 1.2 + performer_ratio * 0.5, 0, 1)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

